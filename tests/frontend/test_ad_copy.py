from frontend.work.copy import COPY_MODE_OPTIONS, build_auto_copy


def test_build_auto_copy_returns_headline_subcopy_and_cta() -> None:
    copy_text = build_auto_copy("인스타그램", "정사각형 피드")

    assert "헤드라인:" in copy_text
    assert "서브카피:" in copy_text
    assert "CTA:" in copy_text
    assert "인스타그램" in copy_text


def test_copy_mode_options_use_backend_values_and_korean_labels() -> None:
    assert COPY_MODE_OPTIONS == (
        ("그대로 사용", "preserve"),
        ("자연스럽게 다듬기", "polish"),
        ("홍보 문구로 바꾸기", "rewrite"),
    )

