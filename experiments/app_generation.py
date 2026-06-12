"""Background generation workflow for the experiments Streamlit console."""

import asyncio
import base64
import json
import threading
import time
from datetime import datetime
from pathlib import Path

from app_common import RUNS_DIR
from app_prompting import assemble_full_prompt, resolve_ad_copy
from runner import b64_from_edit_result, load_settings, usage_from_edit_result

from backend.app.services.costs import calculate_image_cost
from backend.app.services.image_processing import normalize_for_openai
from backend.app.services.image_validation import parse_image
from backend.app.services.openai_images import call_openai_edit


def _write_progress(run_dir: Path, **updates) -> None:
    path = run_dir / "progress.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data.update(updates)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_results(run_dir: Path, payload: dict) -> None:
    (run_dir / "results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def _batch(cfg: dict, run_dir: Path) -> None:
    settings = load_settings()
    if cfg["quality"]:
        settings = settings.model_copy(update={"openai_image_quality": cfg["quality"]})
    ad_copy = await resolve_ad_copy(cfg, settings)
    prompt = assemble_full_prompt(cfg, ad_copy)

    uploaded = parse_image(cfg["image_data_url"], settings.max_upload_bytes)
    logo_uploaded = (
        parse_image(cfg["logo_data_url"], settings.max_upload_bytes) if cfg["has_logo"] else None
    )
    openai_uploaded = await asyncio.to_thread(normalize_for_openai, uploaded)
    openai_logo = (
        await asyncio.to_thread(normalize_for_openai, logo_uploaded) if logo_uploaded else None
    )

    copy_dict = (
        {"headline": ad_copy.headline, "subcopy": ad_copy.subcopy, "cta": ad_copy.cta}
        if ad_copy
        else None
    )
    kind = "copy" if ad_copy else ("logo" if cfg["has_logo"] else "system")
    base_record = {
        "case_id": cfg["name"],
        "kind": kind,
        "preset": cfg["channel_id"],
        "detail": cfg["detail_id"],
        "image": cfg["image_name"],
        "logo": cfg["logo_name"],
        "prompt": prompt,
        "copy": copy_dict,
        "has_logo": cfg["has_logo"],
        "logo_position": cfg["logo_position"] if cfg["has_logo"] else None,
        "user_prompt": cfg.get("user_prompt", ""),
        "system_override": False,
        "system_append": None,
        "target": f"{cfg['target_w']}x{cfg['target_h']}",
        "api_size": cfg["api_size"],
        "resize_mode": "cover",
    }
    payload = {
        "run_id": run_dir.name,
        "run_name": cfg["name"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": settings.openai_image_model,
        "quality": settings.openai_image_quality,
        "repeat": cfg["count"],
        "dry_run": False,
        "records": [],
    }
    state = {"done": 0, "ok": 0, "error": 0}
    lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(min(4, cfg["count"]))

    async def one(rep: int) -> None:
        record = {
            **base_record,
            "rep": rep,
            "output": None,
            "status": "pending",
            "error": None,
            "elapsed_s": None,
        }
        async with semaphore:
            start = time.perf_counter()
            try:
                edit_result = await call_openai_edit(
                    uploaded=openai_uploaded,
                    reference_images=[openai_logo] if openai_logo else None,
                    api_size=cfg["api_size"],
                    prompt=prompt,
                    settings=settings,
                )
                out_name = f"{cfg['name']}__r{rep}.png"
                (run_dir / "images" / out_name).write_bytes(
                    base64.b64decode(b64_from_edit_result(edit_result))
                )
                usage = usage_from_edit_result(edit_result)
                record.update(
                    output=f"images/{out_name}",
                    status="ok",
                    usage=usage or None,
                    cost_usd=calculate_image_cost(
                        usage, quality=settings.openai_image_quality
                    ),
                )
            except Exception as exc:
                record.update(status="error", error=f"{type(exc).__name__}: {exc}")
            record["elapsed_s"] = round(time.perf_counter() - start, 1)
        async with lock:
            state["done"] += 1
            state["ok" if record["status"] == "ok" else "error"] += 1
            payload["records"].append(record)
            payload["records"].sort(key=lambda r: r["rep"])
            _write_results(run_dir, payload)
            progress_update = {"done": state["done"], "ok": state["ok"], "error": state["error"]}
            if record["status"] == "error" and record["error"]:
                progress_update["last_error"] = record["error"][:300]
            _write_progress(run_dir, **progress_update)

    await asyncio.gather(*(one(rep) for rep in range(1, cfg["count"] + 1)))
    _write_progress(run_dir, status="done", ended=datetime.now().isoformat(timespec="seconds"))


def _worker(cfg: dict, run_dir: Path) -> None:
    try:
        asyncio.run(_batch(cfg, run_dir))
    except Exception as exc:
        _write_progress(run_dir, status="failed", message=f"{type(exc).__name__}: {exc}")


def start_run(cfg: dict) -> str:
    run_id = f"{datetime.now():%Y%m%d_%H%M%S}_{cfg['name']}"
    run_dir = RUNS_DIR / run_id
    (run_dir / "images").mkdir(parents=True, exist_ok=True)
    (run_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (run_dir / "inputs" / cfg["image_name"]).write_bytes(cfg["image_bytes"])
    if cfg["has_logo"]:
        (run_dir / "inputs" / cfg["logo_name"]).write_bytes(cfg["logo_bytes"])
    config_snapshot = {
        k: v for k, v in cfg.items() if not k.endswith("_bytes") and not k.endswith("_data_url")
    }
    (run_dir / "config.json").write_text(
        json.dumps(config_snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_progress(
        run_dir,
        name=cfg["name"],
        total=cfg["count"],
        done=0,
        ok=0,
        error=0,
        status="running",
        started=datetime.now().isoformat(timespec="seconds"),
    )
    threading.Thread(target=_worker, args=(cfg, run_dir), daemon=True).start()
    return run_id


def _to_data_url(file) -> str:
    return f"data:{file.type};base64,{base64.b64encode(file.getvalue()).decode('ascii')}"


# ── 설정 불러오기 ──────────────────────────────────────────────────────────
