from collections.abc import Sequence
from typing import TypeVar

UploadedFileT = TypeVar("UploadedFileT")

UPLOAD_FILE_TYPES = ["jpg", "jpeg", "png", "webp"]
UPLOAD_HELP_TEXT = (
    "JPG, PNG, WEBP 파일을 업로드할 수 있습니다. "
    "백엔드에서 OpenAI 호출 전 PNG/RGB 형식으로 정리합니다."
)


def get_primary_uploaded_file(
    uploaded_files: UploadedFileT | Sequence[UploadedFileT] | None,
) -> UploadedFileT | None:
    if uploaded_files is None:
        return None

    if isinstance(uploaded_files, Sequence) and not isinstance(
        uploaded_files,
        str | bytes | bytearray,
    ):
        return uploaded_files[0] if uploaded_files else None

    return uploaded_files
