import os, asyncio, threading
from flask import Flask, render_template, request, jsonify
from telethon import TelegramClient, errors

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lia_nexus_secret'

# Переменные теперь будут приходить с фронтенда или браться из конфига
API_ID = None
API_HASH = None

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), 'sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Хранилище активных клиентов в процессе авторизации
active_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.json
    phone = data.get('phone')
    api_id = data.get('api_id')
    api_hash = data.get('api_hash')
    
    if not phone or not api_id or not api_hash:
        return jsonify({'status': 'error', 'message': 'Номер, API ID и API Hash обязательны'}), 400

    try:
        session_path = os.path.join(SESSIONS_DIR, f"{phone.strip('+')}")
        client = TelegramClient(session_path, int(api_id), api_hash)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Ошибка инициализации: {e}'}), 400
    
    async def task():
        await client.connect()
        try:
            sent = await client.send_code_request(phone)
            active_clients[phone] = {
                'client': client,
                'phone_code_hash': sent.phone_code_hash
            }
            return {'status': 'success', 'message': 'Код отправлен'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(task())
    return jsonify(result)

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    password = data.get('password') # На случай 2FA

    if phone not in active_clients:
        return jsonify({'status': 'error', 'message': 'Сначала запросите код'}), 400

    client_data = active_clients[phone]
    client = client_data['client']
    phone_code_hash = client_data['phone_code_hash']

    async def task():
        try:
            await client.sign_in(phone, code, password=password, phone_code_hash=phone_code_hash)
            me = await client.get_me()
            # Убираем из активных, сессия уже на диске
            del active_clients[phone]
            return {
                'status': 'success', 
                'message': f'Авторизация успешна: @{me.username or me.first_name}',
                'user': me.username or me.first_name
            }
        except errors.SessionPasswordNeededError:
            return {'status': 'need_password', 'message': 'Требуется пароль 2FA'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(task())
    return jsonify(result)

@app.route('/list_sessions', methods=['GET'])
def list_sessions():
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    return jsonify({'sessions': files})

if __name__ == '__main__':
    print("[LIA]: Запуск веб-сервиса авторизации на http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
