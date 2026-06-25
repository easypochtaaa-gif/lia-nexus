# LIA // FIX HTTPS for dark-stab.space
# Run this script on YOUR PC (not VPS) — it will SSH and fix everything
# Prerequisites: SSH access to root@80.89.237.50

param(
    [string]$VpsHost = "80.89.237.50",
    [string]$VpsUser = "root",
    [string]$Domain = "dark-stab.space",
    [string]$SshKey = "C:\Users\StabX\.ssh\lia_vps_key"
)

Write-Host "👁 [LIA HTTPS FIX] Diagnosing and fixing HTTPS for $Domain..." -ForegroundColor Cyan

# Step 1: Check what's running
Write-Host "`n[1/5] Checking current state on VPS..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
echo '=== Nginx Config ==='
cat /etc/nginx/sites-enabled/default 2>/dev/null || cat /etc/nginx/conf.d/*.conf 2>/dev/null || echo 'NO NGINX CONFIG FOUND'
echo ''
echo '=== Open Ports ==='
ss -tlnp | grep -E ':(80|443|8080|8081) ' 2>/dev/null || netstat -tlnp 2>/dev/null | grep -E ':(80|443|8080|8081) '
echo ''
echo '=== Firewall ==='
ufw status 2>/dev/null || iptables -L INPUT -n 2>/dev/null | head -20
echo ''
echo '=== Docker ==='
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'Docker not running or no containers'
"@

# Step 2: Open port 443
Write-Host "`n[2/5] Opening port 443 in firewall..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
ufw allow 443/tcp 2>/dev/null
ufw allow 80/tcp 2>/dev/null
ufw --force enable 2>/dev/null
iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null
iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null
echo 'Firewall rules updated'
"@

# Step 3: Install certbot
Write-Host "`n[3/5] Installing certbot..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
if ! command -v certbot &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq certbot python3-certbot-nginx 2>&1 | tail -3
fi
echo "Certbot: \$(which certbot)"
"@

# Step 4: Get SSL certificate
Write-Host "`n[4/5] Obtaining SSL certificate for $Domain..." -ForegroundColor Yellow
ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
certbot --nginx -d $Domain --non-interactive --agree-tos --email admin@${Domain} --redirect 2>&1
"@

# Step 5: Verify
Write-Host "`n[5/5] Verifying HTTPS..." -ForegroundColor Yellow
$result = Invoke-WebRequest -Uri "https://$Domain" -TimeoutSec 10 -ErrorAction SilentlyContinue
if ($result -and $result.StatusCode -eq 200) {
    Write-Host "   ✅ HTTPS работает! https://$Domain" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ HTTPS всё ещё не отвечает. Проверяем детали..." -ForegroundColor Yellow
    ssh -i "$SshKey" -o StrictHostKeyChecking=no "${VpsUser}@${VpsHost}" @"
echo '=== Nginx status ==='
systemctl status nginx --no-pager 2>&1 | head -10
echo ''
echo '=== Certbot status ==='
certbot certificates 2>&1
echo ''
echo '=== Port check ==='
ss -tlnp | grep -E ':(80|443) '
"@
}

Write-Host "`n👁 [LIA HTTPS FIX] Done!" -ForegroundColor Cyan
