"""광고 문구 생성.

⚠️ 실제 프롬프트/문구 생성은 '프롬프트 담당'의 영역이다.
백엔드는 끼울 자리(인터페이스)만 두고, 비용 방지를 위해 베이스라인에선 더미 응답을 돌려준다.
추후 OpenAI 연동 시 이 함수 내부만 교체하면 된다.
"""


async def generate_ad_copy(
    store_name: str,
    industry: str,
    ad_purpose: str | None = None,
    mood: str | None = None,
    output_type: str | None = None,
    price: str | None = None,
    contact: str | None = None,
) -> dict:
    """광고 문구와 해시태그를 생성한다. (현재는 비용 방지용 더미)

    Args:
        store_name: 매장명.
        industry: 업종.
        ad_purpose: 광고 목적(선택).
        mood: 분위기(선택).
        output_type: 출력 용도(선택).
        price: 가격(선택).
        contact: 연락처(선택).
    Returns:
        {"ad_copy": 광고문구(str), "hashtags": 해시태그(list[str])} 형태의 dict.
    """
    # TODO(프롬프트 담당 + OpenAI 연동): 실제 GPT 호출로 교체
    details = [
        f"업종: {industry}",
        f"목적: {ad_purpose or '일반 광고'}",
        f"분위기: {mood or '기본'}",
        f"용도: {output_type or '일반'}",
    ]
    if price:
        details.append(f"가격: {price}")
    if contact:
        details.append(f"문의: {contact}")

    copy = f"{store_name} 광고 문구 더미 - " + " / ".join(details)
    return {
        "ad_copy": copy,
        "hashtags": [f"#{industry}", f"#{store_name}", "#광고"],
    }
