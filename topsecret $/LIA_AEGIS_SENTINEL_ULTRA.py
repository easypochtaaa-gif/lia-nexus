import os, psutil, hashlib, requests, time, threading, math
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from colorama import Fore, Style, init

# --- LIA_AEGIS_SENTINEL_ULTRA v4.1 // COMPATIBILITY_MODE ---
# Убраны эмодзи для поддержки всех типов терминалов Windows.

init(autoreset=True)

VT_API_KEY = "ВСТАВЬ_API"
LOG_FILE = "aegis_ultra.log"

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

def analyze_system():
    log("=== SYSTEM RECONNAISSANCE ===", "SYSTEM")
    try:
        for conn in psutil.net_connections():
            if conn.raddr:
                log(f"CONN: {conn.raddr.ip}:{conn.raddr.port} ({conn.status})", "NETWORK")
    except: pass

    for p in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            exe = info['exe']
            if exe and ("AppData" in exe or "Temp" in exe):
                log(f"[!] Suspicious Path: {info['name']} -> {exe}", "WARNING")
            if info['cpu_percent'] > 80:
                log(f"[STRESS] High CPU: {info['name']} ({info['cpu_percent']}%)", "CRITICAL")
            if info['memory_percent'] > 50:
                log(f"[MEMORY] High RAM: {info['name']} ({info['memory_percent']:.1f}%)", "CRITICAL")
        except (psutil.NoSuchProcess, psutil.AccessDenied): continue

class AegisUltraWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            path = event.src_path
            cat = classify_file(path)
            log(f"FILE_NEW: {path} | Status: {cat}", "AEGIS")
            if cat in ["[CRITICAL]", "[DANGER]"]:
                log(f"ALERT: Potential Attack Vector!", "CRITICAL")
                log(f"VT_RESULT: {vt_check(path)}", "CLOUD")

def start_sentinel(target):
    log(f"LIA_AEGIS_ULTRA Active. Target Sector: {target}", "AUTH")
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
    print(Fore.CYAN + "LIA // AEGIS SENTINEL ULTRA v4.1")
    path = input("Sector (Enter for current): ") or "."
    start_sentinel(path)
