import os
import csv
import psycopg2
from datetime import datetime

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

def init_db():
    load_env()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL not found in .env")
        return

    print("[SYSTEM] Подключение к Neon Cloud PostgreSQL...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Create leads table
        print("[SYSTEM] Инициализация таблицы leads...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                messages_sent INT DEFAULT 0,
                replies_received INT DEFAULT 0,
                clients_converted INT DEFAULT 0,
                revenue DOUBLE PRECISION DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create chat_history table for LIA Personal Assistant
        print("[SYSTEM] Инициализация таблицы chat_history...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                role VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("[SUCCESS] Все таблицы успешно созданы в Neon Cloud!")

        # Import local CSV data if exists
        csv_path = os.path.join(os.path.dirname(__file__), "STAB_TRACKING.csv")
        if os.path.exists(csv_path):
            print("[SYSTEM] Обнаружен локальный файл STAB_TRACKING.csv. Перенос данных...")
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None) # Skip header
                
                rows_imported = 0
                for row in reader:
                    if not row or len(row) < 5:
                        continue
                    
                    try:
                        date_val = datetime.strptime(row[0].strip(), "%Y-%m-%d").date()
                        msgs = int(row[1].strip())
                        replies = int(row[2].strip())
                        clients = int(row[3].strip())
                        rev = float(row[4].strip())

                        # Check if duplicate date
                        cur.execute("SELECT id FROM leads WHERE date = %s", (date_val,))
                        if cur.fetchone():
                            continue # Already imported
                        
                        cur.execute("""
                            INSERT INTO leads (date, messages_sent, replies_received, clients_converted, revenue)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (date_val, msgs, replies, clients, rev))
                        rows_imported += 1
                    except Exception as ex:
                        print(f"[WARN] Ошибка импорта строки {row}: {ex}")

            conn.commit()
            print(f"[SUCCESS] Перенос завершен. Импортировано записей: {rows_imported}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Ошибка инициализации базы данных: {e}")

if __name__ == "__main__":
    init_db()
