def build_user_prompt(
    prompt: str,
    detail_label: str,
) -> str:
    parts = [f"광고 유형: {detail_label}"]
    clean_prompt = prompt.strip()

    if clean_prompt:
        parts.append(f"이미지 요청:\n{clean_prompt}")

    return "\n\n".join(parts)
