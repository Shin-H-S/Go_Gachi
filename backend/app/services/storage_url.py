"""저장된 결과 파일 → 외부에서 접근 가능한 정적 URL 변환.

지금은 로컬 ``/outputs`` 정적 마운트를 기준으로 URL을 만든다.
GCS / signed URL 등 다른 백엔드로 옮길 때 이 모듈만 교체하면 된다.
"""

from pathlib import Path

from backend.app.core.config import Settings


def public_output_url(settings: Settings, output_path: Path | str | None) -> str | None:
    """저장된 결과 파일 경로를 브라우저에서 접근 가능한 ``/outputs`` URL로 변환한다.

    Args:
        settings: ``base_url``을 참조하기 위한 런타임 설정.
        output_path: 결과 파일의 경로. ``None`` 또는 빈 값이면 URL을 만들 수 없다.
    Returns:
        ``{base_url}/outputs/{filename}`` 형태의 URL, 또는 ``None``.
    """
    if output_path is None:
        return None
    filename = Path(output_path).name
    if not filename:
        return None
    return f"{settings.base_url}/outputs/{filename}"
