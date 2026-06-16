from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

UploadedFileT = TypeVar("UploadedFileT")

HANDOFF_UPLOAD_BYTES_KEY = "work_handoff_upload_bytes"
HANDOFF_UPLOAD_NAME_KEY = "work_handoff_upload_name"
HANDOFF_UPLOAD_TYPE_KEY = "work_handoff_upload_type"

UPLOAD_FILE_TYPES = ["jpg", "jpeg", "png", "webp"]
UPLOAD_HELP_TEXT = (
    "JPG, PNG, WEBP 파일을 업로드할 수 있습니다. "
    "백엔드에서 OpenAI 호출 전 PNG/RGB 형식으로 정리합니다."
)


@dataclass(frozen=True)
class HandoffUploadedFile:
    name: str
    type: str
    _value: bytes

    def getvalue(self) -> bytes:
        return self._value


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


def set_handoff_uploaded_file(
    session_state: MutableMapping[str, object],
    *,
    image_bytes: bytes,
    file_name: str,
    mime_type: str,
) -> None:
    session_state[HANDOFF_UPLOAD_BYTES_KEY] = bytes(image_bytes)
    session_state[HANDOFF_UPLOAD_NAME_KEY] = file_name
    session_state[HANDOFF_UPLOAD_TYPE_KEY] = mime_type


def get_handoff_uploaded_file(
    session_state: MutableMapping[str, object],
) -> HandoffUploadedFile | None:
    image_bytes = session_state.get(HANDOFF_UPLOAD_BYTES_KEY)
    if not isinstance(image_bytes, bytes):
        return None

    file_name = str(session_state.get(HANDOFF_UPLOAD_NAME_KEY) or "selected-image.png")
    mime_type = str(session_state.get(HANDOFF_UPLOAD_TYPE_KEY) or "application/octet-stream")
    return HandoffUploadedFile(name=file_name, type=mime_type, _value=image_bytes)


def clear_handoff_uploaded_file(session_state: MutableMapping[str, object]) -> None:
    session_state.pop(HANDOFF_UPLOAD_BYTES_KEY, None)
    session_state.pop(HANDOFF_UPLOAD_NAME_KEY, None)
    session_state.pop(HANDOFF_UPLOAD_TYPE_KEY, None)


def get_effective_uploaded_file(
    uploaded_files: UploadedFileT | Sequence[UploadedFileT] | None,
    session_state: MutableMapping[str, object],
) -> UploadedFileT | HandoffUploadedFile | None:
    uploaded_file = get_primary_uploaded_file(uploaded_files)
    if uploaded_file is not None:
        clear_handoff_uploaded_file(session_state)
        return uploaded_file
    return get_handoff_uploaded_file(session_state)
