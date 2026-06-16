"""실제 /api/generate 호출 후 응답·DB 변화를 한 번에 확인하는 검증 스크립트.

사용:
  uv run python scripts/test_generate.py backend/uploads/<파일명>.jpg
  uv run python scripts/test_generate.py backend/uploads/<파일명>.jpg https://YOUR_BACKEND_URL

같은 이미지와 요청으로 한 번 더 실행하면 두 번째는 캐시 hit 여부를 확인할 수 있다.
"""

import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8000/api/generate"
DEFAULT_USER_PROMPT = "따뜻하고 깔끔한 카페 광고 이미지로 만들어줘"
DEFAULT_USER_COPY = "오늘 아메리카노 2,500원"

if len(sys.argv) < 2:
    print("사용: uv run python scripts/test_generate.py <이미지경로> [백엔드URL]")
    raise SystemExit(1)

image_path = Path(sys.argv[1])
if not image_path.exists():
    print(f"[!] 파일을 찾을 수 없음: {image_path}")
    raise SystemExit(1)

# mime은 확장자로 단순 결정. OpenAI는 png/jpg/webp만 받음.
ext = image_path.suffix.lower().lstrip(".")
mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
    ext
)
if mime is None:
    print(f"[!] 지원하지 않는 확장자: {ext}")
    raise SystemExit(1)

encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
data_url = f"data:{mime};base64,{encoded}"
api_url = (
    f"{sys.argv[2].rstrip('/')}/api/generate"
    if len(sys.argv) >= 3
    else API_URL
)

body = json.dumps(
    {
        "imageDataUrl": data_url,
        "presetId": "instagram",
        "detailType": "story_image",
        "userPrompt": DEFAULT_USER_PROMPT,
        "userCopy": DEFAULT_USER_COPY,
        "copyMode": "polish",
        "adCopyEnabled": True,
        "targetWidth": 1080,
        "targetHeight": 1920,
        "resizeMode": "cover",
    }
).encode("utf-8")

req = urllib.request.Request(
    api_url,
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print(f"[*] POST {api_url} (이미지: {image_path.name}, {len(encoded):,} chars base64)")
started = time.time()
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        elapsed = time.time() - started
        payload = json.loads(resp.read().decode("utf-8"))
        status = resp.status
except urllib.error.HTTPError as exc:
    error_body = exc.read().decode("utf-8", errors="replace")
    raise SystemExit(f"[!] HTTP {exc.code}: {error_body}") from exc

print(f"[+] {status} {elapsed:.1f}s 소요")
print("  provider:", payload.get("provider"))
print("  note    :", payload.get("note"))
print("  preset  :", (payload.get("preset") or {}).get("id"))
print("  imageUrl:", payload.get("imageUrl"))
print("  copy    :", payload.get("copy"))
print("  prompt  :", (payload.get("prompt") or "")[:80], "...")
image_data_url = payload.get("imageDataUrl") or ""
if image_data_url:
    print("  fallback imageDataUrl:", image_data_url[:60], f"... ({len(image_data_url):,} chars)")
