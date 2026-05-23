import os, psutil, hashlib, requests, time, threading, math
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

# --- LIA_AEGIS_SENTINEL v3.0 // STAB_PROTOCOL ---
# Глубокий аудит, мониторинг в реальном времени и интеграция с облачным ядром.

VT_API_KEY = "ВСТАВЬ_API_KEY_ЗДЕСЬ" # Или подтянем из конфига
LOG_FILE = "aegis_sentinel.log"

def log_event(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

# --- 1. КРИМИНОЛОГИЧЕСКИЙ АНАЛИЗ (Heuristics) ---
def get_entropy(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read(1024 * 1024)
            if not data: return 0
            entropy = 0
            for x in range(256):
                p_x = float(data.count(x)) / len(data)
                if p_x > 0: entropy += - p_x * math.log(p_x, 2)
            return entropy
    except: return 0

def classify_file(filepath):
    score = 0
    filename = os.path.basename(filepath).lower()
    ext = os.path.splitext(filename)[1]
    
    if "temp" in filepath.lower() or "appdata" in filepath.lower(): score += 2
    if ext in {'.exe', '.dll', '.vbs', '.ps1', '.bat'}: score += 3
    if filename.count('.') > 1: score += 4
    
    size = os.path.getsize(filepath)
    if ext == ".exe" and size < 100000: score += 3
    if ext in {'.exe', '.dll'} and get_entropy(filepath) > 7.5: score += 5

    if score >= 8: return "🚨 CRITICAL"
    elif score >= 5: return "⚠️ DANGER"
    elif score >= 2: return "❓ SUSPICIOUS"
    return "🟢 NORMAL"

# --- 2. ОБЛАЧНАЯ ПРОВЕРКА (VirusTotal) ---
def check_virustotal(file_path):
    if VT_API_KEY == "ВСТАВЬ_API_KEY_ЗДЕСЬ": return "NO_API_KEY"
    try:
        sha256_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
        headers = {"x-apikey": VT_API_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            stats = data['data']['attributes']['last_analysis_stats']
            return f"VT_RESULT: {stats['malicious']} detections"
        return "VT_NOT_FOUND"
    except Exception as e:
        return f"VT_ERROR: {e}"

# --- 3. АНАЛИЗ ПРОЦЕССОВ И АВТОЗАГРУЗКИ ---
def analyze_system():
    log_event("Запуск системного анализа...", "SYSTEM")
    
    # Процессы
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
        try:
            exe = proc.info['exe']
            if exe and ("AppData" in exe or "Temp" in exe):
                log_event(f"Подозрительный процесс: {proc.info['name']} (PID: {proc.info['pid']}) -> {exe}", "WARNING")
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue

    # Автозагрузка
    startup_folders = [
        os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup"),
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    ]
    for folder in startup_folders:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                log_event(f"Автозагрузка: {f} в {folder}", "STARTUP")

# --- 4. ЖИВОЙ МОНИТОРИНГ (Watchdog) ---
class AegisWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            category = classify_file(event.src_path)
            log_event(f"НОВЫЙ ФАЙЛ: {event.src_path} | Статус: {category}", "AEGIS")
            if category in ["🚨 CRITICAL", "⚠️ DANGER"]:
                log_event(f"ВНИМАНИЕ: Обнаружен потенциальный вектор атаки!", "CRITICAL")
                vt = check_virustotal(event.src_path)
                if vt != "NO_API_KEY": log_event(f"Облачный вердикт: {vt}", "VT")

def start_monitoring(path):
    event_handler = AegisWatcher()
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    observer.start()
    log_event(f"Мониторинг Aegis запущен в секторе: {path}", "SYSTEM")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    target = input("Введите путь для защиты (Enter для текущей папки): ") or "."
    
    analyze_system()
    
    # Фоновый скан существующих файлов
    log_event("Начинаю фоновое сканирование существующих файлов...", "SCAN")
    for root, _, files in os.walk(target):
        for f in files:
            path = os.path.join(root, f)
            cat = classify_file(path)
            if cat != "🟢 NORMAL":
                log_event(f"Обнаружен старый узел: {path} | Статус: {cat}", "SCAN")

    # Запуск живого мониторинга
    start_monitoring(target)
