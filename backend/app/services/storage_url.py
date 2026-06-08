"""저장된 결과 파일 경로를 프론트가 쓸 수 있는 정적 경로로 변환한다.

백엔드는 ``/outputs/result.png`` 같은 루트 상대 경로만 돌려주고,
프론트는 환경별 backend origin을 직접 붙여 사용한다. 그래서 응답에는
local/VM/Cloud Run 호스트 같은 환경 의존 값을 박지 않는다.
"""

import asyncio
from pathlib import Path


def output_url(output_path: Path | str | None) -> str | None:
    """저장된 결과 파일의 ``/outputs`` 루트 상대 경로를 만든다.

    Args:
        output_path: 저장된 결과 파일 경로. ``None``이거나 파일명이 비면 ``None``.
    Returns:
        ``/outputs/{filename}`` 또는 ``None``.
    """
    if output_path is None:
        return None
    filename = Path(output_path).name
    if not filename:
        return None
    return f"/outputs/{filename}"


def output_url_if_exists(output_path: Path | str | None) -> str | None:
    """저장된 결과 파일이 실제 디스크에 존재할 때만 ``/outputs`` 경로를 만든다.

    옛 기록 중 파일이 사라진 행은 ``None``으로 응답해 마이페이지에서 깨진
    이미지 링크가 노출되지 않도록 막는다.

    Args:
        output_path: 저장된 결과 파일 경로. ``None``이거나 파일이 없으면 ``None``.
    Returns:
        ``/outputs/{filename}`` 또는 ``None``.
    """
    if output_path is None:
        return None
    path = Path(output_path)
    if not path.is_file():
        return None
    return output_url(path)


async def output_url_if_exists_async(
    output_path: Path | str | None,
) -> str | None:
    """``output_url_if_exists``의 비동기 버전.

    디스크 stat(``is_file``)을 별도 스레드에서 실행해 FastAPI 이벤트 루프를
    차단하지 않는다. 마이페이지처럼 한 요청에서 여러 행을 검사할 때 사용한다.
    """
    if output_path is None:
        return None
    path = Path(output_path)
    exists = await asyncio.to_thread(path.is_file)
    if not exists:
        return None
    return output_url(path)
