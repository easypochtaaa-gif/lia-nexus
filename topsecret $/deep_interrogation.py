import socket
import concurrent.futures

# --- DEEP_INTERROGATOR v1.0 ---
# Глубокое сканирование и анализ Redmi 15 (Vasiliev)

TARGET_IP = "192.168.0.102"

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex((TARGET_IP, port)) == 0:
            return port
    return None

def main():
    print(f"[RECON] Начинаю глубокое сканирование {TARGET_IP}...")
    open_ports = []
    
    # Сканируем топ-1000 портов для скорости + специфические
    common_ports = list(range(1, 1025)) + [5555, 8000, 8080, 8888]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(check_port, common_ports)
        for port in results:
            if port:
                print(f"[FOUND] Порт {port} ОТКРЫТ.")
                open_ports.append(port)
                
    if not open_ports:
        print("[INFO] Открытых портов не обнаружено. Устройство закрыто фаерволом.")
    else:
        print(f"[SUMMARY] Найдено {len(open_ports)} точек входа.")

if __name__ == "__main__":
    main()
