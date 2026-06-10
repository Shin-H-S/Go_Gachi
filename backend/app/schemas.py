"""API 요청/응답 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.core.presets import Preset

ResizeMode = Literal["cover", "contain"]
CopyMode = Literal["preserve", "polish", "rewrite"]
LogoPosition = Literal[
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "center_bottom",
]


class ConfigResponse(BaseModel):
    """프론트 초기 설정에 필요한 프리셋과 provider 정보."""

    presets: list[Preset]
    provider: str
    max_upload_bytes: int = Field(alias="maxUploadBytes")


class GenerateRequest(BaseModel):
    """이미지 생성 요청 본문."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image_data_url: str = Field(alias="imageDataUrl")
    preset_id: str | None = Field(default=None, alias="presetId")
    detail_type: str | None = Field(default=None, alias="detailType")
    user_prompt: str = Field(default="", alias="userPrompt")
    copy_mode: CopyMode = Field(default="preserve", alias="copyMode")
    ad_copy_enabled: bool = Field(default=False, alias="adCopyEnabled")
    user_copy: str | None = Field(default=None, alias="userCopy", max_length=300)
    logo_data_url: str | None = Field(default=None, alias="logoDataUrl", max_length=8_000_000)
    logo_position: LogoPosition = Field(default="bottom_right", alias="logoPosition")
    parent_request_id: str | None = Field(default=None, alias="parentRequestId")
    target_width: int | None = Field(default=None, alias="targetWidth", ge=1, le=4096)
    target_height: int | None = Field(default=None, alias="targetHeight", ge=1, le=4096)
    resize_mode: ResizeMode = Field(default="cover", alias="resizeMode")

    @model_validator(mode="after")
    def validate_target_size(self) -> "GenerateRequest":
        """최종 출력 크기는 너비와 높이를 한 쌍으로만 받는다."""
        if (self.target_width is None) != (self.target_height is None):
            raise ValueError("targetWidth와 targetHeight는 함께 전달해야 합니다.")
        return self


class CopyGenerateRequest(BaseModel):
    """광고 문구 자동 생성 요청 본문."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preset_id: str | None = Field(default=None, alias="presetId")
    detail_type: str | None = Field(default=None, alias="detailType")
    user_prompt: str = Field(default="", alias="userPrompt")
    copy_mode: CopyMode = Field(default="rewrite", alias="copyMode")


class CopyResponse(BaseModel):
    """V3 문구 처리 결과. 이미지 프롬프트에 포함할 광고 문구를 담는다."""

    model_config = ConfigDict(populate_by_name=True)

    headline: str | None = None
    subcopy: str | None = None
    cta: str | None = None
    mode: CopyMode | None = Field(default=None, alias="copyMode")


class LogoResponse(BaseModel):
    """V3 로고 반영 결과. 로고 기능이 꺼져 있으면 used=false로 내려갈 수 있다."""

    used: bool = False
    position: LogoPosition | None = None


class RevisionResponse(BaseModel):
    """V3 수정 이력 정보. 최초 생성이면 parentRequestId는 null이다."""

    model_config = ConfigDict(populate_by_name=True)

    parent_request_id: str | None = Field(default=None, alias="parentRequestId")
    revision_number: int | None = Field(default=None, alias="revisionNumber")


class GenerateResponse(BaseModel):
    """이미지 생성 응답 본문."""

    model_config = ConfigDict(populate_by_name=True)

    image_data_url: str = Field(alias="imageDataUrl")
    # 같은 이미지를 외부에서 받을 수 있는 http(s) URL. mock 분기는 파일 저장이 없어 None.
    image_url: str | None = Field(default=None, alias="imageUrl")
    provider: str
    preset: Preset
    copy_info: CopyResponse | None = Field(default=None, alias="copy")
    logo_info: LogoResponse | None = Field(default=None, alias="logo")
    revision_info: RevisionResponse | None = Field(default=None, alias="revision")
    note: str | None = None
    prompt: str | None = None
