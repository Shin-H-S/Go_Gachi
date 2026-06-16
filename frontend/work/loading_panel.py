from html import escape
from random import randrange

from frontend.work.loading_icons import LOADING_ICON_FILES, loading_icon_data_url

LOADING_TIP_INTERVAL_SECONDS = 7

LOADING_BACKGROUNDS = (
    "#9fdcf5",
    "#ffb8ca",
    "#ffe17a",
    "#aee9c2",
    "#c8b8ff",
    "#ffb38d",
    "#9ee0d3",
    "#f5a9d0",
    "#b7d8ff",
    "#d6f58a",
    "#ffc7a6",
    "#f2c4ff",
)

_LAST_LOADING_START_INDEX: int | None = None

LOADING_TIPS = (
    {
        "kind": "photo",
        "title": "광고할 상품에 초점을 맞춰 촬영해 주세요",
        "body": "초점이 어긋나면 다른 결과가 나올 수 있어요",
    },
    {
        "kind": "photo",
        "title": "밝은 곳에서 흔들림 없이 촬영해 주세요",
        "body": "어두움이나 흔들림은 질감과 색감을 흐리게 만들 수 있어요",
    },
    {
        "kind": "photo",
        "title": "반사, 그림자, 비닐이 상품을 가리지 않게 해주세요",
        "body": "가려진 영역은 의도와 다르게 표현될 수 있어요",
    },
    {
        "kind": "object",
        "title": "중요한 토핑과 데코가 선명하게 보이도록 촬영해 주세요",
        "body": "작은 장식은 흐리면 재생성 과정에서 생략될 수 있어요",
    },
    {
        "kind": "object",
        "title": "주변 소품은 최소화하고 상품이 주인공이 되게 해주세요",
        "body": "대상이 많으면 메인 상품 인식이 어려워질 수 있어요",
    },
    {
        "kind": "object",
        "title": "같은 제품이라면 가장 잘 나온 사진 한 장만 선택해 주세요",
        "body": "대표 사진이 또렷할수록 결과도 안정적으로 나와요",
    },
    {
        "kind": "framing",
        "title": "상품 주변에 여백을 조금 남겨 주세요",
        "body": "다양한 플랫폼 비율에서도 자연스럽게 구성돼요",
    },
    {
        "kind": "framing",
        "title": "상품 전체가 화면 안에 보이도록 촬영해 주세요",
        "body": "일부가 잘리면 형태가 다르게 생성될 수 있어요",
    },
    {
        "kind": "framing",
        "title": "컵이나 그릇은 정면 또는 살짝 사선으로 촬영해 주세요",
        "body": "과하게 기울어진 사진은 형태가 찌그러질 수 있어요",
    },
    {
        "kind": "prompt",
        "title": "원하는 수정 방향을 구체적으로 적어 주세요",
        "body": "예: 따뜻한 색감, 밝게, 배경만 변경",
    },
    {
        "kind": "prompt",
        "title": "수정하고 싶은 부분만 요청해 주세요",
        "body": "필요한 부분만 바꾸면 원본 특징을 유지하기 쉬워요",
    },
    {
        "kind": "prompt",
        "title": "요청이 여러 개라면 우선순위를 적어 주세요",
        "body": "예: 상품 유지 > 배경 변경 > 색감 보정",
    },
    {
        "kind": "copy",
        "title": "광고 문구는 짧고 핵심만 입력해 주세요",
        "body": "문구가 길수록 레이아웃과 가독성이 흔들릴 수 있어요",
    },
    {
        "kind": "copy",
        "title": "문구가 생각나지 않으면 광고 문구 칸을 비워보세요",
        "body": "기본 문구 생성을 활용할 수 있어요",
    },
    {
        "kind": "mypage",
        "title": "마음에 드는 결과는 이어작업으로 다시 가져올 수 있어요",
        "body": "작업 페이지에서 같은 이미지를 이어서 변형해보세요",
    },
    {
        "kind": "mypage",
        "title": "생성한 이미지는 폴더로 나눠 정리할 수 있어요",
        "body": "시즌 메뉴, 이벤트, 채널별 이미지처럼 따로 모아보세요",
    },
    {
        "kind": "mypage",
        "title": "마이페이지에서 여러 이미지를 ZIP으로 받을 수 있어요",
        "body": "필요한 결과물을 묶어서 빠르게 저장해보세요",
    },
)


def _next_loading_start_index() -> int:
    global _LAST_LOADING_START_INDEX

    tip_count = len(LOADING_TIPS)
    if tip_count <= 1:
        _LAST_LOADING_START_INDEX = 0
        return 0

    next_index = randrange(tip_count - 1)
    if _LAST_LOADING_START_INDEX is not None and next_index >= _LAST_LOADING_START_INDEX:
        next_index += 1
    _LAST_LOADING_START_INDEX = next_index
    return next_index


def _normalized_start_index(start_index: int | None) -> int:
    if not LOADING_TIPS:
        return 0
    if start_index is None:
        return _next_loading_start_index()
    return start_index % len(LOADING_TIPS)


def loading_panel_html(start_index: int | None = None) -> str:
    cards = []
    first_index = _normalized_start_index(start_index)
    for index in range(len(LOADING_TIPS)):
        source_index = (first_index + index) % len(LOADING_TIPS)
        tip = LOADING_TIPS[source_index]
        background = LOADING_BACKGROUNDS[source_index % len(LOADING_BACKGROUNDS)]
        icon_file = LOADING_ICON_FILES[source_index % len(LOADING_ICON_FILES)]
        icon_src = loading_icon_data_url(icon_file)
        cards.append(
            
                '<article class="loading-tip-card" '
                f'style="--tip-index: {index}; --tip-bg: {background};">'
                '<div class="loading-tip-content">'
                '<div class="loading-clay-icon-wrap">'
                f'<img class="loading-clay-icon" src="{icon_src}" alt="" aria-hidden="true" />'
                "</div>"
                '<div class="loading-tip-heading">'
                f'<strong>{escape(str(tip["title"]))}</strong>'
                "</div>"
                f'<p>{escape(str(tip["body"]))}</p>'
                "</div>"
                "</article>"
            
        )
    return (
        '<div class="loading-state">'
        '<div class="loading-tip-stage" aria-live="polite">'
        + "".join(cards)
        + '<div class="loading-status">'
        '<span>이미지를 다듬는 중이에요</span>'
        '<div class="loading-progress-dots" aria-hidden="true">'
        "<span></span><span></span><span></span>"
        "</div>"
        "</div>"
        "</div>"
        "</div>"
    )
