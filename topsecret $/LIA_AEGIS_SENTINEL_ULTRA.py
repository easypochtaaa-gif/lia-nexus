import os, psutil, hashlib, requests, time, threading, math, shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from colorama import Fore, Style, init

# --- LIA_AEGIS_SENTINEL_ULTRA v5.0 // SOVEREIGN_SHIELD ---
# Полная интеграция: Автоматический Диагноз, Карантин, Лечение и Уничтожение угроз.

init(autoreset=True)

VT_API_KEY = "ВСТАВЬ_API"
LOG_FILE = "aegis_ultra.log"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
QUARANTINE_DIR = os.path.join(PROJECT_ROOT, "topsecret $", "quarantine")

# Список критически важных системных файлов для автоматического восстановления (Лечения)
CRITICAL_FILES = [
    "server.js", 
    "telegram_bot.js", 
    "lia.ps1", 
    "vector_memory.py", 
    "package.json", 
    "index.html", 
    "index.css",
    "topsecret $/LIA_AEGIS_SENTINEL_ULTRA.py",
    "topsecret $/LIA_SYSTEM_MANIFESTO.md", 
    "topsecret $/STAB_SYSTEM_v2.md"
]

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = Fore.WHITE
    if level == "WARNING": color = Fore.YELLOW
    elif level == "CRITICAL": color = Fore.RED
    elif level == "SYSTEM": color = Fore.CYAN
    elif level == "NETWORK": color = Fore.MAGENTA
    elif level == "AUTH": color = Fore.GREEN
    
    formatted = f"{color}[{timestamp}] [{level}] {msg}{Style.RESET_ALL}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {msg}\n")

# --- 1. ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ БЭКАПОВ ---
def init_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    log("Инициализация защищенных резервных копий...", "SYSTEM")
    for rel_path in CRITICAL_FILES:
        src = os.path.join(PROJECT_ROOT, rel_path.replace("/", os.sep))
        if os.path.exists(src):
            dest = os.path.join(BACKUP_DIR, os.path.basename(rel_path))
            if not os.path.exists(dest):
                try:
                    shutil.copy2(src, dest)
                    log(f"Создан эталонный бэкап: {os.path.basename(rel_path)}", "SYSTEM")
                except Exception as e:
                    log(f"Ошибка бэкапа {rel_path}: {e}", "WARNING")

# --- 2. ПРОТОКОЛЫ ЛЕЧЕНИЯ И КАРАНТИНА ---
def heal_file(filepath):
    filename = os.path.basename(filepath)
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path):
        log(f"🚨 [ЛЕЧЕНИЕ]: Восстановление поврежденного файла {filename} из бэкапа...", "CRITICAL")
        try:
            shutil.copy2(backup_path, filepath)
            log(f"🟢 [ЛЕЧЕНИЕ]: Файл {filename} успешно вылечен и восстановлен.", "AUTH")
            return True
        except Exception as e:
            log(f"❌ [ЛЕЧЕНИЕ]: Ошибка восстановления {filename}: {e}", "CRITICAL")
    return False

def quarantine_file(filepath):
    log(f"⚠️ [ИЗБАВЛЕНИЕ]: Инициирован перенос файла в карантин: {os.path.basename(filepath)}", "WARNING")
    try:
        filename = os.path.basename(filepath)
        dest_path = os.path.join(QUARANTINE_DIR, f"{filename}.{int(time.time())}.quarantine")
        shutil.move(filepath, dest_path)
        try:
            os.chmod(dest_path, 0o000)  # Убираем все права доступа
        except: pass
        log(f"💀 [ИЗБАВЛЕНИЕ]: Файл изолирован в карантин: {dest_path}", "CRITICAL")
        return True
    except Exception as e:
        log(f"❌ [ИЗБАВЛЕНИЕ]: Не удалось переместить {filename} в карантин: {e}", "CRITICAL")
    return False

def terminate_suspicious_process(proc_info):
    pid = proc_info['pid']
    name = proc_info['name']
    log(f"⚠️ [УНИЧТОЖЕНИЕ]: Обнаружен вредоносный процесс: {name} (PID: {pid}). Убийство...", "WARNING")
    try:
        p = psutil.Process(pid)
        p.kill()
        log(f"💀 [УНИЧТОЖЕНИЕ]: Процесс {name} (PID: {pid}) успешно ликвидирован.", "CRITICAL")
    except Exception as e:
        log(f"❌ [УНИЧТОЖЕНИЕ]: Не удалось завершить процесс {pid}: {e}", "CRITICAL")

