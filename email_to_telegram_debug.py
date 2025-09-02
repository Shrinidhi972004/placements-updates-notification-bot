import imaplib
import email
import requests
import time
import os
import re
from datetime import datetime
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=ENV_PATH)

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
PASSWORD = os.getenv("EMAIL_PASSWORD")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
PLACEMENT_OFFICER = os.getenv("PLACEMENT_OFFICER")

required_vars = {
    "EMAIL_ACCOUNT": EMAIL_ACCOUNT,
    "EMAIL_PASSWORD": PASSWORD,
    "BOT_TOKEN": BOT_TOKEN,
    "GROUP_CHAT_ID": GROUP_CHAT_ID,
    "PLACEMENT_OFFICER": PLACEMENT_OFFICER
}

missing = [k for k, v in required_vars.items() if not v]
if missing:
    raise SystemExit(f"Missing env variables: {', '.join(missing)}")

print("Bot started...")

IMAP_SERVER = "imap.gmail.com"
last_seen_id = None

def log(msg: str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {msg}")

def clean_body(body: str) -> str:
    return re.sub(r'http[s]?://\S+', '[link removed]', body)

def send_to_group(message: str):
    if len(message) > 4095:
        message = message[:4095] + "\n\n[Message truncated, check Gmail for full text]"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": GROUP_CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=data, timeout=10)
        log(f"Forwarded to group {GROUP_CHAT_ID}, Response: {r.json()}")
    except Exception as e:
        log(f"Failed to send to Telegram: {e}")

def extract_safe_text(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                except Exception:
                    continue
    else:
        if msg.get_content_type() == "text/plain":
            body = msg.get_payload(decode=True).decode(errors="ignore")
    return clean_body(body)

def extract_email(sender: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
    return match.group(0).lower() if match else sender.lower()

def check_email():
    global last_seen_id
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, PASSWORD)
    except Exception as e:
        log(f"Gmail login failed: {e}. Retrying in 30s...")
        time.sleep(30)
        return

    mail.select("inbox")
    search_query = f'FROM "{PLACEMENT_OFFICER}"'
    result, data = mail.search(None, search_query)
    email_ids = data[0].split()
    if not email_ids:
        mail.logout()
        return

    latest_id = email_ids[-1]
    if latest_id == last_seen_id:
        mail.logout()
        return

    last_seen_id = latest_id
    res, msg_data = mail.fetch(latest_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    subject = msg["subject"]
    sender = msg["from"]
    sender_email = extract_email(sender)

    if PLACEMENT_OFFICER and PLACEMENT_OFFICER.lower() == sender_email:
        body = extract_safe_text(msg)
        text = f"New Placement Mail\nFrom: {sender}\n\nSubject: {subject}\n\n{body}"
        send_to_group(text)

    mail.logout()

if __name__ == "__main__":
    while True:
        check_email()
        time.sleep(30)

