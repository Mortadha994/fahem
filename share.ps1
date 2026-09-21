# Share Fahem with friends through a free Cloudflare quick tunnel.
# See docker/docker-compose.share.yml for what this changes and why.
#
#   powershell -ExecutionPolicy Bypass -File share.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
# --project-directory . because the compose files moved into docker/, and
# Compose would otherwise resolve the bind mounts (and look for .env) there
# rather than at the repository root. Set-Location above makes "." the root.
$compose = @(
    "compose",
    "--env-file", "env/.env",
    "--project-directory", ".",
    "-f", "docker/docker-compose.yml",
    "-f", "docker/docker-compose.share.yml"
)

Write-Host "1/3  Building and starting Fahem in share mode..."
docker @compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

Write-Host "2/3  Waiting for the public link..."
$url = $null
$deadline = (Get-Date).AddSeconds(90)
while (-not $url -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 3
    $logs = (docker @compose logs tunnel) | Out-String
    $found = [regex]::Matches($logs, "https://[a-z0-9-]+\.trycloudflare\.com")
    if ($found.Count -gt 0) { $url = $found[$found.Count - 1].Value }
}
if (-not $url) { throw "No tunnel link after 90s - check: docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.share.yml logs tunnel" }

Write-Host "3/3  Telling the backend its public address (for e-mail links)..."
$env:FAHEM_PUBLIC_URL = $url
docker @compose up -d backend
if ($LASTEXITCODE -ne 0) { throw "restarting the backend failed" }

$healthy = $false
$deadline = (Get-Date).AddSeconds(180)
while (-not $healthy -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "$url/api/health"
        $healthy = $r.StatusCode -eq 200
    } catch { }
}

Write-Host ""
if ($healthy) {
    Write-Host "Fahem is online: $url" -ForegroundColor Green
} else {
    Write-Host "Link: $url  (the backend is still starting - try it in a minute)" -ForegroundColor Yellow
}
Write-Host "Send this link to your friends. It works while this PC and Docker are on,"
Write-Host "and changes if the tunnel restarts."
Write-Host "Stop sharing:  docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml -f docker/docker-compose.share.yml stop tunnel"
