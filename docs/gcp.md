# GCP Operation

이 문서는 Go_Gachi를 Cloud Run에 올려 운영하거나 배포 검증할 때 필요한 절차를 정리합니다. 로컬 검증과 별개로, 운영 값은 GCP 환경변수와 Secret Manager에서 관리합니다.

## One-time Setup

```powershell
gcloud.cmd auth login
gcloud.cmd config set project YOUR_PROJECT_ID

gcloud.cmd services enable `
  run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  secretmanager.googleapis.com

gcloud.cmd artifacts repositories create cafe-ad-maker `
  --repository-format=docker `
  --location=asia-northeast3 `
  --description="Cafe Ad Maker containers"
```

OpenAI API 키는 Secret Manager에 저장합니다.

```powershell
Set-Content -Path .openai-key.tmp -Value "YOUR_OPENAI_API_KEY" -NoNewline
gcloud.cmd secrets create OPENAI_API_KEY --data-file=.openai-key.tmp
Remove-Item .openai-key.tmp
```

이미 Secret이 있다면 새 버전을 추가합니다.

```powershell
Set-Content -Path .openai-key.tmp -Value "YOUR_OPENAI_API_KEY" -NoNewline
gcloud.cmd secrets versions add OPENAI_API_KEY --data-file=.openai-key.tmp
Remove-Item .openai-key.tmp
```

Cloud Run 런타임 서비스 계정에 Secret 접근 권한이 필요합니다. 기본 Compute 서비스 계정을 쓰는 경우 프로젝트 번호를 확인한 뒤 아래처럼 부여합니다.

```powershell
$PROJECT_ID="YOUR_PROJECT_ID"
$PROJECT_NUMBER=$(gcloud.cmd projects describe $PROJECT_ID --format="value(projectNumber)")

gcloud.cmd secrets add-iam-policy-binding OPENAI_API_KEY `
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

## Deploy

```powershell
.\scripts\gcp-deploy.ps1 -ProjectId YOUR_PROJECT_ID
```

스크립트는 `cloudbuild.yaml`을 사용해서 이미지를 빌드하고, Artifact Registry에 푸시한 뒤 Cloud Run에 배포합니다. 마지막 줄에 서비스 URL을 출력합니다.

## Smoke Test

배포 후 출력된 Cloud Run URL로 스모크 테스트를 실행합니다.

```powershell
.\scripts\gcp-smoke.ps1 -Url https://YOUR_SERVICE_URL
```

확인 항목:

- `/api/health`
- `/api/ready`
- `/api/config`

## Runtime Settings

Cloud Run 배포 기본값:

- Python `3.11.14`
- `APP_ENV=production`
- `IMAGE_PROVIDER=openai`
- `OPENAI_TEXT_MODEL=gpt-5.4-mini`
- `OPENAI_IMAGE_MODEL=gpt-image-2`
- `OPENAI_IMAGE_QUALITY=medium`
- `OPENAI_API_KEY`는 Secret Manager에서 주입

## Rollback

Cloud Run 콘솔에서 이전 revision으로 트래픽을 되돌리거나, CLI로 revision 목록을 확인한 뒤 트래픽을 옮깁니다.

```powershell
gcloud.cmd run revisions list --service cafe-ad-maker-v1 --region asia-northeast3
```
