from pydantic import BaseModel

from backend.app.db.models import Folder


class FolderCreateRequest(BaseModel):
    name: str


class FolderUpdateRequest(BaseModel):
    name: str


class GenerationFolderRequest(BaseModel):
    folder_id: int | None = None


def _folder_item(folder: Folder) -> dict[str, object]:
    return {
        "id": folder.id,
        "name": folder.name,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
    }
