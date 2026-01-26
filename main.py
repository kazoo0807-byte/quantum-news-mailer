import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# =====================
# 設定
# =====================
FROM_EMAIL = "kazoo0807@gmail.com"
TO_EMAIL = "kazoo0807@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

SENT_FILE = "sent_articles.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================
# 既送信記事の読み込み
# =====================
if os.path.exists(SENT_FILE):
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        sent_articles = json.load(f)
else:
    sent_articles = []

def is_duplicate(title, url):
    for a in sent_articles:
        if a["title"] == title or a["url"] == url:
            return True
    return False

# =====================
# 日本語要約（簡易）
# =====================
def summarize_japanese(text, limit=100):
    text = text.replace("\n", "").strip()
    return text[:limit] + ("…" if len(text) > limit else "")

# =====================
# Quantum Insider
# =====================
def fetch_quantum_insider():
    base = "https://thequantuminsider.com"
    results = []

    for path in ["/news/", "/resources/"]:
        url = base + path
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        for article in soup.select("article"):
            a_tag = article.find("a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            if not link.startswith("http"):
                link =
