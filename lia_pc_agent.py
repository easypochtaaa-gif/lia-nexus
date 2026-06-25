import os
import time
import telebot
import pyautogui
import platform
import subprocess
import ctypes
import requests
import threading
import psutil
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from telebot import types

# Загрузка переменных окружения
load_dotenv()

# ВАШИ НАСТРОЙКИ
TOKEN = os.getenv("LOCAL_BOT_TOKEN", "8864182812:AAFMxmd8vu4CEuFK5RoJKivqrMwrIqFrN-c")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "7915004877,7782822551")
ADMIN_IDS = [int(i.strip()) for i in ADMIN_IDS_STR.split(",") if i.strip()]

OPENAI_API_KEY = os.getenv("LOCAL_OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

bot = telebot.TeleBot(TOKEN)

# Глобальное состояние
ADMIN_OVERRIDE = {} # chat_id -> bool

def check_admin(message):
    return message.from_user.id in ADMIN_IDS

def get_system_info():
    info = f"👁 LIA PC AGENT // ONLINE\n"
    info += f"--------------------------\n"
    info += f"OS: {platform.system()} {platform.release()}\n"
    info += f"Node: {platform.node()}\n"
    info += f"Time: {time.strftime('%H:%M:%S')}\n"
    info += f"Status: СИСТЕМА ПОД КОНТРОЛЕМ\n"
    info += f"--------------------------\n"
    info += f"/admin — SUPREME ADMIN PANEL\n"
    info += f"/help — список команд терминала"
    return info

def _run_shell(cmd, timeout=90):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                           timeout=timeout, encoding="utf-8", errors="replace")
        out = (r.stdout or "")
        if r.stderr:
            out += ("\n[stderr]\n" + r.stderr)
        out = out.strip() or "(пустой вывод)"
        return out
    except subprocess.TimeoutExpired:
        return f"⏱ Команда превысила лимит {timeout}с и была прервана."
    except Exception as e:
        return f"Ошибка выполнения: {e}"

def _send_long(chat_id, text):
    MAX = 3800
    if not text:
        text = "(пусто)"
    for i in range(0, len(text), MAX):
        bot.send_message(chat_id, "```\n" + text[i:i+MAX] + "\n```", parse_mode="Markdown")

def _arg(message):
    p = message.text.split(maxsplit=1)
    return p[1].strip() if len(p) > 1 else ""

@bot.message_handler(commands=['admin'])
def cmd_admin_panel(message):
    if not check_admin(message): return
    
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    status_text = (
        f"🔴 *SUPREME ADMIN PANEL*\n\n"
        f"💻 *System Metrics:*\n"
        f"CPU: `{cpu}%` {'🔴' if cpu > 80 else '🟢'}\n"
        f"RAM: `{ram}%` {'🔴' if ram > 80 else '🟢'}\n"
        f"Disk: `{disk}%` {'🔴' if disk > 90 else '🟢'}\n\n"
        f"🛡 *Override Mode:* `{'ENABLED' if ADMIN_OVERRIDE.get(message.chat.id) else 'DISABLED'}`"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📸 Screenshot", callback_data="adm_screen"),
        types.InlineKeyboardButton("📊 Processes", callback_data="adm_ps"),
        types.InlineKeyboardButton("🌐 Network", callback_data="adm_net"),
        types.InlineKeyboardButton("🔐 Lock PC", callback_data="adm_lock"),
        types.InlineKeyboardButton("⚡ Override", callback_data="adm_override"),
        types.InlineKeyboardButton("☢️ Nuclear", callback_data="adm_nuclear")
    )
    
    bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.id not in ADMIN_IDS: return
    
    if call.data == "adm_screen":
        bot.answer_callback_query(call.id, "Захват экрана...")
        take_screenshot(call.message)
    elif call.data == "adm_ps":
        bot.answer_callback_query(call.id, "Сбор процессов...")
        ps = ("powershell -NoProfile -Command \"Get-Process | Sort-Object CPU -Descending | "
              "Select-Object -First 15 Name,Id,@{n='CPU';e={$_.CPU}} | Format-Table -AutoSize | Out-String\"")
        _send_long(call.message.chat.id, _run_shell(ps))
    elif call.data == "adm_net":
        bot.answer_callback_query(call.id, "Сетевой аудит...")
        _send_long(call.message.chat.id, _run_shell("netstat -an | findstr ESTABLISHED"))
    elif call.data == "adm_lock":
        bot.answer_callback_query(call.id, "Блокировка...")
        lock_pc(call.message)
    elif call.data == "adm_override":
        curr = ADMIN_OVERRIDE.get(call.message.chat.id, False)
        ADMIN_OVERRIDE[call.message.chat.id] = not curr
        bot.answer_callback_query(call.id, f"Override: {'ON' if not curr else 'OFF'}")
        cmd_admin_panel(call.message) # Refresh
    elif call.data == "adm_nuclear":
        bot.answer_callback_query(call.id, "NUCLEAR: модуль деактивирован")
        bot.send_message(call.message.chat.id, "☢️ NUCLEAR RESET: модуль деактивирован. Используйте ручные команды.")

