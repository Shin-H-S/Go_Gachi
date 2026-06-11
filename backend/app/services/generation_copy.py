"""생성 흐름에서 쓰는 광고 문구 저장값과 캐시 입력을 조립한다."""

from backend.app.services.copywriting import AdCopy


def rendered_copy_text(text_copy: AdCopy | None) -> str | None:
    """이미지에 실제로 합성되는 광고 문구를 DB 저장용 문자열로 만든다."""
    if text_copy is None:
        return None

    lines = [text_copy.headline, text_copy.subcopy, text_copy.cta]
    rendered = "\n".join(line.strip() for line in lines if line and line.strip())
    return rendered or None


def cache_instruction(
    generation_user_prompt: str,
    text_copy: AdCopy | None,
    *,
    user_copy: str | None = None,
    has_logo: bool = False,
    logo_position: str | None = None,
    logo_image_hash: str | None = None,
) -> str:
    """캐시 키에 광고 문구와 로고 reference 정보를 반영한다."""
    if text_copy is None and not user_copy and not has_logo:
        return generation_user_prompt

    parts = [generation_user_prompt]
    if user_copy:
        parts.extend(["[User copy metadata]", user_copy])
    if text_copy:
        parts.extend(
            [
                "[Text overlay]",
                f"copyMode={text_copy.mode}",
                f"headline={text_copy.headline or ''}",
                f"subcopy={text_copy.subcopy or ''}",
                f"cta={text_copy.cta or ''}",
            ]
        )
    if has_logo:
        parts.extend(
            [
                "[Logo metadata]",
                f"logoPosition={logo_position or ''}",
                f"logoImageHash={logo_image_hash or ''}",
            ]
        )
    return "\n".join(parts)
