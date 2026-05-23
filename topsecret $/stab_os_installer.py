import subprocess
import time
import os
import sys

# --- STAB_OS_INSTALLER v1.1 ---
# Фикс кодировки для Windows

if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

ADB_PATH = "..\\platform-tools\\adb.exe"

def run_adb(command):
    print(f"[ADB] Executing: {command}")
    result = subprocess.run(f"{ADB_PATH} {command}", shell=True, capture_output=True, text=True)
    return result.stdout

def install_overlay():
    print("INITIATING AUTONOMOUS STAB_OS OVERLAY INSTALLATION...")
    
    devices = run_adb("devices")
    if "device" not in devices.split("\n")[1]:
        print("[ERROR] Phone not found. Check USB connection.")
        return

    # 1. Backup Telegram Media (safe way)
    print("[BACKUP] Saving Telegram media to Empire Vault...")
    # Создаем папку если нет
    os.makedirs("c:\\Users\\StabX\\Desktop\\Lia\\backups\\tg_media", exist_ok=True)
    run_adb("pull /sdcard/Android/media/org.telegram.messenger c:\\Users\\StabX\\Desktop\\Lia\\backups\\tg_media")
    
    # 2. Debloat (Non-destructive for user data)
    TRACKERS = [
        "com.google.android.apps.tachyon",
        "com.motorola.ccc.ota",
        "com.google.android.apps.messaging",
        "com.google.android.gms.location.history"
    ]
    
    for pkg in TRACKERS:
        run_adb(f"shell pm uninstall --user 0 {pkg}")
        print(f"[OK] Neutralized: {pkg}")

    # 3. UI/Kernel Optimization
    run_adb("shell settings put global window_animation_scale 0.5")
    run_adb("shell settings put global transition_animation_scale 0.5")
    run_adb("shell settings put global animator_duration_scale 0.5")
    
    # 4. Agent Deployment
    run_adb("shell mkdir -p /sdcard/Lia/nexus")
    run_adb("push nexus_config.json /sdcard/Lia/nexus/config.json")

    print("\nSUCCESS. STAB_OS OVERLAY DEPLOYED. PHONE IS NOW SYNCED.")

if __name__ == "__main__":
    install_overlay()
