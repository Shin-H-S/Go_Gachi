import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def fetch_json(url: str) -> dict:
    with urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


base_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
if not base_url:
    raise SystemExit("Usage: uv run python scripts/gcp_smoke.py https://service-url")

try:
    health = fetch_json(f"{base_url}/api/health")
    ready = fetch_json(f"{base_url}/api/ready")
    config = fetch_json(f"{base_url}/api/config")
except (HTTPError, URLError, TimeoutError) as exc:
    raise SystemExit(f"GCP smoke test failed: {exc}") from exc

if health.get("status") != "ok":
    raise SystemExit(f"Unexpected health response: {health}")

if ready.get("status") != "ready":
    raise SystemExit(f"Unexpected ready response: {ready}")

if not config.get("presets"):
    raise SystemExit("Config response has no presets")

print(
    json.dumps(
        {
            "health": health["status"],
            "ready": ready["status"],
            "provider": config.get("provider"),
            "presets": len(config.get("presets", [])),
        },
        ensure_ascii=False,
    )
)
