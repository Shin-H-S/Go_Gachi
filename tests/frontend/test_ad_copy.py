from frontend.work.copy import build_auto_copy, copy_mode_for_prompt


def test_build_auto_copy_returns_headline_subcopy_and_cta() -> None:
    copy_text = build_auto_copy("인스타그램", "정사각형 피드")

    assert "헤드라인:" in copy_text
    assert "서브카피:" in copy_text
    assert "CTA:" in copy_text
    assert "인스타그램" in copy_text


def test_copy_mode_for_prompt_matches_text_overlay_state() -> None:
    assert copy_mode_for_prompt(text_overlay_enabled=False, prompt="anything") == "preserve"
    assert copy_mode_for_prompt(text_overlay_enabled=True, prompt="   ") == "rewrite"
    assert copy_mode_for_prompt(text_overlay_enabled=True, prompt="오늘만 할인") == "polish"

