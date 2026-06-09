"""V3 광고 문구 처리 서비스.

이미지 합성 전 단계에서 사용자 요청을 광고 문구 구조로 정리한다.
실제 텍스트 렌더링은 후속 overlay_text 모듈에서 담당한다.
"""

import re

from pydantic import BaseModel

from backend.app.schemas import CopyMode

_WHITESPACE_RE = re.compile(r"\s+")
_PRICE_RE = re.compile(r"(?P<number>\d{4,})(?P<unit>\s*원)")


class AdCopy(BaseModel):
    """후처리 합성에 사용할 광고 문구 구조."""

    headline: str | None = None
    subcopy: str | None = None
    cta: str | None = None
    mode: CopyMode


def _normalize_text(text: str) -> str:
    """문구 처리 공통 정규화. 숫자 가격은 가독성을 위해 콤마를 넣는다."""
    normalized = _WHITESPACE_RE.sub(" ", text.strip())

    def _format_price(match: re.Match[str]) -> str:
        number = f"{int(match.group('number')):,}"
        return f"{number}{match.group('unit').strip()}"

    return _PRICE_RE.sub(_format_price, normalized)


def _user_copy_text(user_prompt: str) -> str:
    """프론트가 붙인 보조 메타데이터를 제외하고 실제 사용자 문구만 남긴다."""
    lines = []
    for line in user_prompt.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("광고 유형:"):
            continue
        lines.append(stripped)
    return _normalize_text(" ".join(lines))


def _fallback_copy(copy_mode: CopyMode) -> AdCopy:
    """문구 미입력 시 카페 광고 기본 문구를 제공한다."""
    return AdCopy(
        headline="오늘도 기분 좋은 카페 한 잔",
        subcopy="가볍게 들르기 좋은 동네 카페 메뉴를 만나보세요.",
        cta="지금 매장에서 확인해보세요",
        mode=copy_mode,
    )


def _rewrite_copy(text: str, copy_mode: CopyMode) -> AdCopy:
    """사용자 문구의 핵심 조건은 유지하면서 홍보성 헤드라인으로 정리한다."""
    return AdCopy(
        headline=f"오늘 놓치기 아까운 {text}",
        subcopy="카페에서 즐기는 신선한 메뉴를 더 맛있게 전해드려요.",
        cta="지금 방문해보세요",
        mode=copy_mode,
    )


def build_ad_copy(user_prompt: str, copy_mode: CopyMode) -> AdCopy:
    """사용자 요청과 copyMode를 합성용 광고 문구로 변환한다."""
    text = _user_copy_text(user_prompt)
    if not text:
        return _fallback_copy(copy_mode)

    if copy_mode == "rewrite":
        return _rewrite_copy(text, copy_mode)

    if copy_mode == "polish":
        return AdCopy(
            headline=text,
            subcopy="카페에서 더 맛있게 즐겨보세요.",
            cta=None,
            mode=copy_mode,
        )

    return AdCopy(headline=text, subcopy=None, cta=None, mode=copy_mode)
