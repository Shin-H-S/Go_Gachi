param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectId,
  [string]$Region = "asia-northeast3",
  [string]$Repository = "cafe-ad-maker",
  [string]$Service = "cafe-ad-maker-v1",
  [string]$Provider = "openai",
  [string]$TextModel = "gpt-5",
  [string]$ImageModel = "gpt-image-2",
  [string]$Quality = "medium",
  [string]$Secret = "OPENAI_API_KEY"
)

$ErrorActionPreference = "Stop"
$gcloud = "gcloud.cmd"

& $gcloud config set project $ProjectId
& $gcloud builds submit . `
  --config cloudbuild.yaml `
  --substitutions "_REGION=$Region,_REPOSITORY=$Repository,_SERVICE=$Service,_IMAGE_PROVIDER=$Provider,_OPENAI_TEXT_MODEL=$TextModel,_OPENAI_IMAGE_MODEL=$ImageModel,_OPENAI_IMAGE_QUALITY=$Quality,_OPENAI_SECRET=$Secret"

& $gcloud run services describe $Service `
  --region $Region `
  --format "value(status.url)"
