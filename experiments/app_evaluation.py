"""Evaluation and prompt-comparison helpers for the experiments Streamlit console."""

import asyncio
import base64
import json
import os
from datetime import datetime
from pathlib import Path

import httpx
from judge import _extract_output_text, _parse_judge_json

from backend.app.services.costs import calculate_text_cost

EVAL_COST_PER_CALL_USD = float(os.getenv("EVAL_ESTIMATED_COST_USD", "0.005"))
COMPARE_MODEL = os.getenv("COMPARE_MODEL", "gpt-5.4-mini")

EVAL_SYSTEM = (
    "You are a strict QA reviewer for AI-generated food advertisement images. "
    "Score objectively. Respond with JSON only, no markdown."
)

DEFAULT_ITEM_COUNT = 6


def default_eval_items() -> list[dict]:
    return [{"evaluator": "사람", "criterion": "", "scores": {}} for _ in range(DEFAULT_ITEM_COUNT)]


def load_evaluation(run_dir: Path) -> dict:
    path = run_dir / "evaluation.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {
        "items": default_eval_items(),
        "memo": "",
        "costs": {"eval_usd": 0.0, "eval_calls": 0},
    }


def save_evaluation(
    run_dir: Path,
    test_name: str,
    items: list[dict],
    memo: str,
    costs: dict,
) -> None:
    payload = {
        "test_name": test_name,
        "items": items,
        "memo": memo,
        "costs": costs,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (run_dir / "evaluation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── AI 평가 (Responses API) ────────────────────────────────────────────────


def _image_to_data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_eval_rubric(criteria: dict[str, str], prompt_text: str) -> str:
    lines = [
        "First image: the original input photo. Second image: the generated advertisement.",
        "The generation prompt was:",
        "--- prompt start ---",
        prompt_text,
        "--- prompt end ---",
        "",
        "Score the generated image against each numbered criterion below.",
        "10 = the criterion is fully satisfied. 0 = not satisfied at all.",
        "Use an intermediate integer when partially satisfied.",
        "Criteria (written in Korean):",
    ]
    for key, text in criteria.items():
        lines.append(f"{key}. {text}")
    keys = ", ".join(f'"{k}": <0-10 integer>' for k in criteria)
    lines += ["", "Respond with JSON only, exactly: {" + keys + "}"]
    return "\n".join(lines)


async def _eval_one_image(
    *,
    client: httpx.AsyncClient,
    api_key: str,
    model: str,
    rubric: str,
    input_image: Path,
    output_image: Path,
    semaphore: asyncio.Semaphore,
) -> tuple[dict[str, int], dict]:
    async with semaphore:
        content = [
            {"type": "input_text", "text": rubric},
            {"type": "input_image", "image_url": _image_to_data_url(input_image)},
            {"type": "input_image", "image_url": _image_to_data_url(output_image)},
        ]
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "instructions": EVAL_SYSTEM,
                "input": [{"role": "user", "content": content}],
            },
        )
        payload = response.json()
        if response.status_code >= 400:
            error = payload.get("error") or {}
            raise RuntimeError(error.get("message") or f"HTTP {response.status_code}")
        parsed = _parse_judge_json(_extract_output_text(payload))
        scores: dict[str, int] = {}
        for key, value in parsed.items():
            try:
                scores[str(key)] = max(0, min(10, int(value)))
            except (TypeError, ValueError):
                continue
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        return scores, usage


async def run_ai_eval(
    run_dir: Path,
    ok_records: list[dict],
    criteria: dict[str, str],
    prompt_text: str,
    settings,
) -> tuple[dict[str, dict[str, int]], int, list[str]]:
    """이미지 1장당 Responses API 1회로 모든 AI 항목을 채점한다.

    반환: ({이미지번호: {항목키: 점수}}, 호출 수, 오류 메시지들)
    """
    rubric = build_eval_rubric(criteria, prompt_text)
    semaphore = asyncio.Semaphore(3)
    errors: list[str] = []
    results: dict[str, dict[str, int]] = {}
    cost_state = {"usd": 0.0}

    async with httpx.AsyncClient(timeout=120) as client:
        async def one(number: str, record: dict) -> None:
            try:
                scores, usage = await _eval_one_image(
                    client=client,
                    api_key=settings.openai_api_key,
                    model=settings.openai_text_model,
                    rubric=rubric,
                    input_image=run_dir / "inputs" / record["image"],
                    output_image=run_dir / record["output"],
                    semaphore=semaphore,
                )
                results[number] = scores
                missing = [str(int(k) + 1) for k in criteria if k not in scores]
                if missing:
                    errors.append(
                        f"이미지 {number}: {', '.join(missing)}번째 항목 점수가 응답에 없어 "
                        "빈칸으로 둡니다."
                    )
                call_cost = calculate_text_cost(usage, model=settings.openai_text_model)
                cost_state["usd"] += call_cost if call_cost > 0 else EVAL_COST_PER_CALL_USD
            except Exception as exc:
                errors.append(f"이미지 {number}: {type(exc).__name__}: {exc}")

        await asyncio.gather(
            *(one(str(i + 1), rec) for i, rec in enumerate(ok_records))
        )
    return results, len(ok_records), errors, round(cost_state["usd"], 6)


# ── 프롬프트 비교 (탭3) ────────────────────────────────────────────────────

COMPARE_SYSTEM = (
    "You are a prompt engineer reviewing two image-generation prompts for a cafe "
    "ad service. Explain the differences in Korean for a non-expert teammate."
)


def compare_cost_estimate(prompt_a: str, prompt_b: str, model: str) -> float:
    """비교 1회의 대략적 비용. 입력은 글자수/4 토큰으로 근사, 출력은 700토큰 가정."""
    input_tokens = (len(prompt_a) + len(prompt_b)) // 4 + 200
    return calculate_text_cost(
        {"input_tokens": input_tokens, "output_tokens": 700}, model=model
    )


async def compare_prompts(
    name_a: str, prompt_a: str, name_b: str, prompt_b: str, settings, model: str
) -> tuple[str, dict]:
    """두 프롬프트의 차이를 한국어로 설명받는다. (설명, usage) 반환."""
    user_text = (
        f"[테스트 A: {name_a}]\n{prompt_a}\n\n[테스트 B: {name_b}]\n{prompt_b}\n\n"
        "두 프롬프트를 비교해 한국어로 설명해줘. 형식: 1) 공통 구조 한 줄, "
        "2) 차이점을 영역별로(채널/광고 유형/문구/로고/유저 요청/출력 규격/기타) 나눠 "
        "어떤 문장이 어떻게 다른지 짧게 인용하며 설명, 3) 각 차이가 생성 이미지에 "
        "미칠 영향 한 줄씩. 차이가 없는 영역은 '동일'이라고만 표시."
    )
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": model,
                "instructions": COMPARE_SYSTEM,
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_text}],
                    }
                ],
            },
        )
    payload = response.json()
    if response.status_code >= 400:
        error = payload.get("error") or {}
        raise RuntimeError(error.get("message") or f"HTTP {response.status_code}")
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return _extract_output_text(payload), usage


# ── UI ─────────────────────────────────────────────────────────────────────
