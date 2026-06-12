"""프롬프트 배치 테스트 러너.

matrix.yaml(또는 .json)에 정의한 [케이스 × 이미지 × 반복] 조합을 전개해
OpenAI Images Edit API를 병렬 호출하고, 결과를 runs/<run_id>/ 아래에 저장한다.

실제 서비스의 프롬프트 조립 흐름(build_system_prompt → user_prompt_with_context →
merge_image_prompt)을 그대로 재사용하므로, 여기서 통과한 프롬프트는 서비스에서도
동일하게 동작한다. 캐시/DB를 거치지 않고 call_openai_edit를 직접 호출하기 때문에
같은 조합을 반복 실행해도 매번 새로 생성된다(편차 테스트 가능).

사용:
  uv run python experiments/runner.py experiments/matrix.example.yaml --dry-run
  uv run python experiments/runner.py experiments/matrix.example.yaml --yes
"""

import argparse
import asyncio
import base64
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import Settings, get_settings, load_env  # noqa: E402
from backend.app.core.presets import Preset, PresetDetail, get_presets  # noqa: E402
from backend.app.core.prompts import (  # noqa: E402
    build_system_prompt,
    build_user_prompt,
    merge_image_prompt,
)
from backend.app.services import openai_images  # noqa: E402
from backend.app.services.copywriting import AdCopy  # noqa: E402
from backend.app.services.costs import calculate_image_cost  # noqa: E402
from backend.app.services.generation_inputs import (  # noqa: E402
    target_size_or_detail,
    user_prompt_with_context,
)
from backend.app.services.image_processing import normalize_for_openai  # noqa: E402
from backend.app.services.image_validation import parse_image  # noqa: E402
from backend.app.services.openai_images import call_openai_edit  # noqa: E402

# 실험 도구 전용: 서비스 코드는 그대로 두고, 이미지 API 타임아웃만 연장한다.
# (openai_images.py는 120초 고정 — 고품질/세로형 생성이 가끔 이를 넘겨 실패할 수 있음)
IMAGE_API_TIMEOUT_S = float(os.getenv("IMAGE_API_TIMEOUT_S", "300"))


class _PatchedAsyncClient(httpx.AsyncClient):
    """timeout 인자를 무시하고 실험용 타임아웃을 강제한다."""

    def __init__(self, *args, timeout=None, **kwargs):  # noqa: ARG002
        super().__init__(*args, timeout=IMAGE_API_TIMEOUT_S, **kwargs)


class _HttpxShim:
    AsyncClient = _PatchedAsyncClient
    HTTPError = httpx.HTTPError

    def __getattr__(self, name):
        # TimeoutException 등 나머지 httpx 속성은 실제 모듈로 위임한다.
        return getattr(httpx, name)


def b64_from_edit_result(result: object) -> str:
    """call_openai_edit 반환 형식이 b64 문자열이든 (b64, usage) 튜플이든 b64만 꺼낸다.

    백엔드가 usage 반환을 추가/제거해도 테스트 도구가 깨지지 않게 하는 호환 계층.
    """
    if isinstance(result, tuple):
        return result[0]
    return str(result)


def usage_from_edit_result(result: object) -> dict:
    """call_openai_edit 반환에서 usage(토큰 수) dict를 꺼낸다. 없으면 빈 dict."""
    if isinstance(result, tuple) and len(result) > 1 and isinstance(result[1], dict):
        return result[1]
    return {}


# openai_images 모듈 안에서 참조하는 httpx만 바꿔치기 → 서비스 런타임에는 영향 없음.
openai_images.httpx = _HttpxShim()

MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

KNOWN_KINDS = {"system", "logo", "copy", "user", "mixed"}


