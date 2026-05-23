# run_stab.ps1 -- STAB SYSTEM v2 Daily Launcher (Windows PowerShell)
# Displays daily goals, checks tracking CSV, and starts the Telegram logger.

$ErrorActionPreference = "Continue"
$STAB_DIR = "c:\Users\StabX\Desktop\Lia\topsecret $"
$CSV_FILE = Join-Path $STAB_DIR "STAB_TRACKING.csv"
$LOGGER   = Join-Path $STAB_DIR "telegram_logger.py"
$TODAY    = Get-Date -Format "yyyy-MM-dd"

# ----------------------------------------------------------------
# 1. DAILY REMINDER
# ----------------------------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   STAB SYSTEM v2 -- DAILY CHECK  [$TODAY]" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  TARGET:  40 000 UAH / 14 days  (~2 857 UAH per day)" -ForegroundColor White
Write-Host "  MODEL:   AI-content (posts)  |  10 posts / 24h" -ForegroundColor White
Write-Host ""
Write-Host "  TODAY'S TASKS:" -ForegroundColor Green
Write-Host "    [1] Send 50-100 outreach messages" -ForegroundColor White
Write-Host "    [2] Process replies and close deals" -ForegroundColor White
Write-Host "    [3] Deliver orders to clients" -ForegroundColor White
Write-Host "    [4] Post 1-2 items to NEON FLOW channel" -ForegroundColor White
Write-Host ""
Write-Host "  DECISION RULES:" -ForegroundColor Red
Write-Host "    - 2 days with 0 clients -> change the offer" -ForegroundColor White
Write-Host "    - <50 messages sent     -> the problem is YOU" -ForegroundColor White
Write-Host "    - many replies, few sales -> weak script" -ForegroundColor White
Write-Host "    - few replies           -> bad opening message" -ForegroundColor White
Write-Host ""

# ----------------------------------------------------------------
# 2. CHECK YESTERDAY'S STATS (from CSV)
# ----------------------------------------------------------------
if (Test-Path $CSV_FILE) {
    $lines = Get-Content $CSV_FILE | Select-Object -Skip 1 | Where-Object { $_.Trim() -ne "" }
    if ($lines.Count -gt 0) {
        $last = ($lines | Select-Object -Last 1) -split ","
        $lastDate = $last[0]
        $lastMsgs = $last[1]
        $lastReplies = $last[2]
        $lastClients = $last[3]
        $lastRevenue = $last[4]

        Write-Host "  LAST RECORDED DAY: $lastDate" -ForegroundColor Magenta
        Write-Host "    Messages: $lastMsgs  |  Replies: $lastReplies  |  Clients: $lastClients  |  Revenue: $lastRevenue UAH" -ForegroundColor White

        # Calculate cumulative revenue
        $totalRevenue = 0
        foreach ($line in $lines) {
            $parts = $line -split ","
            if ($parts.Count -ge 5) {
                $totalRevenue += [double]$parts[4]
            }
        }
        $remaining = 40000 - $totalRevenue
        Write-Host "    TOTAL REVENUE: $totalRevenue UAH  |  REMAINING: $remaining UAH" -ForegroundColor Yellow
        Write-Host ""

        # Warnings
        if ([int]$lastMsgs -lt 50) {
            Write-Host "  [!] WARNING: Yesterday you sent less than 50 messages!" -ForegroundColor Red
        }
    } else {
        Write-Host "  No data in tracking CSV yet. Start working!" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Tracking CSV not found. The logger will create it." -ForegroundColor Yellow
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------
# 3. START TELEGRAM LOGGER IN BACKGROUND
# ----------------------------------------------------------------
if (Test-Path $LOGGER) {
    Write-Host "Starting Telegram logger..." -ForegroundColor Green
    $logFile = Join-Path $STAB_DIR "telegram_logger.log"
    Start-Process -FilePath "python" -ArgumentList "`"$LOGGER`"" -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError (Join-Path $STAB_DIR "telegram_logger_err.log")
    Write-Host "Telegram logger launched in background. Logs: $logFile" -ForegroundColor Green
} else {
    Write-Host "[!] telegram_logger.py not found at $LOGGER" -ForegroundColor Red
}

Write-Host ""
Write-Host "Go make money. Action > Analysis. Speed > Perfection." -ForegroundColor Yellow
Write-Host ""
