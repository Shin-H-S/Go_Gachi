"""프롬프트 조립 (분야별 템플릿 + 입력값 → 최종 프롬프트).

⚠️ 템플릿 내용·조립 로직은 '프롬프트 담당'의 영역이다.
백엔드는 끼울 자리(인터페이스)만 만들어 두고, 베이스라인에선 입력값을 단순 결합한 더미를 돌려준다.
프롬프트 담당은 아래 PROMPT_TEMPLATES 와 함수 내부만 채우면 된다.
"""

# 분야(업종)별 프롬프트 템플릿. 프롬프트 담당이 채운다.
# 예: {"음식점": "음식점 광고 이미지. {mood} 분위기. 매장: {store_name}. ..."}
PROMPT_TEMPLATES: dict[str, str] = {}


def build_prompt(
    industry: str,
    store_name: str,
    mood: str | None = None,
    ad_purpose: str | None = None,
    output_type: str | None = None,
) -> str:
    """입력값을 분야별 템플릿에 끼워 이미지 생성용 프롬프트를 만든다.

    Args:
        industry: 업종.
        store_name: 매장명.
        mood: 분위기(선택).
        ad_purpose: 광고 목적(선택).
        output_type: 출력 용도(선택).
    Returns:
        OpenAI 이미지 생성에 보낼 프롬프트 문자열.
    """
    # TODO(프롬프트 담당): PROMPT_TEMPLATES 기반의 실제 조립으로 교체
    parts = [f"{industry} 광고 이미지", store_name]
    if mood:
        parts.append(f"{mood} 분위기")
    if ad_purpose:
        parts.append(ad_purpose)
    if output_type:
        parts.append(output_type)
    return ", ".join(parts)
