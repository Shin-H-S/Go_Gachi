"""사용자 입력에서 파생되는 프롬프트·출력 크기 가공 헬퍼."""

from backend.app.core.presets import PresetDetail
from backend.app.services.image_types import ResizeMode, TargetSize


def target_size_or_detail(
    *,
    detail: PresetDetail,
    target_width: int | None,
    target_height: int | None,
) -> TargetSize:
    """출력 크기를 정한다. target 가로·세로가 비면 detail 기본 크기로 폴백한다."""
    if target_width is None or target_height is None:
        return TargetSize(width=detail.width, height=detail.height)
    return TargetSize(width=target_width, height=target_height)


def feedback_with_context(
    feedback: str,
    target_size: TargetSize,
    detail: PresetDetail | None,
    resize_mode: ResizeMode,
) -> str:
    """프롬프트·캐시 키에 최종 출력 크기와 상세 광고 유형 컨텍스트를 함께 반영한다."""
    context_parts = [
        f"Target output canvas: {target_size.width}x{target_size.height}px. "
        "Compose for this final aspect ratio."
    ]
    if resize_mode == "contain":
        context_parts.append("Final resize mode: contain. Preserve the full generated image.")
    else:
        context_parts.append("Final resize mode: cover. Fill the canvas edge to edge.")
    if detail:
        context_parts.append(f"Selected detail type: {detail.id} ({detail.label}).")

    clean_feedback = (feedback or "").strip()
    if clean_feedback:
        context_parts.append(clean_feedback)
    return "\n".join(context_parts)
