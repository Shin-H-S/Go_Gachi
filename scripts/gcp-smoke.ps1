param(
  [Parameter(Mandatory = $true)]
  [string]$Url
)

$ErrorActionPreference = "Stop"
uv run python scripts/gcp_smoke.py $Url