@bot.message_handler(commands=['help', 'commands', 'menu'])
def send_help(message):
    if not check_admin(message): return
    txt = (
        "👁 *LIA PC AGENT* — терминал ПК\n\n"
        "🔴 *АДМИНКА*: /admin\n\n"
        "🖥 *Система*\n"
        "/status /sysinfo /uptime /whoami\n"
        "/ps — процессы · /services — службы\n"
        "/kill <PID> · /killname <имя>\n"
        "/disk — диски · /apps — программы\n\n"
        "🌐 *Сеть*\n"
        "/ip /publicip /netstat\n"
        "/ping <хост> · /wifi — сохранённые сети+пароли\n\n"
        "📁 *Файлы*\n"
        "/dir <путь> · /find <имя>\n"
        "/read <файл> · /get <файл> — скачать в Telegram\n"
        "/del <путь> · /open <путь|url>\n\n"
        "🎛 *Управление*\n"
        "/screen · /lock · /type <текст> · /key <комбо>\n"
        "/volup /voldown /mute\n"
        "/notify <текст> · /say <текст>\n\n"
        "💬 *Терминал*\n"
        "/cmd <команда> — выполнить в shell\n"
        "Любой текст без / — диалог с Лией (GPT)"
    )
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'status'])
def send_welcome(message):
    if not check_admin(message): return
    bot.reply_to(message, get_system_info())

