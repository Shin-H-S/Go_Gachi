from collections.abc import Sequence
from typing import TypeVar

UploadedFileT = TypeVar("UploadedFileT")


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
