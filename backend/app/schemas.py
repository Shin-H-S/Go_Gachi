"""API 요청/응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.core.presets import Preset


class ConfigResponse(BaseModel):
    """프론트 초기 설정에 필요한 프리셋과 provider 정보."""

    presets: list[Preset]
    provider: str
    max_upload_bytes: int = Field(alias="maxUploadBytes")


class GenerateRequest(BaseModel):
    """이미지 생성 요청 본문."""

    image_data_url: str = Field(alias="imageDataUrl")
    preset_id: str | None = Field(default=None, alias="presetId")
    feedback: str = ""


class GenerateResponse(BaseModel):
    """이미지 생성 응답 본문."""

    model_config = ConfigDict(populate_by_name=True)

    image_data_url: str = Field(alias="imageDataUrl")
    provider: str
    preset: Preset
    note: str | None = None
    prompt: str | None = None