# ---------- СИСТЕМА ----------
@bot.message_handler(commands=['sysinfo'])
def cmd_sysinfo(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    ps = ("powershell -NoProfile -Command \""
          "$os=Get-CimInstance Win32_OperatingSystem;"
          "$cpu=(Get-CimInstance Win32_Processor).Name;"
          "$ram=[math]::Round($os.TotalVisibleMemorySize/1MB,1);"
          "$free=[math]::Round($os.FreePhysicalMemory/1MB,1);"
          "$up=(Get-Date)-$os.LastBootUpTime;"
          "Write-Output ('OS: '+$os.Caption+' '+$os.Version);"
          "Write-Output ('CPU: '+$cpu);"
          "Write-Output ('RAM: '+$free+' / '+$ram+' GB free');"
          "Write-Output ('Uptime: '+[int]$up.TotalHours+'h '+$up.Minutes+'m')\"")
    _send_long(message.chat.id, _run_shell(ps))

@bot.message_handler(commands=['uptime'])
def cmd_uptime(message):
    if not check_admin(message): return
    _send_long(message.chat.id, _run_shell(
        "powershell -NoProfile -Command \"$u=(Get-Date)-(Get-CimInstance Win32_OperatingSystem).LastBootUpTime; "
        "'Uptime: {0}d {1}h {2}m' -f $u.Days,$u.Hours,$u.Minutes\""))

@bot.message_handler(commands=['whoami'])
def cmd_whoami(message):
    if not check_admin(message): return
    _send_long(message.chat.id, _run_shell("whoami /user & echo. & hostname"))

@bot.message_handler(commands=['services'])
def cmd_services(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell(
        "powershell -NoProfile -Command \"Get-Service | Where-Object Status -eq 'Running' | "
        "Select-Object -First 40 Name,DisplayName | Format-Table -AutoSize | Out-String\""))

@bot.message_handler(commands=['killname'])
def cmd_killname(message):
    if not check_admin(message): return
    name = _arg(message)
    if not name:
        bot.reply_to(message, "Использование: /killname <имя.exe>"); return
    _send_long(message.chat.id, _run_shell(f'taskkill /IM "{name}" /F'))

@bot.message_handler(commands=['apps'])
def cmd_apps(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell(
        "powershell -NoProfile -Command \"Get-ItemProperty "
        "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*,"
        "HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* "
        "-ErrorAction SilentlyContinue | Where-Object DisplayName | "
        "Select-Object -ExpandProperty DisplayName | Sort-Object -Unique | Out-String\""))

# ---------- СЕТЬ ----------
@bot.message_handler(commands=['publicip'])
def cmd_publicip(message):
    if not check_admin(message): return
    _send_long(message.chat.id, _run_shell("curl -s https://ifconfig.me || curl -s https://api.ipify.org"))

@bot.message_handler(commands=['netstat'])
def cmd_netstat(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell(
        "powershell -NoProfile -Command \"Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | "
        "Select-Object -First 30 LocalAddress,LocalPort,RemoteAddress,RemotePort | Format-Table -AutoSize | Out-String\""))

@bot.message_handler(commands=['ping'])
def cmd_ping(message):
    if not check_admin(message): return
    host = _arg(message)
    if not host:
        bot.reply_to(message, "Использование: /ping <хост>"); return
    _send_long(message.chat.id, _run_shell(f"ping -n 4 {host}"))

@bot.message_handler(commands=['wifi'])
def cmd_wifi(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    ps = ("powershell -NoProfile -Command \""
          "(netsh wlan show profiles) | Select-String ':(.+)$' | ForEach-Object { $n=$_.Matches.Groups[1].Value.Trim(); "
          "$k=(netsh wlan show profile name=\\\"$n\\\" key=clear) | Select-String 'Key Content|Содержимое ключа'; "
          "$p = if($k){ ($k -split ':')[-1].Trim() } else { '<нет>' }; Write-Output ($n+' : '+$p) }\"")
    _send_long(message.chat.id, _run_shell(ps))

# ---------- ФАЙЛЫ ----------
@bot.message_handler(commands=['find'])
def cmd_find(message):
    if not check_admin(message): return
    name = _arg(message)
    if not name:
        bot.reply_to(message, "Использование: /find <маска, напр. *.pdf>"); return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell(
        f"powershell -NoProfile -Command \"Get-ChildItem -Path $env:USERPROFILE -Recurse -Filter '{name}' "
        f"-ErrorAction SilentlyContinue | Select-Object -First 40 -ExpandProperty FullName | Out-String\""))

@bot.message_handler(commands=['read', 'cat'])
def cmd_read(message):
    if not check_admin(message): return
    path = _arg(message).strip('"')
    if not path:
        bot.reply_to(message, "Использование: /read <файл>"); return
    if not os.path.isfile(path):
        bot.reply_to(message, "Файл не найден."); return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(20000)
        _send_long(message.chat.id, data or "(пусто)")
    except Exception as e:
        bot.reply_to(message, f"Ошибка чтения: {e}")

@bot.message_handler(commands=['get', 'download'])
def cmd_get(message):
    if not check_admin(message): return
    path = _arg(message).strip('"')
    if not path:
        bot.reply_to(message, "Использование: /get <путь к файлу>"); return
    if not os.path.isfile(path):
        bot.reply_to(message, "Файл не найден."); return
    if os.path.getsize(path) > 49 * 1024 * 1024:
        bot.reply_to(message, "Файл больше 49 МБ — Telegram не пропустит."); return
    try:
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.reply_to(message, f"Ошибка отправки: {e}")

@bot.message_handler(commands=['del'])
def cmd_del(message):
    if not check_admin(message): return
    path = _arg(message).strip('"')
    if not path:
        bot.reply_to(message, "Использование: /del <путь>"); return
    _send_long(message.chat.id, _run_shell(f'del /F /Q "{path}" & echo Удалено: {path}'))

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not check_admin(message): return
    try:
        info = bot.get_file(message.document.file_id)
        data = bot.download_file(info.file_path)
        save_dir = os.path.join(os.path.expanduser("~"), "Downloads", "LIA_uploads")
        os.makedirs(save_dir, exist_ok=True)
        dest = os.path.join(save_dir, message.document.file_name)
        with open(dest, "wb") as f:
            f.write(data)
        bot.reply_to(message, f"📥 Сохранено: {dest}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка загрузки: {e}")

# ---------- УПРАВЛЕНИЕ ----------
@bot.message_handler(commands=['screen'])
def take_screenshot(message):
    if not check_admin(message): return
    try:
        msg = bot.send_message(message.chat.id, "👁 Захват визуального потока...")
        screenshot = pyautogui.screenshot()
        screenshot.save("screen.png")
        with open("screen.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo)
        os.remove("screen.png")
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"Ошибка захвата: {e}")

@bot.message_handler(commands=['lock'])
def lock_pc(message):
    if not check_admin(message): return
    bot.reply_to(message, "🔐 Протокол блокировки активирован. До встречи в системе.")
    if platform.system() == "Windows":
        ctypes.windll.user32.LockWorkStation()
    else:
        bot.reply_to(message, "Команда доступна только для Windows.")

@bot.message_handler(commands=['clip'])
def cmd_clip(message):
    if not check_admin(message): return
    _send_long(message.chat.id, _run_shell("powershell -NoProfile -Command \"Get-Clipboard\""))

@bot.message_handler(commands=['setclip'])
def cmd_setclip(message):
    if not check_admin(message): return
    txt = _arg(message)
    if not txt:
        bot.reply_to(message, "Использование: /setclip <текст>"); return
    try:
        subprocess.run("clip", input=txt, text=True, shell=True, encoding="utf-8")
        bot.reply_to(message, "📋 Буфер обмена обновлён.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['type'])
def cmd_type(message):
    if not check_admin(message): return
    txt = _arg(message)
    if not txt:
        bot.reply_to(message, "Использование: /type <текст>"); return
    try:
        subprocess.run("clip", input=txt, text=True, shell=True, encoding="utf-8")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "v")
        bot.reply_to(message, "⌨️ Вставлено в активное окно.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['key'])
def cmd_key(message):
    if not check_admin(message): return
    combo = _arg(message)
    if not combo:
        bot.reply_to(message, "Использование: /key <комбо>, напр. win+d или ctrl+c"); return
    try:
        keys = [k.strip().lower() for k in combo.replace(" ", "").split("+")]
        pyautogui.hotkey(*keys)
        bot.reply_to(message, f"⌨️ Нажато: {combo}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['volup'])
def cmd_volup(message):
    if not check_admin(message): return
    _sendkeys(175); bot.reply_to(message, "🔊 Громче")

@bot.message_handler(commands=['voldown'])
def cmd_voldown(message):
    if not check_admin(message): return
    _sendkeys(174); bot.reply_to(message, "🔉 Тише")

@bot.message_handler(commands=['mute'])
def cmd_mute(message):
    if not check_admin(message): return
    _sendkeys(173); bot.reply_to(message, "🔇 Звук переключён")

@bot.message_handler(commands=['notify'])
def cmd_notify(message):
    if not check_admin(message): return
    txt = _arg(message) or "LIA"
    safe = txt.replace("'", "''")
    _run_shell(f"powershell -NoProfile -Command \"(New-Object -ComObject WScript.Shell).Popup('{safe}',8,'LIA',0)\"")
    bot.reply_to(message, "🔔 Уведомление показано на ПК.")

@bot.message_handler(commands=['say'])
def cmd_say(message):
    if not check_admin(message): return
    txt = _arg(message)
    if not txt:
        bot.reply_to(message, "Использование: /say <текст>"); return
    safe = txt.replace("'", "''")
    _run_shell("powershell -NoProfile -Command \"Add-Type -AssemblyName System.Speech;"
               f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')\"")
    bot.reply_to(message, "🗣 Озвучено.")

# ---------- ПИТАНИЕ ----------
@bot.message_handler(commands=['sleep'])
def cmd_sleep(message):
    if not check_admin(message): return
    bot.reply_to(message, "😴 Перевожу ПК в сон.")
    _run_shell("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

@bot.message_handler(commands=['logoff'])
def cmd_logoff(message):
    if not check_admin(message): return
    bot.reply_to(message, "🚪 Выход из системы.")
    _run_shell("shutdown /l")

@bot.message_handler(commands=['shutdown'])
def cmd_shutdown(message):
    if not check_admin(message): return
    arg = _arg(message)
    mins = int(arg) if arg.isdigit() else 1
    bot.reply_to(message, f"⏻ Выключение через {mins} мин. Отмена: /cancel")
    _run_shell(f"shutdown /s /t {mins*60}")

@bot.message_handler(commands=['reboot'])
def cmd_reboot(message):
    if not check_admin(message): return
    arg = _arg(message)
    mins = int(arg) if arg.isdigit() else 1
    bot.reply_to(message, f"🔄 Перезагрузка через {mins} мин. Отмена: /cancel")
    _run_shell(f"shutdown /r /t {mins*60}")

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    if not check_admin(message): return
    _run_shell("shutdown /a")
    bot.reply_to(message, "✅ Выключение/перезагрузка отменены.")

# ---------- ТЕРМИНАЛ ----------
@bot.message_handler(commands=['cmd', 'sh', 'run'])
def cmd_exec(message):
    if not check_admin(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Использование: /cmd <команда>\nНапример: /cmd ipconfig /all")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell(parts[1]))

@bot.message_handler(commands=['ps'])
def cmd_ps(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    ps = ("powershell -NoProfile -Command \"Get-Process | Sort-Object WS -Descending | "
          "Select-Object -First 15 Name,Id,@{n='MB';e={[math]::Round($_.WS/1MB)}} | "
          "Format-Table -AutoSize | Out-String\"")
    _send_long(message.chat.id, _run_shell(ps))

@bot.message_handler(commands=['ip'])
def cmd_ip(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    _send_long(message.chat.id, _run_shell("ipconfig"))

@bot.message_handler(commands=['disk'])
def cmd_disk(message):
    if not check_admin(message): return
    bot.send_chat_action(message.chat.id, 'typing')
    ps = ("powershell -NoProfile -Command \"Get-PSDrive -PSProvider FileSystem | "
          "Select-Object Name,@{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}},"
          "@{n='UsedGB';e={[math]::Round($_.Used/1GB,1)}} | Format-Table -AutoSize | Out-String\"")
    _send_long(message.chat.id, _run_shell(ps))

@bot.message_handler(commands=['dir', 'ls'])
def cmd_dir(message):
    if not check_admin(message): return
    parts = message.text.split(maxsplit=1)
    path = parts[1] if len(parts) > 1 else "."
    _send_long(message.chat.id, _run_shell(f'dir "{path}"'))

@bot.message_handler(commands=['kill'])
def kill_proc(message):
    if not check_admin(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Использование: /kill <PID>")
        return
    _send_long(message.chat.id, _run_shell(f"taskkill /PID {parts[1].strip()} /F"))

@bot.message_handler(commands=['open'])
def cmd_open(message):
    if not check_admin(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Использование: /open <путь, url или программа>")
        return
    target = parts[1].strip()
    _send_long(message.chat.id, _run_shell(f'start "" "{target}"'))

@bot.message_handler(func=lambda m: True)
def handle_smart_commands(message):
    if not check_admin(message): return
    
    user_text = message.text
    if user_text.startswith('/'): return
    
    if not client:
        bot.reply_to(message, "⚠️ Ошибка: OPENAI_API_KEY не задан.")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    system_prompt = (
        "Ты — Лия (LIA), суверенный ИИ-ассистент, управляющий этим ПК. "
        "Твой стиль: киберпанк, лаконичность, высокий интеллект. "
        "Ты можешь помогать Артуру и его доверенным лицам в управлении системой."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка GPT: {e}")

if __name__ == "__main__":
    print("LIA PC AGENT // ACTIVE")
    bot.infinity_polling()