def load_settings() -> Settings:
    """배치 테스트는 DB가 필요 없으므로 DATABASE_URL 미설정이어도 동작하게 한다."""
    try:
        return get_settings()
    except RuntimeError:
        load_env()
        import os

        api_key = os.getenv("OPENAI_API_KEY", "")
        return Settings(
            image_provider="openai" if api_key else "mock",
            openai_api_key=api_key,
            openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5"),
            openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
            openai_image_quality=os.getenv("OPENAI_IMAGE_QUALITY", "medium"),
            openai_image_edit_estimated_cost_usd=float(
                os.getenv("OPENAI_IMAGE_EDIT_ESTIMATED_COST_USD", "0.01")
            ),
        )


def load_matrix(path: Path) -> dict[str, Any]:
    """matrix 파일을 읽는다. .yaml은 PyYAML이 있을 때만, .json은 항상 지원."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError:
            raise SystemExit(
                "PyYAML이 없습니다. `uv add --dev pyyaml` 후 다시 실행하거나 "
                ".json 매트릭스를 사용하세요."
            ) from None
        return yaml.safe_load(text)
    return json.loads(text)


def file_to_data_url(path: Path) -> str:
    """이미지 파일을 서비스 입력과 동일한 data URL로 변환한다."""
    mime = MIME_BY_SUFFIX.get(path.suffix.lower())
    if mime is None:
        raise SystemExit(f"지원하지 않는 이미지 확장자: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def resolve_path(raw: str) -> Path:
    """매트릭스 안의 경로를 레포 루트 기준으로 해석한다."""
    path = Path(raw)
    return path if path.is_absolute() else ROOT_DIR / path


def build_case_prompt(
    case: dict[str, Any],
    preset: Preset,
    detail: PresetDetail,
) -> tuple[str, dict[str, Any]]:
    """케이스 정의로 실제 서비스와 동일한 최종 프롬프트를 만든다."""
    copy_def = case.get("copy") or None
    ad_copy = (
        AdCopy(
            headline=copy_def.get("headline"),
            subcopy=copy_def.get("subcopy"),
            cta=copy_def.get("cta"),
            mode="preserve",
        )
        if copy_def
        else None
    )
    has_logo = bool(case.get("logo"))
    logo_position = case.get("logo_position") if has_logo else None
    resize_mode = case.get("resize_mode", "cover")

    target_size = target_size_or_detail(detail=detail, target_width=None, target_height=None)
    ctx_user_prompt = user_prompt_with_context(
        case.get("user_prompt", ""), target_size, detail, resize_mode
    )

    # 시스템 프롬프트: 전체 교체(system_override) > 서비스 조립 + 추가(system_append)
    system_text = case.get("system_override") or build_system_prompt(
        preset, detail, image_copy=ad_copy, logo_position=logo_position
    )
    if case.get("system_append"):
        system_text = f"{system_text}\n{case['system_append']}"

    prompt = merge_image_prompt(system_text, build_user_prompt(ctx_user_prompt))
    meta = {
        "copy": copy_def,
        "has_logo": has_logo,
        "logo_position": logo_position,
        "user_prompt": case.get("user_prompt", ""),
        "system_override": bool(case.get("system_override")),
        "system_append": case.get("system_append") or None,
        "target": f"{target_size.width}x{target_size.height}",
        "api_size": detail.api_size,
        "resize_mode": resize_mode,
    }
    return prompt, meta


def expand_jobs(
    matrix: dict[str, Any],
    presets: dict[str, Preset],
    repeat: int,
) -> list[dict[str, Any]]:
    """케이스 × 이미지 × 반복 조합을 실행 단위(job) 목록으로 전개한다."""
    jobs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for case in matrix["cases"]:
        case_id = case["id"]
        if case_id in seen_ids:
            raise SystemExit(f"케이스 id 중복: {case_id}")
        seen_ids.add(case_id)
        kind = case.get("kind", "mixed")
        if kind not in KNOWN_KINDS:
            raise SystemExit(f"알 수 없는 kind '{kind}' (케이스 {case_id})")

        preset = presets.get(case.get("preset", ""))
        if preset is None:
            raise SystemExit(f"존재하지 않는 preset '{case.get('preset')}' (케이스 {case_id})")
        detail = preset.find_detail(case.get("detail")) or preset.default_detail()

        prompt, meta = build_case_prompt(case, preset, detail)

        # 로고: 케이스 값(경로 또는 true) > 전역 logo
        logo_raw = case.get("logo")
        if logo_raw is True:
            logo_raw = matrix.get("logo")
            if not logo_raw:
                raise SystemExit(f"케이스 {case_id}: logo=true인데 전역 logo가 없습니다.")

        for image_def in matrix["images"]:
            image_path = resolve_path(
                image_def["path"] if isinstance(image_def, dict) else image_def
            )
            if not image_path.exists():
                raise SystemExit(f"입력 이미지가 없습니다: {image_path}")
            for rep in range(1, repeat + 1):
                jobs.append(
                    {
                        "case_id": case_id,
                        "kind": kind,
                        "preset": preset.id,
                        "detail": detail.id,
                        "image_path": image_path,
                        "logo_path": resolve_path(logo_raw) if logo_raw else None,
                        "rep": rep,
                        "prompt": prompt,
                        **meta,
                    }
                )
    return jobs


async def run_one(
    job: dict[str, Any],
    *,
    settings: Settings,
    run_dir: Path,
    semaphore: asyncio.Semaphore,
    dry_run: bool,
    progress: dict[str, int],
) -> dict[str, Any]:
    """job 하나를 실행하고 결과 레코드를 돌려준다. 실패해도 예외를 올리지 않는다."""
    image_path: Path = job["image_path"]
    logo_path: Path | None = job["logo_path"]
    out_name = f"{job['case_id']}__{image_path.stem}__r{job['rep']}.png"
    record: dict[str, Any] = {
        **{k: v for k, v in job.items() if k not in {"image_path", "logo_path"}},
        "image": image_path.name,
        "logo": logo_path.name if logo_path else None,
        "output": None,
        "status": "dry_run" if dry_run else "pending",
        "error": None,
        "elapsed_s": None,
    }
    if dry_run:
        return record

    async with semaphore:
        start = time.perf_counter()
        try:
            uploaded = parse_image(file_to_data_url(image_path), settings.max_upload_bytes)
            logo_uploaded = (
                parse_image(file_to_data_url(logo_path), settings.max_upload_bytes)
                if logo_path
                else None
            )
            openai_uploaded = await asyncio.to_thread(normalize_for_openai, uploaded)
            openai_logo = (
                await asyncio.to_thread(normalize_for_openai, logo_uploaded)
                if logo_uploaded
                else None
            )
            edit_result = await call_openai_edit(
                uploaded=openai_uploaded,
                reference_images=[openai_logo] if openai_logo else None,
                api_size=job["api_size"],
                prompt=job["prompt"],
                settings=settings,
            )
            (run_dir / "images" / out_name).write_bytes(
                base64.b64decode(b64_from_edit_result(edit_result))
            )
            usage = usage_from_edit_result(edit_result)
            record["usage"] = usage or None
            record["cost_usd"] = calculate_image_cost(
                usage, quality=settings.openai_image_quality
            )
            record["output"] = f"images/{out_name}"
            record["status"] = "ok"
        except Exception as exc:  # 한 건 실패가 배치 전체를 멈추지 않게 한다.
            record["status"] = "error"
            record["error"] = f"{type(exc).__name__}: {exc}"
        record["elapsed_s"] = round(time.perf_counter() - start, 1)

    progress["done"] += 1
    mark = "OK " if record["status"] == "ok" else "ERR"
    print(f"[{progress['done']}/{progress['total']}] {mark} {out_name} ({record['elapsed_s']}s)")
    return record


def copy_inputs(jobs: list[dict[str, Any]], run_dir: Path) -> None:
    """리포트가 입력 원본을 보여줄 수 있게 입력/로고 이미지를 런 폴더로 복사한다."""
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        for key in ("image_path", "logo_path"):
            path = job.get(key)
            if path and not (inputs_dir / path.name).exists():
                shutil.copy2(path, inputs_dir / path.name)


async def main_async(args: argparse.Namespace) -> None:
    matrix_path = resolve_path(args.matrix)
    matrix = load_matrix(matrix_path)
    settings = load_settings()
    overrides: dict[str, Any] = {}
    quality = args.quality or matrix.get("quality")
    if quality:
        overrides["openai_image_quality"] = quality
    model = args.model or matrix.get("model")
    if model:
        overrides["openai_image_model"] = model
    if overrides:
        settings = settings.model_copy(update=overrides)

    repeat = args.repeat or int(matrix.get("repeat", 1))
    concurrency = args.concurrency or int(matrix.get("concurrency", 4))
    jobs = expand_jobs(matrix, get_presets(), repeat)
    if args.limit:
        jobs = jobs[: args.limit]

    estimated = len(jobs) * settings.openai_image_edit_estimated_cost_usd
    print(
        f"run: {matrix.get('run_name', matrix_path.stem)} | jobs: {len(jobs)} "
        f"(케이스 {len(matrix['cases'])} × 이미지 {len(matrix['images'])} × 반복 {repeat})"
    )
    print(
        f"model: {settings.openai_image_model} | quality: {settings.openai_image_quality} "
        f"| 동시 {concurrency} | 예상 비용 ≈ ${estimated:.2f}"
    )
    if not args.dry_run:
        if not settings.openai_api_key:
            raise SystemExit(
                "OPENAI_API_KEY가 없습니다. --dry-run으로 프롬프트만 확인할 수 있습니다."
            )
        if not args.yes and input("진행할까요? [y/N] ").strip().lower() != "y":
            raise SystemExit("중단했습니다.")

    run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{matrix.get('run_name', matrix_path.stem)}"
    run_dir = ROOT_DIR / "experiments" / "runs" / run_id
    (run_dir / "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(matrix_path, run_dir / f"matrix{matrix_path.suffix}")
    copy_inputs(jobs, run_dir)

    semaphore = asyncio.Semaphore(concurrency)
    progress = {"done": 0, "total": len(jobs)}
    records = await asyncio.gather(
        *(
            run_one(
                job,
                settings=settings,
                run_dir=run_dir,
                semaphore=semaphore,
                dry_run=args.dry_run,
                progress=progress,
            )
            for job in jobs
        )
    )

    ok = sum(1 for r in records if r["status"] == "ok")
    payload = {
        "run_id": run_id,
        "run_name": matrix.get("run_name", matrix_path.stem),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": settings.openai_image_model,
        "quality": settings.openai_image_quality,
        "repeat": repeat,
        "dry_run": args.dry_run,
        "records": list(records),
    }
    (run_dir / "results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n완료: ok {ok} / error {sum(1 for r in records if r['status'] == 'error')}")
    print(f"결과: {run_dir / 'results.json'}")
    print(f"다음: uv run python experiments/report.py experiments/runs/{run_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="프롬프트 배치 테스트 러너")
    parser.add_argument("matrix", help="matrix .yaml/.json 경로")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 프롬프트만 생성")
    parser.add_argument("--yes", action="store_true", help="비용 확인 질문 생략")
    parser.add_argument("--repeat", type=int, default=None, help="반복 횟수 덮어쓰기")
    parser.add_argument("--concurrency", type=int, default=None, help="동시 호출 수")
    parser.add_argument("--quality", default=None, help="low|medium|high")
    parser.add_argument("--model", default=None, help="이미지 모델 덮어쓰기")
    parser.add_argument("--limit", type=int, default=None, help="앞에서 N개 조합만 실행")
    asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    main()
