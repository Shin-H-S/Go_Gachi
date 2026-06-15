"""생성 결과 AI 자동 채점.

runner.py가 만든 runs/<run_id>/results.json의 성공 레코드를 vision 모델에 보내
프롬프트 준수 여부를 1~5점으로 채점하고, 결과를 results.json에 다시 써넣는다.

채점 항목:
  - product_preserved: 원본 메뉴(형태·구성·양)가 보존됐는가
  - composition: 채널/디테일 레이아웃 규칙(여백, 점유율, 구도)을 지켰는가
  - copy_text_accuracy: 지정한 문구·가격·숫자가 정확히 렌더됐는가 (문구 케이스만)
  - no_unwanted_elements: 금지 요소(불필요 텍스트/워터마크/사람/추가 제품)가 없는가

사용:
  uv run python experiments/judge.py experiments/runs/<run_id>
  uv run python experiments/judge.py experiments/runs/<run_id> --model gpt-5-mini --force
"""

import argparse
import asyncio
import base64
import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import Settings, get_settings, load_env  # noqa: E402


def load_settings() -> Settings:
    """배치 채점은 DB가 필요 없으므로 DATABASE_URL 미설정이어도 동작하게 한다."""
    try:
        return get_settings()
    except RuntimeError:
        load_env()
        import os

        return Settings(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5"),
        )


JUDGE_SYSTEM = (
    "You are a strict QA reviewer for AI-generated food advertisement images. "
    "You receive the generation prompt, the original input photo, and the generated result. "
    "Score how well the result follows the prompt. Respond with JSON only, no markdown."
)

JUDGE_SCHEMA_HINT = """Respond with exactly this JSON shape:
{
  "product_preserved": 1-5,
  "composition": 1-5,
  "copy_text_accuracy": 1-5 or null (null when no ad copy was requested),
  "no_unwanted_elements": 1-5,
  "overall": 1-5,
  "verdict": "pass" | "warn" | "fail",
  "issues": ["short Korean description of each problem found"]
}
Scoring: 5 = perfect compliance, 3 = noticeable deviation, 1 = ignored the instruction.
verdict: pass = 상용 가능, warn = 수정 필요, fail = 프롬프트 미준수."""


def _data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _rubric(record: dict[str, Any]) -> str:
    """레코드 메타데이터로 채점 기준 텍스트를 만든다."""
    lines = [
        f"Case id: {record['case_id']} (kind: {record['kind']})",
        f"Preset/detail: {record['preset']}/{record['detail']}, target {record['target']}",
        "",
        "=== Full generation prompt ===",
        record["prompt"],
        "",
        "=== Specific expectations ===",
    ]
    copy_def = record.get("copy")
    if copy_def:
        lines.append(
            "Ad copy must be rendered EXACTLY (Korean text, prices, numbers): "
            + json.dumps(copy_def, ensure_ascii=False)
        )
    else:
        lines.append("No ad copy was requested: any rendered text/typography is a violation.")
    lines.append("No logo was provided: any logo or brand mark is a violation.")
    if record.get("user_prompt"):
        lines.append(f"User request to honor: {record['user_prompt']}")
    lines += [
        "",
        "First image = original input photo. Second image = generated result.",
        "",
        JUDGE_SCHEMA_HINT,
    ]
    return "\n".join(lines)


def _extract_output_text(payload: dict[str, Any]) -> str:
    """Responses API 응답에서 output_text를 관대하게 추출한다."""
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    chunks: list[str] = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if not chunks:
        raise RuntimeError("채점 모델 응답에서 텍스트를 찾지 못했습니다.")
    return "\n".join(chunks)


def _parse_judge_json(text: str) -> dict[str, Any]:
    """모델이 코드펜스를 둘러도 JSON 본문만 꺼내 파싱한다."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise RuntimeError(f"채점 JSON 파싱 실패: {text[:200]}")
    return json.loads(match.group(0))


async def judge_one(
    record: dict[str, Any],
    *,
    run_dir: Path,
    model: str,
    api_key: str,
    semaphore: asyncio.Semaphore,
    progress: dict[str, int],
) -> None:
    """결과 이미지 1장을 채점해 record['judge']에 저장한다."""
    async with semaphore:
        try:
            input_image = run_dir / "inputs" / record["image"]
            output_image = run_dir / record["output"]
            content: list[dict[str, Any]] = [
                {"type": "input_text", "text": _rubric(record)},
                {"type": "input_image", "image_url": _data_url(input_image)},
                {"type": "input_image", "image_url": _data_url(output_image)},
            ]
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "instructions": JUDGE_SYSTEM,
                        "input": [{"role": "user", "content": content}],
                    },
                )
            payload = response.json()
            if response.status_code >= 400:
                error = payload.get("error") or {}
                raise RuntimeError(error.get("message") or f"HTTP {response.status_code}")
            record["judge"] = _parse_judge_json(_extract_output_text(payload))
        except Exception as exc:
            record["judge"] = {"error": f"{type(exc).__name__}: {exc}"}

    progress["done"] += 1
    judge = record["judge"]
    label = (
        f"overall {judge.get('overall')} ({judge.get('verdict')})"
        if "error" not in judge
        else f"채점 실패: {judge['error'][:80]}"
    )
    print(
        f"[{progress['done']}/{progress['total']}] "
        f"{record['case_id']} × {record['image']} → {label}"
    )


def print_summary(records: list[dict[str, Any]]) -> None:
    """케이스별 평균 점수를 표로 출력한다(편차 확인용 min~max 포함)."""
    by_case: dict[str, list[int]] = {}
    for record in records:
        judge = record.get("judge") or {}
        if isinstance(judge.get("overall"), int | float):
            by_case.setdefault(record["case_id"], []).append(judge["overall"])
    if not by_case:
        return
    print("\n케이스별 overall 평균 (min~max):")
    for case_id, scores in sorted(by_case.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        avg = sum(scores) / len(scores)
        print(f"  {avg:.1f}  ({min(scores)}~{max(scores)}, n={len(scores)})  {case_id}")


async def main_async(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = ROOT_DIR / run_dir
    results_path = run_dir / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))

    settings = load_settings()
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY가 없습니다.")
    model = args.model or settings.openai_text_model

    targets = [
        r
        for r in payload["records"]
        if r["status"] == "ok" and (args.force or "judge" not in r)
    ]
    if not targets:
        raise SystemExit("채점할 레코드가 없습니다 (이미 채점됐으면 --force).")
    print(f"채점 대상 {len(targets)}건 | model: {model}")

    semaphore = asyncio.Semaphore(args.concurrency)
    progress = {"done": 0, "total": len(targets)}
    await asyncio.gather(
        *(
            judge_one(
                record,
                run_dir=run_dir,
                model=model,
                api_key=settings.openai_api_key,
                semaphore=semaphore,
                progress=progress,
            )
            for record in targets
        )
    )

    results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print_summary(payload["records"])
    print(f"\n저장: {results_path}")
    print(f"다음: uv run python experiments/report.py {args.run_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="배치 결과 AI 자동 채점")
    parser.add_argument("run_dir", help="experiments/runs/<run_id> 경로")
    parser.add_argument(
        "--model",
        default=None,
        help="채점용 vision 모델 (기본: OPENAI_TEXT_MODEL)",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--force", action="store_true", help="이미 채점된 레코드도 다시 채점")
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
