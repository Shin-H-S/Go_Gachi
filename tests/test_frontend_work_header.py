from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
WORK_COMPONENTS = ROOT_DIR / "frontend" / "work" / "components.py"


def test_mypage_navigation_keeps_streamlit_session() -> None:
    source = WORK_COMPONENTS.read_text(encoding="utf-8")

    assert 'href="?page=mypage"' not in source
    assert 'navigate_to("mypage")' in source
    assert 'key="work-mypage-link"' in source
