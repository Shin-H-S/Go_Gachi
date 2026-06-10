"""저장소 구현체가 지켜야 하는 공통 인터페이스."""

from typing import Protocol


class Storage(Protocol):
    """local/R2 저장소가 공통으로 제공하는 동작."""

    def output_path(self, generation_id: str) -> str:
        """생성 결과 이미지 저장 위치를 만든다."""
        ...

    def original_path(self, *, image_hash: str, extension: str, generation_id: str) -> str:
        """업로드 원본 이미지 저장 위치를 만든다."""
        ...

    async def write_bytes(self, path: str, body: bytes, *, content_type: str) -> None:
        """바이트를 저장한다."""
        ...

    async def read_bytes(self, path: str) -> bytes | None:
        """저장된 바이트를 읽는다. 없으면 None."""
        ...

    async def exists(self, path: str) -> bool:
        """저장 위치에 객체/파일이 있는지 확인한다."""
        ...

    def output_url(self, path: str | None) -> str | None:
        """생성 결과 이미지의 프론트 표시 URL을 만든다."""
        ...

    def upload_url(self, path: str | None) -> str | None:
        """업로드 원본 이미지의 프론트 표시 URL을 만든다."""
        ...

    async def output_url_if_exists(self, path: str | None) -> str | None:
        """생성 결과가 존재할 때만 프론트 표시 URL을 만든다."""
        ...

    async def upload_url_if_exists(self, path: str | None) -> str | None:
        """업로드 원본이 존재할 때만 프론트 표시 URL을 만든다."""
        ...
