"""실제 /api/generate 호출 후 응답·DB 변화를 한 번에 확인하는 검증 스크립트.

사용:
  uv run python scripts/test_generate.py backend/uploads/<파일명>.jpg
  (옵션) 같은 명령을 한 번 더 실행 → 두 번째는 캐시 hit이어야 함
"""

import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8000/api/generate"

if len(sys.argv) < 2:
    print("사용: uv run python scripts/test_generate.py <이미지경로>")
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

body = json.dumps(
    {
        "imageDataUrl": data_url,
        "presetId": None,  # 기본 프리셋 사용
        "feedback": "더 따뜻하고 카페 광고 느낌으로",
    }
).encode("utf-8")

req = urllib.request.Request(
    API_URL,
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

print(f"[*] POST {API_URL} (이미지: {image_path.name}, {len(encoded):,} chars base64)")
started = time.time()
with urllib.request.urlopen(req, timeout=180) as resp:
    elapsed = time.time() - started
    payload = json.loads(resp.read().decode("utf-8"))

print(f"[+] {resp.status} {elapsed:.1f}s 소요")
# imageDataUrl은 너무 길어서 앞 60자만, 응답 길이도 같이 보여준다.
preview = payload.get("imageDataUrl", "")[:60]
print("  provider:", payload.get("provider"))
print("  note    :", payload.get("note"))
print("  preset  :", (payload.get("preset") or {}).get("id"))
print("  prompt  :", (payload.get("prompt") or "")[:80], "...")
print("  result  :", preview, f"... ({len(payload.get('imageDataUrl', '')):,} chars)")
