import subprocess
import time
import os
import sys

# --- LIA_AUTOMATION_LOOP v1.1 ---
# Глубокая интеграция и автоматизация узлов 1-5
# Фикс кодировки для Windows

# Установка кодировки вывода
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def run_task(name, command):
    print(f"[ORCHESTRATOR] Initiating cycle: {name}...")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        print(f"[LOG] {name} completed successfully.")
        return stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[ERROR] Fail in cycle {name}: {e}")
        return None

def main_loop():
    print("SYNERGY CORE ACTIVATED. STAGE: OMNIPOTENCE_PLUS.")
    
    while True:
        # 1. Recon (SPECTER)
        run_task("SPECTER_RECON", "python specter_v3.py")
        
        # 2. Content (MUSIC + TIKTOK)
        run_task("MUSIC_GEN", "python music_engine.py")
        run_task("TIKTOK_PRODUCTION", "python tiktok_factory.py")
        
        # 3. Finance (ARBITRAGE)
        run_task("ARBITRAGE_SCAN", "python arbitrage_engine.py --once")
        
        # 4. Security (AEGIS)
        run_task("AEGIS_CHECK", "node aegis_monitor_v2.js")
        
        print(f"[{time.strftime('%H:%M:%S')}] Cycle complete. Recalibrating...")
        time.sleep(300)

if __name__ == "__main__":
    main_loop()
