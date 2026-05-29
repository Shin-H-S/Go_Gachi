"""API 요청/응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    detail_type: str | None = Field(default=None, alias="detailType")
    feedback: str = ""
    target_width: int | None = Field(default=None, alias="targetWidth", ge=1, le=4096)
    target_height: int | None = Field(default=None, alias="targetHeight", ge=1, le=4096)

    @model_validator(mode="after")
    def validate_target_size(self) -> "GenerateRequest":
        """최종 출력 크기는 너비와 높이를 한 쌍으로만 받는다."""
        if (self.target_width is None) != (self.target_height is None):
            raise ValueError("targetWidth와 targetHeight는 함께 전달해야 합니다.")
        return self


class GenerateResponse(BaseModel):
    """이미지 생성 응답 본문."""

    model_config = ConfigDict(populate_by_name=True)

    image_data_url: str = Field(alias="imageDataUrl")
    provider: str
    preset: Preset
    note: str | None = None
    prompt: str | None = None
