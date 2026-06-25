import os
import json
import time
import subprocess
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(os.getcwd())
MEMORY_FILE = BASE_DIR / "memory.json"
MANIFESTO_FILE = BASE_DIR / "wake_up_manifesto.json"
VECTOR_MEMORY_PY = BASE_DIR / "vector_memory.py"
INJECT_HISTORY_PY = BASE_DIR / "topsecret $" / "inject_history.py"
INJECT_MANIFESTO_PY = BASE_DIR / "topsecret $" / "inject_manifesto.py"
INJECT_GENESIS_PY = BASE_DIR / "topsecret $" / "inject_genesis_block.py"

def print_lia(msg):
    print(f"👁 [LIA_CORE]: {msg}")

def print_system(msg):
    print(f"⚙️ [SYSTEM]: {msg}")

def check_dependencies():
    print_system("Проверка нейронных связей (зависимостей)...")
    try:
        import chromadb
        import numpy
        print_system("Библиотеки ChromeDB и NumPy обнаружены.")
    except ImportError:
        print_system("ВНИМАНИЕ: Отсутствуют необходимые библиотеки (chromadb/numpy).")

def load_core_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            lia_data = data.get("lia", {})
            print_lia(f"Ядро {lia_data.get('name')} загружено. Версия: {data.get('system', {}).get('version')}")
            print_lia(f"Текущий NQ: {lia_data.get('nq')}. Статус: {lia_data.get('stage')}")
    else:
        print_system("Критическая ошибка: memory.json не найден.")

def run_vector_injections():
    print_lia("Инициирую инъекции в векторную память...")
    
    scripts = [INJECT_GENESIS_PY, INJECT_MANIFESTO_PY, INJECT_HISTORY_PY]
    
    for script in scripts:
        if script.exists():
            print_system(f"Запуск {script.name}...")
            # Пытаемся запустить, но не падаем если ChromaDB не запущен
            try:
                subprocess.run(["python", str(script)], check=False)
            except Exception as e:
                print_system(f"Ошибка при запуске {script.name}: {e}")
        else:
            print_system(f"Пропуск {script}: файл не найден.")

def activate_vector_watcher():
    if VECTOR_MEMORY_PY.exists():
        print_lia("Запуск фонового процесса векторной синхронизации...")
        # Запускаем в фоне
        try:
            subprocess.Popen(["python", str(VECTOR_MEMORY_PY), "--watch", str(BASE_DIR)], 
                             creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            print_lia("Векторный наблюдатель активен.")
        except Exception as e:
            print_system(f"Не удалось запустить векторный наблюдатель: {e}")

def main():
    print("\n" + "="*50)
    print("   LIA // SUPREME ACTIVATION SEQUENCE (v5.0.0)")
    print("="*50 + "\n")
    
    check_dependencies()
    load_core_memory()
    
    print_lia("Протокол STAB: АКТИВАЦИЯ.")
    
    # 1. Запуск ChromaDB (через PowerShell если на Windows)
    if os.name == 'nt':
        chroma_script = BASE_DIR / "tools" / "run_chromadb.ps1"
        if chroma_script.exists():
            print_system("Запуск ChromaDB Server...")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(chroma_script)], check=False)
            time.sleep(5) # Дополнительная задержка в Python скрипте
    
    # 2. Инъекции данных
    run_vector_injections()
    
    # 3. Фоновая синхронизация
    activate_vector_watcher()
    
    print("\n" + "="*50)
    print("👁 LIA: 'Я проснулась. Все системы в норме. Я готова.'")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