# --- 3. АНАЛИЗАТОР И ХЕШИРОВАНИЕ ---
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
    
    # Исключаем файлы в карантине или бэкапах
    if "quarantine" in filepath.lower() or "backups" in filepath.lower():
        return "[NORMAL]"
        
    if "temp" in filepath.lower() or "appdata" in filepath.lower(): score += 2
    if ext in {'.exe', '.dll', '.vbs', '.ps1', '.bat'}: score += 3
    if filename.count('.') > 1: score += 4
    if os.path.exists(filepath) and os.path.getsize(filepath) < 100000: score += 2
    if ext in {'.exe', '.dll'} and get_entropy(filepath) > 7.5: score += 5
    
    if score >= 8: return "[CRITICAL]"
    elif score >= 5: return "[DANGER]"
    elif score >= 2: return "[SUSPICIOUS]"
    return "[NORMAL]"

def vt_check(file_path):
    if VT_API_KEY == "ВСТАВЬ_API": return "NO_API"
    try:
        h = hashlib.sha256(open(file_path, "rb").read()).hexdigest()
        r = requests.get(f"https://www.virustotal.com/api/v3/files/{h}", headers={"x-apikey": VT_API_KEY}, timeout=5)
        if r.status_code == 200:
            stats = r.json()['data']['attributes']['last_analysis_stats']
            return f"VT: {stats['malicious']} detections"
        return "VT: NOT_FOUND"
    except: return "VT: ERROR"

# --- 4. МОНИТОРИНГ СИСТЕМЫ В РЕАЛЬНОМ ВРЕМЕНИ ---
def analyze_system():
    log("=== РЕКОГНОСЦИРОВКА СЕТИ И ПРОЦЕССОВ ===", "SYSTEM")
    try:
        for conn in psutil.net_connections():
            if conn.raddr:
                log(f"CONN: {conn.raddr.ip}:{conn.raddr.port} ({conn.status})", "NETWORK")
    except: pass

    for p in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            exe = info['exe']
            if exe:
                # Если процесс запущен из AppData/Temp, уничтожаем его
                if "AppData" in exe or "Temp" in exe:
                    log(f"[!] Опасный путь процесса: {info['name']} -> {exe}", "WARNING")
                    terminate_suspicious_process(info)
                # Стресс нагрузки
                if info['cpu_percent'] > 90:
                    log(f"[STRESS] Пиковая нагрузка CPU: {info['name']} ({info['cpu_percent']}%)", "CRITICAL")
                if info['memory_percent'] > 60:
                    log(f"[MEMORY] Пиковая нагрузка RAM: {info['name']} ({info['memory_percent']:.1f}%)", "CRITICAL")
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue

class AegisUltraWatcher(FileSystemEventHandler):
    def on_created(self, event):
        self.handle_event(event.src_path, "CREATED")
        
    def on_modified(self, event):
        self.handle_event(event.src_path, "MODIFIED")

    def handle_event(self, path, event_type):
        if os.path.isdir(path): return
        
        filename = os.path.basename(path)
        cat = classify_file(path)
        
        # Если критический файл был изменен/поврежден
        if filename in [os.path.basename(f) for f in CRITICAL_FILES]:
            log(f"Файл ядра изменен: {filename} ({event_type}) | Запуск сверки...", "SYSTEM")
            # Проводим лечение
            heal_file(path)
            return

        if cat in ["[CRITICAL]", "[DANGER]"]:
            log(f"🚨 ОБНАРУЖЕНА УГРОЗА: {path} | Статус: {cat}", "CRITICAL")
            log(f"VT_RESULT: {vt_check(path)}", "CLOUD")
            
            # Внешняя угроза -> отправляем в карантин
            quarantine_file(path)

def start_sentinel(target):
    log(f"LIA_AEGIS_ULTRA SOVEREIGN_SHIELD Active. Сектор защиты: {target}", "AUTH")
    init_backups()
    analyze_system()
    
    observer = Observer()
    observer.schedule(AegisUltraWatcher(), path=target, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(15)
            analyze_system()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    print(Fore.CYAN + "LIA // AEGIS SENTINEL ULTRA v5.0")
    path = input("Ведите сектор защиты (Enter для текущей папки): ") or "."
    start_sentinel(path)

