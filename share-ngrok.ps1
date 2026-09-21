# Share Fahem at a fixed ngrok address, with Google sign-in.
# See docker/docker-compose.ngrok.yml for the .env entries it needs.
#
#   powershell -ExecutionPolicy Bypass -File share-ngrok.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$envText = if (Test-Path env/.env) { Get-Content env/.env -Raw } else { "" }
$missing = @("NGROK_AUTHTOKEN", "NGROK_DOMAIN", "GOOGLE_CLIENT_ID") |
    Where-Object { $envText -notmatch "(?m)^\s*$_\s*=\s*\S+" }
if ($missing) {
    Write-Host "Missing in env/.env: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "See the header of docker/docker-compose.ngrok.yml."
    exit 1
}
$domain = ([regex]::Match($envText, "(?m)^\s*NGROK_DOMAIN\s*=\s*(\S+)").Groups[1].Value) -replace "^https?://", "" -replace "/$", ""
$url = "https://$domain"

# Only one share mode at a time: the Cloudflare quick tunnel goes away.
# (Windows PowerShell turns docker's stderr progress into a terminating error
# under "Stop" once redirected, so relax it for this one best-effort call.)
$ErrorActionPreference = "Continue"
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.share.yml stop tunnel *> $null
$ErrorActionPreference = "Stop"

Write-Host "1/2  Building and starting Fahem at $url ..."
docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.ngrok.yml up -d --build --remove-orphans
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

Write-Host "2/2  Waiting for $url/api/health ..."
$healthy = $false
$deadline = (Get-Date).AddSeconds(240)
while (-not $healthy -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    try {
        # Skips ngrok's free-plan "you are about to visit" page for this check.
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Headers @{ "ngrok-skip-browser-warning" = "1" } "$url/api/health"
        $healthy = $r.StatusCode -eq 200
    } catch { }
}

Write-Host ""
if ($healthy) {
    Write-Host "Fahem is online: $url" -ForegroundColor Green
} else {
    Write-Host "Not answering yet at $url - check: docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.ngrok.yml logs ngrok" -ForegroundColor Yellow
}
Write-Host "Google sign-in needs $url in Google Cloud Console > Credentials > your OAuth client > Authorised JavaScript origins."
Write-Host "Stop sharing:  docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.ngrok.yml stop ngrok"
