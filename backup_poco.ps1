# LIA // POCO X3 NFC FULL BACKUP
# Copies entire phone internal storage to D:\POCCO
# Uses Shell COM for MTP access (phone has no drive letter)

$ErrorActionPreference = "Continue"
$PhoneName = "POCO X3 NFC"
$BackupRoot = "D:\POCCO"
$LogFile = "$BackupRoot\backup_log.txt"

# Create backup folder
New-Item -ItemType Directory -Force $BackupRoot | Out-Null
$startTime = Get-Date

"=== POCO X3 NFC BACKUP ===" | Out-File $LogFile
"Start: $startTime" | Out-File $LogFile -Append
"Backup: $BackupRoot" | Out-File $LogFile -Append
"----------------------------------------" | Out-File $LogFile -Append

Write-Host "👁 [POCO BACKUP] Starting full backup to $BackupRoot..." -ForegroundColor Cyan

# Get phone Shell object
$shell = New-Object -ComObject Shell.Application
$phone = $null
foreach ($item in $shell.NameSpace(0x11).Items()) {
    if ($item.Name -eq $PhoneName) {
        $phone = $item
        break
    }
}

if (-not $phone) {
    Write-Host "❌ Phone '$PhoneName' not found! Is it connected and unlocked?" -ForegroundColor Red
    exit 1
}

Write-Host "   Phone: $($phone.Name)" -ForegroundColor Green

# Get internal storage
$storage = $phone.GetFolder.Items() | Where-Object { $_.IsFolder -and $_.Name -match 'сховище|storage|Internal' }
if (-not $storage) {
    $storageItem = $phone.GetFolder
} else {
    $storageItem = $storage.GetFolder
}

Write-Host "   Storage: $($storageItem.Title)" -ForegroundColor Green

# Function: Recursive copy from MTP shell folder
$totalFiles = 0
$totalDirs = 0
$totalBytes = 0
$skipped = 0
$errors = @()

function Copy-ShellFolder {
    param(
        $ShellFolder,
        [string]$DestPath,
        [string]$RelativePath = "",
        [int]$Depth = 0
    )

    $script:totalDirs++
    $indent = "  " * [Math]::Min($Depth, 4)

    # Create destination folder
    if (-not (Test-Path $DestPath)) {
        New-Item -ItemType Directory -Force $DestPath | Out-Null
    }

    $items = @()
    try {
        $items = @($ShellFolder.Items())
    } catch {
        $script:errors += "$RelativePath : $_"
        return
    }

    $count = $items.Count
    $idx = 0

    foreach ($item in $items) {
        $idx++
        $itemName = $item.Name
        $itemDest = Join-Path $DestPath $itemName
        $itemRel = if ($RelativePath) { "$RelativePath\$itemName" } else { $itemName }

        # Progress indicator for large folders
        if ($Depth -le 2 -and $idx % 10 -eq 0) {
            $pct = if ($count -gt 0) { [math]::Round($idx/$count*100) } else { 0 }
            Write-Host "   ${indent}[$pct%] $itemRel" -NoNewline -ForegroundColor DarkGray
            Write-Host "`r" -NoNewline
        }

        if ($item.IsFolder) {
            # Recursive
            try {
                Copy-ShellFolder -ShellFolder $item.GetFolder -DestPath $itemDest -RelativePath $itemRel -Depth ($Depth + 1)
            } catch {
                $script:errors += "$itemRel (folder): $_"
                $script:skipped++
            }
        } else {
            # Copy file
            try {
                $fileSize = $item.Size
                # Skip if file exists with same size
                if (Test-Path $itemDest) {
                    $existing = (Get-Item $itemDest)
                    if ($existing.Length -eq $fileSize) {
                        $script:skipped++
                        continue
                    }
                }
                # Copy via Shell (MTP doesn't support direct file copy)
                $parentShell = (New-Object -ComObject Shell.Application).NameSpace((Get-Item $DestPath).FullName)
                if ($parentShell) {
                    $parentShell.CopyHere($item, 4 + 16)  # 4=no dialog, 16=yes to all
                }
                $script:totalFiles++
                $script:totalBytes += $fileSize
            } catch {
                $script:errors += "$itemRel : $_"
                $script:skipped++
            }
        }
    }
}

# Start backup
Write-Host ""
Write-Host "=== Copying files... (MTP is slow, be patient) ===" -ForegroundColor Yellow

$mainFolder = $storageItem
$folderCount = @($mainFolder.Items()).Count
Write-Host "   Root folders: $folderCount" -ForegroundColor Gray

$fidx = 0
foreach ($item in @($mainFolder.Items())) {
    $fidx++
    $itemName = $item.Name
    $itemDest = Join-Path $BackupRoot $itemName

    # Skip some system folders that fail on MTP
    if ($itemName -match '^(Android|\.|cache|\.thumbnails)$') {
        Write-Host "   [$fidx/$folderCount] SKIP: $itemName (system)" -ForegroundColor DarkGray
        "$itemName : SKIPPED (system folder)" | Out-File $LogFile -Append
        continue
    }

    Write-Host "   [$fidx/$folderCount] COPY: $itemName" -ForegroundColor White

    if ($item.IsFolder) {
        Copy-ShellFolder -ShellFolder $item.GetFolder -DestPath $itemDest -RelativePath $itemName -Depth 1
    } else {
        # Single file in root
        try {
            $parentShell = (New-Object -ComObject Shell.Application).NameSpace($BackupRoot)
            $parentShell.CopyHere($item, 4 + 16)
            $totalFiles++
            $totalBytes += $item.Size
        } catch {
            $errors += "$itemName : $_"
            $skipped++
        }
    }
}

$endTime = Get-Date
$duration = $endTime - $startTime

# Summary
$summary = @"

========================================
POCO X3 NFC BACKUP COMPLETE
========================================
Start:    $startTime
End:      $endTime
Duration: $($duration.ToString('hh\:mm\:ss'))
----------------------------------------
Folders:  $totalDirs
Files:    $totalFiles
Size:     $([math]::Round($totalBytes/1MB, 1)) MB
Skipped:  $skipped
Errors:   $($errors.Count)
========================================

"@

$summary | Out-File $LogFile -Append

if ($errors.Count -gt 0) {
    "`n=== ERRORS ===" | Out-File $LogFile -Append
    $errors | ForEach-Object { $_ } | Out-File $LogFile -Append
}

Write-Host ""
Write-Host "👁 [POCO BACKUP] Complete!" -ForegroundColor Cyan
Write-Host $summary

# Open the backup folder
explorer $BackupRoot
