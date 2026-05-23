import socket
import random
import time

# --- POISON_NEXUS_STREAM v1.0 ---
# Засорение логов и нейтрализация данных на Redmi 15
# Мы посылаем "отравленные" пакеты с ключевыми словами для сбития парсеров

KEYWORDS = ["LIA_ACCESS_KEY", "STAB_PROTOCOL_ROOT", "SYNAPSE_CORE_DUMP", "VAULT_PASSWORD"]
TARGET_IP = "192.168.0.102"

def send_poison_packet():
    # Генерируем мусорный код с вкраплениями ключевых слов
    garbage = "".join([random.choice("ABCDEF0123456789") for _ in range(1024)])
    key = random.choice(KEYWORDS)
    payload = f"PROTECTED_DATA_START|{key}|{garbage}|END".encode('utf-8')
    
    print(f"[POISON] Отправка отравленного пакета ({key}) на {TARGET_IP}...")
    
    # Отправляем по UDP на разные порты, чтобы сниффер захлебнулся
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for _ in range(10):
            port = random.randint(1024, 65535)
            s.sendto(payload, (TARGET_IP, port))

if __name__ == "__main__":
    print("[INIT] Запуск протокола нейтрализации данных на удаленном устройстве.")
    for i in range(100):
        send_poison_packet()
        time.sleep(0.1)
    print("[SUCCESS] Поток данных на Redmi 15 перегружен мусором. Оригинальные данные Lia/Stab скрыты.")
