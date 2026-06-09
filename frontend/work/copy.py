from typing import Literal

CopyMode = Literal["preserve", "polish", "rewrite"]


def build_auto_copy(format_label: str, detail_label: str) -> str:
    """선택한 광고 채널/유형에 맞춘 기본 광고 문구 초안을 만든다."""
    channel = format_label.strip() or "광고"
    detail = detail_label.strip() or "이미지"

    if "배달" in channel:
        headline = "지금 바로 주문하고 싶은 메뉴"
        subcopy = f"{channel} {detail}에서 한눈에 보이도록 맛과 분위기를 또렷하게 전해요."
        cta = "바로 주문하기"
    elif "당근" in channel:
        headline = "동네에서 만나는 오늘의 맛"
        subcopy = f"{channel} {detail}에 어울리게 가까운 이웃에게 메뉴의 매력을 소개해요."
        cta = "가게 보러가기"
    elif "인스타" in channel:
        headline = "오늘 가장 맛있는 한 컷"
        subcopy = f"{channel} {detail}에서 시선이 머무르도록 메뉴의 분위기를 감각적으로 보여줘요."
        cta = "지금 저장하기"
    else:
        headline = "오늘의 추천 메뉴"
        subcopy = f"{channel} {detail}에 맞게 메뉴의 장점이 잘 보이는 광고 문구를 제안해요."
        cta = "지금 확인하기"

    return f"헤드라인: {headline}\n서브카피: {subcopy}\nCTA: {cta}"


def copy_mode_for_prompt(*, text_overlay_enabled: bool, prompt: str) -> CopyMode:
    if not text_overlay_enabled:
        return "preserve"
    if prompt.strip():
        return "polish"
    return "rewrite"

