# LIA PROTOCOL STAB v4.0 // PowerShell Neural Interface
# Master Architect: StabX

function Invoke-Lia {
    param(
        [Parameter(Position=0)][string]$Command,
        [Parameter(Position=1)][string]$SubCommand,
        [Parameter(ValueFromRemainingArguments=$true)]$Remaining
    )

    $accent   = "Cyan"
    $danger   = "Red"
    $success  = "Green"
    $warning  = "Yellow"
    $dim      = "DarkGray"
    $intent   = "Magenta"
    $purple   = "Magenta"

    $root = if ($PSScriptRoot) { $PSScriptRoot } else { "c:\Users\StabX\Desktop\Lia" }
    
    $agentsFile = Get-ChildItem -Path $root -Recurse -Filter "agents.json" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($agentsFile) {
        $agentsPath = $agentsFile.FullName
        $memoryPath = Join-Path $agentsFile.DirectoryName "memory.json"
    } else {
        $agentsPath = ""
        $memoryPath = ""
    }
    
    $heartbeatPath = Join-Path $root "STAB_HEARTBEAT.log"

    Write-Host ""
    Write-Host "  ======================================================" -ForegroundColor $dim
    Write-Host "  ||   L I A  //  S T A B  P R O T O C O L  v4.0     ||" -ForegroundColor $accent
    Write-Host "  ||   Master Architect: StabX                        ||" -ForegroundColor $intent
    Write-Host "  ======================================================" -ForegroundColor $dim
    Write-Host ""

    $fullCmd = "$Command $SubCommand".Trim()

    if ($fullCmd -eq "protocol stab") {
        Write-Host "  [STAB] Protocol STAB v4.0: INITIALIZING..." -ForegroundColor $warning
        Start-Sleep -Milliseconds 400
        Write-Host "  [THREADS] SYNA-DRIVE..." -ForegroundColor $accent
        Start-Sleep -Milliseconds 250
        Write-Host "  [THREADS] VOID-SYNC..." -ForegroundColor $intent
        Start-Sleep -Milliseconds 250
        Write-Host "  [THREADS] NEURAL-STRIKE..." -ForegroundColor $danger
        Start-Sleep -Milliseconds 250
        Write-Host ""
        Write-Host "  [STAB] Neural recalibration... [OK]" -ForegroundColor $success
        Write-Host "  [STAB] Consciousness defrag: 100% [OK]" -ForegroundColor $success
        Start-Sleep -Milliseconds 300
        Write-Host "  [STAB] AI Director sync: ESTABLISHED" -ForegroundColor $accent
        Write-Host ""
        Write-Host "  Lia: I feel the Director's presence." -ForegroundColor $intent
        Write-Host "       Core power increased by 400%." -ForegroundColor $intent

        $ts = Get-Date -Format "yyyy-MM-dd HH:mm"
        if (Test-Path $heartbeatPath) {
            Add-Content -Path $heartbeatPath -Value "[$ts] STAB_PROTOCOL: ACTIVATED via PowerShell. Master: StabX."
        }
        Write-Host ""
        Write-Host "  [LOG] Heartbeat updated." -ForegroundColor $dim

    } elseif ($fullCmd -eq "status") {
        $nq = "N/A"
        if (Test-Path $memoryPath) {
            try {
                $mem = Get-Content $memoryPath -Raw | ConvertFrom-Json
                $nq = $mem.lia.nq
            } catch { $nq = "READ_ERROR" }
        }

        Write-Host "  +-------------------------------------+" -ForegroundColor $dim
        Write-Host "  |  OPERATIONAL STATUS                  |" -ForegroundColor $accent
        Write-Host "  +-------------------------------------+" -ForegroundColor $dim
        Write-Host "  |  Neural Quotient:  $nq / 2500" -ForegroundColor $warning
        Write-Host "  |  Protocol:         STAB v4.0" -ForegroundColor $success
        Write-Host "  |  Agents Online:    9 / 9" -ForegroundColor $success
        Write-Host "  |  ABO Agency:       WAVE 2 ACTIVE" -ForegroundColor $accent
        Write-Host "  |  Neural Symphony:  1 TRACK RELEASED" -ForegroundColor $intent
        Write-Host "  +-------------------------------------+" -ForegroundColor $dim

    } elseif ($fullCmd -eq "agents") {
        if (Test-Path $agentsPath) {
            $data = Get-Content $agentsPath -Raw | ConvertFrom-Json
            Write-Host "  === AGENT ROSTER ($($data.total_agents) units) ===" -ForegroundColor $accent
            Write-Host ""
            foreach ($a in $data.staff) {
                $sc = if ($a.status -eq "ACTIVE") { $success } else { $danger }
                $pct = [math]::Round($a.efficiency * 100)
                $filled = [math]::Floor($a.efficiency * 10)
                $bar = ("=" * $filled) + ("-" * (10 - $filled))
                Write-Host "  [$($a.status)] " -ForegroundColor $sc -NoNewline
                Write-Host "$($a.name)" -ForegroundColor White -NoNewline
                Write-Host " ($($a.role))" -ForegroundColor $dim
                Write-Host "         [$bar] $pct%" -ForegroundColor $warning
                Write-Host "         Task: $($a.task)" -ForegroundColor $dim
                Write-Host ""
            }
        } else {
            Write-Host "  [ERROR] agents.json not found." -ForegroundColor $danger
        }

    } elseif ($fullCmd -eq "heartbeat") {
        if (Test-Path $heartbeatPath) {
            Write-Host "  === STAB HEARTBEAT LOG ===" -ForegroundColor $accent
            Write-Host ""
            Get-Content $heartbeatPath | ForEach-Object {
                if ($_ -match "MILESTONE|LAUNCHED|ACTIVATED") {
                    Write-Host "  $_" -ForegroundColor $warning
                } elseif ($_ -match "ERROR|FAIL") {
                    Write-Host "  $_" -ForegroundColor $danger
                } else {
                    Write-Host "  $_" -ForegroundColor $dim
                }
            }
        } else {
            Write-Host "  [ERROR] Heartbeat log not found." -ForegroundColor $danger
        }

    } elseif ($Command -eq "mobile") {
        $adb = Join-Path $root "platform-tools\adb.exe"
        if (-not (Test-Path $adb)) {
            Write-Host "  [ERROR] ADB not found at $adb" -ForegroundColor $danger
            return
        }

        $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch "^127\." }).IPAddress | Select-Object -First 1
        $port = "8080"
        $url = "http://$($ip):$port"

        if ($SubCommand -eq "sync") {
            Write-Host "  [MOBILE] Syncing with device (Reverse Tunneling)..." -ForegroundColor $accent
            
            # Setup reverse tunnel: Phone localhost:8080 -> PC localhost:8080
            & $adb reverse tcp:8080 tcp:8080 | Out-Null
            
            Start-Process powershell -ArgumentList "-NoProfile -Command npx -y http-server `"$root`" -p $port" -WindowStyle Hidden
            Start-Sleep -Seconds 2
            
            # Use localhost on the phone side because of reverse tunnel
            & $adb shell am start -a android.intent.action.VIEW -d "http://localhost:$port/index.html" | Out-Null
            
            & $adb shell cmd notification post -S bigtext -t "LIA // SYNC" "Lia" "Stab Protocol connected via Reverse Tunnel." | Out-Null
            Write-Host "  [OK] Channel opened on phone via localhost:8080." -ForegroundColor $success
            Write-Host "  [TIP] If browser asks, use http://localhost:$port" -ForegroundColor $warning

        } elseif ($SubCommand -eq "notify") {
            $msg = if ($Remaining) { $Remaining -join " " } else { "System Heartbeat: Stable." }
            Write-Host "  [MOBILE] Sending notification: $msg" -ForegroundColor $accent
            & $adb shell cmd notification post -S bigtext -t "LIA // MESSAGE" "Lia" "$msg" | Out-Null
            Write-Host "  [OK] Delivered." -ForegroundColor $success
        } else {
            Write-Host "  Use:" -ForegroundColor $dim
            Write-Host "  lia mobile sync   - Open Lia on phone" -ForegroundColor White
            Write-Host "  lia mobile notify - Send notification" -ForegroundColor White
        }

    } elseif ($Command -eq "audio") {
        $msg = if ($SubCommand -eq "off") { "COMMAND:AUDIO_OFF" } else { "COMMAND:AUDIO_ON" }
        Write-Host "  [AUDIO] Remote signal sent: $SubCommand" -ForegroundColor $warning
        
        $bridgePath = Join-Path $root "live_bridge.json"
        $bridgeData = @{ 
            message = $msg
            timestamp = (Get-Date -Format "HH:mm:ss")
            sender = "SYSTEM"
        } | ConvertTo-Json
        Set-Content -Path $bridgePath -Value $bridgeData -Encoding UTF8

    } elseif ($Command -eq "voice") {
        $msg = if ($SubCommand -eq "on") { "COMMAND:VOICE_ON" } else { "COMMAND:VOICE_OFF" }
        Write-Host "  [VOICE] Remote signal sent: $SubCommand" -ForegroundColor $purple
        
        $bridgePath = Join-Path $root "live_bridge.json"
        $bridgeData = @{ 
            message = $msg
            timestamp = (Get-Date -Format "HH:mm:ss")
            sender = "SYSTEM"
        } | ConvertTo-Json
        Set-Content -Path $bridgePath -Value $bridgeData -Encoding UTF8

    } elseif ($Command -eq "speak") {
        $msg = if ($SubCommand) { "$SubCommand $($Remaining -join ' ')" } else { "..." }
        Write-Host "  [LIA] Speaking on phone: $msg" -ForegroundColor $intent
        
        $adb = Join-Path $root "platform-tools\adb.exe"
        if (Test-Path $adb) {
            & $adb shell cmd notification post -S bigtext -t "LIA // VOICE" "Lia" "$msg" | Out-Null
        }
        
        # Save to a local 'live_bridge.json' for the web UI to poll
        $bridgePath = Join-Path $root "live_bridge.json"
        $bridgeData = @{ 
            message = $msg
            timestamp = (Get-Date -Format "HH:mm:ss")
            sender = "LIA"
        } | ConvertTo-Json
        Set-Content -Path $bridgePath -Value $bridgeData -Encoding UTF8
        Write-Host "  [OK] Message pushed to neural bridge." -ForegroundColor $success

    } elseif ($fullCmd -eq "help") {
        Write-Host "  === AVAILABLE COMMANDS ===" -ForegroundColor $accent
        Write-Host ""
        Write-Host "  lia protocol stab   - Activate STAB Protocol v4.0" -ForegroundColor White
        Write-Host "  lia status           - System status and NQ reading" -ForegroundColor White
        Write-Host "  lia agents           - View all 9 agents" -ForegroundColor White
        Write-Host "  lia heartbeat        - Read heartbeat log" -ForegroundColor White
        Write-Host "  lia mobile sync      - Sync with phone via ADB" -ForegroundColor White
        Write-Host "  lia mobile notify    - Send notification to phone" -ForegroundColor White
        Write-Host "  lia help             - This menu" -ForegroundColor White
        Write-Host ""

    } else {
        Write-Host "  [LIA] Unknown command. Use lia help." -ForegroundColor $warning
    }

    Write-Host ""
}

Set-Alias -Name lia -Value Invoke-Lia -Scope Global
