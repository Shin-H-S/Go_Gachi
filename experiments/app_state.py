"""Saved run and widget-state helpers for the experiments Streamlit console."""

from pathlib import Path

from app_common import RUNS_DIR
from app_prompting import (
    API_SIZE_LABELS,
    API_SIZES,
    COPY_MODE_LABELS,
    DIRECT,
    REPO_DEFAULT,
)


def widget_state_from_cfg(cfg: dict) -> dict:
    """config.json 스냅샷을 탭1 위젯 세션 상태로 변환한다 (이미지 제외)."""
    state: dict = {"channel": cfg["channel_label"]}
    if cfg["channel_label"] == DIRECT:
        state["channel_custom"] = cfg["channel_hint"]
    state[f"detail_{cfg['channel_label']}"] = cfg["detail_label"]
    if cfg["detail_label"] == DIRECT:
        state[f"detail_custom_{cfg['channel_label']}"] = cfg["detail_hint"]
        state["api_size"] = API_SIZE_LABELS.get(cfg["api_size"], API_SIZES[0][0])
    state["copy_on"] = cfg["copy_on"]
    state["copy_text"] = cfg["copy_text"]
    state["copy_mode"] = COPY_MODE_LABELS.get(cfg["copy_mode"], "그대로 사용")
    state["copy_mode_custom"] = cfg["copy_mode_custom"]
    state["copy_source"] = DIRECT if cfg["copy_instr_custom"] else REPO_DEFAULT
    state["copy_instr_custom"] = cfg["copy_instr_custom"]
    state["user_prompt"] = cfg.get("user_prompt", "")
    state["count"] = int(cfg["count"])
    state["quality"] = cfg["quality"]
    return state


def list_runs(require: str) -> list[tuple[str, Path]]:
    """require 파일이 있는 run 폴더를 최신순으로 돌려준다."""
    if not RUNS_DIR.exists():
        return []
    found = [d for d in RUNS_DIR.iterdir() if d.is_dir() and (d / require).exists()]
    found.sort(key=lambda d: d.name, reverse=True)
    return [(d.name, d) for d in found]


# ── 평가 저장/불러오기 ─────────────────────────────────────────────────────
