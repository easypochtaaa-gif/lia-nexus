# LIA // DEPLOY TO VPS
# Usage: .\deploy_to_vps.ps1
# Prerequisites: SSH key configured for VPS, docker installed on VPS
#
# This script:
# 1. Creates a tar.gz of the sovereign_bot source
# 2. Uploads it to VPS via SCP
# 3. Rebuilds and restarts docker containers on VPS

param(
    [string]$VpsHost = "80.89.237.50",
    [string]$VpsUser = "root",
    [string]$VpsPath = "/root/lia",
    [string]$SshKey = "C:\Users\StabX\.ssh\lia_vps_key"
)

$ErrorActionPreference = "Stop"
Write-Host "👁 [LIA DEPLOY] Starting deployment to $VpsHost..." -ForegroundColor Cyan

# 1. Create tar.gz of source
Write-Host "[1/5] Packing sovereign_bot source..." -ForegroundColor Yellow
$tempTar = "$env:TEMP\lia_deploy.tar.gz"
$sourceDir = "$PSScriptRoot\sovereign_bot"

if (Test-Path $tempTar) { Remove-Item $tempTar -Force }

# List of files to include
$includeFiles = @(
    "main.py", "emotions.py", "memory.py", "chroma_memory.py",
    "media.py", "emotions_enhanced.py", "memory_enhanced.py",
    "memory_scheduler.py", "prompt_modifiers.py",
    "requirements.txt", "Dockerfile"
)

# Create temp dir with only needed files
$tempDir = "$env:TEMP\lia_pack"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Force $tempDir | Out-Null

foreach ($f in $includeFiles) {
    $src = Join-Path $sourceDir $f
    if (Test-Path $src) {
        Copy-Item $src $tempDir -Force
    }
}

# Also copy .env (exclude in .gitignore but needed for deploy)
$envFile = "$PSScriptRoot\.env"
if (Test-Path $envFile) {
    Copy-Item $envFile $tempDir -Force
}

# Tar + gzip
Push-Location $tempDir
try {
    & tar -czf $tempTar *
} finally {
    Pop-Location
    Remove-Item $tempDir -Recurse -Force
}
Write-Host "   OK: $((Get-Item $tempTar).Length / 1KB) KB packed" -ForegroundColor Green

# 2. Upload to VPS
Write-Host "[2/5] Uploading to VPS..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" "mkdir -p $VpsPath/sovereign_bot"
scp -i "$SshKey" -o StrictHostKeyChecking=no $tempTar "${VpsUser}@${VpsHost}:$VpsPath/lia_deploy.tar.gz"
Write-Host "   OK: Uploaded" -ForegroundColor Green

# 3. Extract on VPS
Write-Host "[3/5] Extracting on VPS..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
cd $VpsPath
tar -xzf lia_deploy.tar.gz -C sovereign_bot/
rm lia_deploy.tar.gz
echo "Files extracted:"
ls -la sovereign_bot/
"@
Write-Host "   OK: Extracted" -ForegroundColor Green

# 4. Copy docker-compose and .env
Write-Host "[4/5] Updating docker config..." -ForegroundColor Yellow
scp -i "$SshKey" -o StrictHostKeyChecking=no "$PSScriptRoot\docker-compose.yml" "${VpsUser}@${VpsHost}:$VpsPath/docker-compose.yml"
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" "cd $VpsPath && cp -f sovereign_bot/.env .env 2>/dev/null || true"
Write-Host "   OK: Config updated" -ForegroundColor Green

# 5. Rebuild and restart
Write-Host "[5/5] Rebuilding and restarting containers..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
cd $VpsPath
docker compose down --remove-orphans
docker compose build --no-cache lia-bot
docker compose up -d
echo ""
echo "=== Container Status ==="
docker compose ps
echo ""
echo "=== Recent Logs ==="
docker compose logs --tail=20 lia-bot
"@
Write-Host "   OK: Deploy complete!" -ForegroundColor Green

# Cleanup
Remove-Item $tempTar -Force

Write-Host ""
Write-Host "👁 [LIA DEPLOY] Deployed to https://dark-stab.space" -ForegroundColor Cyan
Write-Host "   Telegram: @stab_lia_bot" -ForegroundColor Cyan
Write-Host "   Web API:  http://$VpsHost`:8080" -ForegroundColor Cyan
