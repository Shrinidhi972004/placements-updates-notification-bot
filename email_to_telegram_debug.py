import imaplib
import email
import requests
import time
import os
import re

# --- Config ---
print("Bot started...")
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
PASSWORD = os.getenv("EMAIL_PASSWORD")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
PLACEMENT_OFFICER = os.getenv("PLACEMENT_OFFICER", "placements@sahyadri.edu.in")

last_seen_id = None

def clean_body(body: str) -> str:
    """Remove all http/https links from the email body"""
    return re.sub(r'http[s]?://\S+', '[link removed]', body)

def send_to_group(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": GROUP_CHAT_ID,
        "text": message  # no Markdown, plain text
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"Forwarded to group {GROUP_CHAT_ID}, Response:", r.json())
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")

def extract_safe_text(msg):
    """Extract only safe text/plain parts, ignore attachments & HTML"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body += part.get_payload(decode=True).decode(errors="ignore")
    else:
        if msg.get_content_type() == "text/plain":
            body = msg.get_payload(decode=True).decode(errors="ignore")
    return clean_body(body)

def check_email():
    global last_seen_id
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, PASSWORD)
        print("Logged in to Gmail")
    except Exception as e:
        print(f"Gmail login failed: {e}. Retrying in 30s...")
        time.sleep(30)
        return

    mail.select("inbox")
    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()
    if not email_ids:
        mail.logout()
        return

    latest_id = email_ids[-1]
    if latest_id == last_seen_id:
        mail.logout()
        return  # no new email

    last_seen_id = latest_id
    res, msg_data = mail.fetch(latest_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    subject = msg["subject"]
    sender = msg["from"]
    print(f"New mail from {sender}, Subject: {subject}")

    if PLACEMENT_OFFICER in sender.lower():
        print("Placement mail detected. Forwarding...")
        body = extract_safe_text(msg)
        text = f"New Placement Mail\nFrom: {sender}\n\nSubject: {subject}\n\n{body}"
        send_to_group(text)
    else:
        print("Skipped (not from placement officer)")

    mail.logout()

# --- Loop ---
if __name__ == "__main__":
    while True:
        check_email()
        time.sleep(30)  # check every 30 seconds
