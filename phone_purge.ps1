# 💀 STAB IMPERIAL PURGE SCRIPT
$adb = "c:\Users\StabX\Desktop\Lia\tools\platform-tools\adb.exe"

$targets = @(
    "com.locode.manssex",
    "com.recovermessages.recoverdeletedmessages.datarecovery",
    "com.slots777.app.prod",
    "com.vegas.app.prod",
    "org.oxygine.player_championcasino_net",
    "audio.sound.effect.bass.virtrualizer.equalizer.eq.soundbooster",
    "com.volumebooster.soundbooster.louder",
    "com.jazibkhan.equalizer",
    "hub.browser.video.downloader.saver",
    "com.comhub.onlinechat.android.video"
)

Write-Host "--- STARTING THE PURGE ---" -ForegroundColor Red

foreach ($pkg in $targets) {
    Write-Host ">> Uninstalling: $pkg" -ForegroundColor Yellow
    & $adb shell pm uninstall --user 0 $pkg
}

Write-Host "`n--- FINAL OPTIMIZATION ---" -ForegroundColor Cyan
Write-Host ">> Forcing animation scales..."
& $adb shell settings put global window_animation_scale 0.5
& $adb shell settings put global transition_animation_scale 0.5
& $adb shell settings put global animator_duration_scale 0.5

Write-Host ">> Clearing system-wide cache..."
& $adb shell pm trim-caches 999G

Write-Host "`n--- PURGE COMPLETE. REBOOT RECOMMENDED. ---" -ForegroundColor Green
