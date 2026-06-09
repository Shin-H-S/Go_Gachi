from backend.app.services.copywriting import AdCopy
from backend.app.services.generation_copy import cache_instruction, rendered_copy_text


def test_rendered_copy_text_joins_rendered_lines() -> None:
    copy = AdCopy(
        headline=" 딸기 케이크 ",
        subcopy="오늘만 6,500원",
        cta=None,
        mode="preserve",
    )

    assert rendered_copy_text(copy) == "딸기 케이크\n오늘만 6,500원"


def test_rendered_copy_text_returns_none_without_copy() -> None:
    assert rendered_copy_text(None) is None


def test_cache_instruction_returns_base_prompt_without_metadata() -> None:
    assert cache_instruction("base prompt", None) == "base prompt"


def test_cache_instruction_includes_text_and_logo_metadata() -> None:
    copy = AdCopy(
        headline="라떼 4,500원",
        subcopy="카페에서 더 맛있게 즐겨보세요.",
        cta=None,
        mode="polish",
    )

    result = cache_instruction(
        "base prompt",
        copy,
        user_copy="라떼 4500원",
        has_logo=True,
        logo_position="bottom_right",
    )

    assert "[User copy metadata]\n라떼 4500원" in result
    assert "[Text overlay]" in result
    assert "headline=라떼 4,500원" in result
    assert "subcopy=카페에서 더 맛있게 즐겨보세요." in result
    assert "[Logo metadata]\nlogoPosition=bottom_right" in result
