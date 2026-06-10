"""Cloudflare R2 저장소 구현."""

import logging
from pathlib import PurePosixPath
from typing import Final

import aioboto3
from botocore.exceptions import ClientError

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)

_NOT_FOUND_CODES: Final[set[str]] = {"404", "NoSuchKey", "NotFound"}


class R2Storage:
    """Cloudflare R2(S3 호환)를 사용하는 저장소."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def output_path(self, generation_id: str) -> str:
        return f"outputs/{generation_id}.png"

    def original_path(self, *, image_hash: str, extension: str, generation_id: str) -> str:
        _ = generation_id
        return f"uploads/{image_hash}.{extension}"

    async def write_bytes(self, path: str, body: bytes, *, content_type: str) -> None:
        session = aioboto3.Session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            await s3.put_object(
                Bucket=self.settings.r2_bucket_name,
                Key=path,
                Body=body,
                ContentType=content_type,
            )
        logger.info("r2 upload object_key=%s bytes=%d", path, len(body))

    async def read_bytes(self, path: str) -> bytes | None:
        session = aioboto3.Session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            try:
                response = await s3.get_object(Bucket=self.settings.r2_bucket_name, Key=path)
            except ClientError as exc:
                if _is_not_found(exc):
                    return None
                raise
            async with response["Body"] as body:
                return await body.read()

    async def exists(self, path: str) -> bool:
        session = aioboto3.Session()
        async with session.client("s3", **self._client_kwargs()) as s3:
            try:
                await s3.head_object(Bucket=self.settings.r2_bucket_name, Key=path)
                return True
            except ClientError as exc:
                if _is_not_found(exc):
                    return False
                raise

    def output_url(self, path: str | None) -> str | None:
        return self._public_url("outputs", path)

    def upload_url(self, path: str | None) -> str | None:
        return self._public_url("uploads", path)

    async def output_url_if_exists(self, path: str | None) -> str | None:
        # 마이페이지 목록에서는 DB 기록을 신뢰해 R2 HEAD 호출을 생략한다.
        return self.output_url(path)

    async def upload_url_if_exists(self, path: str | None) -> str | None:
        # 마이페이지 목록에서는 DB 기록을 신뢰해 R2 HEAD 호출을 생략한다.
        return self.upload_url(path)

    def _client_kwargs(self) -> dict[str, str]:
        return {
            "endpoint_url": self.settings.r2_endpoint_url,
            "aws_access_key_id": self.settings.r2_access_key_id,
            "aws_secret_access_key": self.settings.r2_secret_access_key,
            "region_name": "auto",
        }

    def _public_url(self, prefix: str, path: str | None) -> str | None:
        if path is None:
            return None
        normalized = str(path).replace("\\", "/").strip().lstrip("/")
        if not normalized:
            return None
        if normalized.startswith(f"{prefix}/"):
            object_key = normalized
        else:
            object_key = f"{prefix}/{PurePosixPath(normalized).name}"
        base = self.settings.r2_public_url.rstrip("/")
        return f"{base}/{object_key}"


def _is_not_found(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code", "")
    status = str(exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", ""))
    return code in _NOT_FOUND_CODES or status == "404"
