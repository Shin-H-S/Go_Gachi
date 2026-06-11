from backend.app.services.copywriting import build_ad_copy


def test_build_ad_copy_preserves_user_prompt_without_metadata() -> None:
    copy = build_ad_copy("광고 유형: 스토리 이미지\n오늘 아메리카노 2500원", "preserve")

    assert copy.headline == "오늘 아메리카노 2,500원"
    assert copy.subcopy is None
    assert copy.cta is None
    assert copy.mode == "preserve"

def test_build_ad_copy_polishes_user_prompt() -> None:
    copy = build_ad_copy("  오늘   라떼   4500원  ", "polish")

    assert copy.headline == "오늘 라떼 4,500원"
    assert copy.subcopy == "카페에서 더 맛있게 즐겨보세요."
    assert copy.cta is None
    assert copy.mode == "polish"


def test_build_ad_copy_rewrites_with_promotional_context() -> None:
    copy = build_ad_copy("딸기 케이크 6500원", "rewrite")

    assert "딸기 케이크 6,500원" in copy.headline
    assert copy.subcopy is not None
    assert copy.cta == "지금 방문해보세요"
    assert copy.mode == "rewrite"


def test_build_ad_copy_returns_fallback_when_user_prompt_is_empty() -> None:
    copy = build_ad_copy("광고 유형: 메뉴 이미지", "preserve")

    assert copy.headline
    assert copy.subcopy
    assert copy.cta
    assert copy.mode == "preserve"
