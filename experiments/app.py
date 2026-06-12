"""Streamlit entrypoint for the prompt test console.

Run:
  uv run streamlit run experiments/app.py
"""

from datetime import datetime

import streamlit as st
from app_common import ROOT_DIR  # noqa: F401  Ensures backend imports resolve.
from app_prompting import prompt_drift_report
from app_ui_compare import render_compare_tab
from app_ui_new import render_new_tab
from app_ui_results import render_results_tab

st.set_page_config(page_title="프롬프트 테스트 콘솔", layout="wide")


def _default_test_name() -> str:
    return f"{datetime.now():%Y-%m-%d_%H%M%S}"


# 위젯 생성 전에 처리해야 하는 세션 상태 갱신 (설정 불러오기 / 테스트명 초기화)
if "_pending_load" in st.session_state:
    for key, value in st.session_state.pop("_pending_load").items():
        st.session_state[key] = value
if st.session_state.pop("_reset_test_name", False):
    st.session_state["test_name"] = _default_test_name()
st.session_state.setdefault("test_name", _default_test_name())
st.session_state.setdefault("count", 2)
st.session_state.setdefault("quality", "low")

st.title("프롬프트 테스트 콘솔")

# 백엔드 프롬프트와 콘솔 조립의 어긋남(드리프트) 자동 감지 — 문자열 비교라 비용 0.
_drift = prompt_drift_report()
if _drift:
    st.warning(
        "백엔드 프롬프트가 변경되어 콘솔 조립과 어긋났습니다 — "
        "지금 콘솔에서 생성하면 서비스와 다른 프롬프트가 사용됩니다. "
        "아래 진단 리포트를 펼쳐 전체 복사한 뒤 AI 어시스턴트(Claude)에게 붙여넣으면 "
        "동기화 수정을 받을 수 있습니다."
    )
    with st.expander("프롬프트 드리프트 진단 리포트 (전체 복사용)"):
        st.code(_drift, language=None)

tab_new, tab_results, tab_compare = st.tabs(["새 테스트", "결과 · 평가", "테스트 모아보기"])

with tab_new:
    render_new_tab()

with tab_results:
    render_results_tab()

with tab_compare:
    render_compare_tab()
