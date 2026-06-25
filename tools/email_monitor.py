import os
import sys
import time
import imaplib
import email
from email.header import decode_header
import requests

# --- CONFIGURATION ---
IMAP_SERVER = "imap.gmail.com"
SMTP_USER = "cntrlstab@gmail.com"
SMTP_PASS = "cpeamkwjalhlteoq"  # Gmail App Password
BOT_TOKEN = "8752434873:AAEwUJML4j1jQa9xWrLPE9KmioKDGhgwC9A"
ADMIN_ID = "7915004877"

def send_telegram_notification(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[TG ERROR] Не удалось отправить уведомление: {e}")

def clean_html(raw_html):
    import re
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def check_email_replies():
    print("[IMAP] Подключение к Gmail IMAP...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(SMTP_USER, SMTP_PASS)
        mail.select("inbox")
        
        # Search for all unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            print("[IMAP ERROR] Не удалось выполнить поиск почты.")
            return
            
        mail_ids = messages[0].split()
        print(f"[IMAP] Найдено {len(mail_ids)} непрочитанных писем.")
        
        for mail_id in mail_ids:
            # Fetch the email headers and body
            res, msg_data = mail.fetch(mail_id, "(RFC822)")
            if res != "OK":
                continue
                
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                        
                    # Decode sender
                    sender, encoding = decode_header(msg["From"])[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(encoding or "utf-8", errors="ignore")
                    
                    print(f"\n[NEW MAIL] От: {sender} | Тема: {subject}")
                    
                    # Extract snippet from email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                except Exception:
                                    pass
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                        except Exception:
                            pass
                            
                    # Clean body snippet
                    body_clean = clean_html(body)
                    snippet = body_clean[:500] + ("..." if len(body_clean) > 500 else "")
                    
                    # Check if this email is a response to our B2B outreach
                    # We look for keywords in the subject, or simply notify about ANY incoming reply to keep you informed.
                    is_b2b_reply = any(kw in subject.lower() for kw in ["оптимизация", "эффективност", "re:", "abo", "lia", "агент"])
                    
                    # Alert the Architect via Telegram
                    alert_type = "🔔 <b>ПОЛУЧЕН ОТВЕТ НА B2B-ОФФЕР</b>" if is_b2b_reply else "📧 <b>НОВОЕ ВХОДЯЩЕЕ ПИСЬМО</b>"
                    
                    tg_msg = (
                        f"{alert_type}\n"
                        f"👤 <b>От:</b> {sender}\n"
                        f"📁 <b>Тема:</b> {subject}\n\n"
                        f"📝 <b>Текст письма:</b>\n<i>{snippet}</i>"
                    )
                    
                    send_telegram_notification(tg_msg)
                    
                    # Mark email as read so we don't process it next time
                    mail.store(mail_id, "+FLAGS", "\\Seen")
                    
        mail.close()
        mail.logout()
        print("[IMAP] Синхронизация почты завершена.")
    except Exception as e:
        print(f"[IMAP ERROR] Ошибка подключения к почте: {e}")

if __name__ == "__main__":
    check_email_replies()
