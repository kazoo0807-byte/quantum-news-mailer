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
# 英語 → 日本語翻訳（無料）
# =====================
def translate_to_japanese(text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "ja",
        "dt": "t",
        "q": text
    }
    r = requests.get(url, params=params)
    result = r.json()
    return "".join([item[0] for item in result[0]])

# =====================
# 日本語要約（400字以内）
# =====================
def summarize_japanese(text, limit=400):
    text = text.replace("\n", " ").strip()

    # ★ 重要：翻訳前に強制短縮
    text = text[:800]

    translated = translate_to_japanese(text)
    return translated[:limit] + ("…" if len(translated) > limit else "")


# =====================
# Quantum Insider
# =====================
def fetch_quantum_insider():
    base = "https://thequantuminsider.com"
    results = []

    for path in ["/news/", "/resources/"]:
        r = requests.get(base + path, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        for article in soup.select("article"):
            a_tag = article.find("a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            if not link.startswith("http"):
                link = base + link

            if is_duplicate(title, link):
                continue

            content = requests.get(link, headers=HEADERS)
            content_soup = BeautifulSoup(content.text, "html.parser")
            body = content_soup.get_text(" ", strip=True)

            summary = summarize_japanese(body)

            date_tag = content_soup.find("time")
            date = date_tag.get_text(strip=True) if date_tag else ""

            results.append({
                "title": title,
                "url": link,
                "summary": summary,
                "date": date
            })

    return results

# =====================
# Quantinuum
# =====================
def fetch_quantinuum():
    base = "https://www.quantinuum.com"
    results = []

    for path in ["/press-releases", "/blog"]:
        r = requests.get(base + path, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a[href^='/']"):
            title = a.get_text(strip=True)
            if not title:
                continue

            link = base + a["href"]

            if is_duplicate(title, link):
                continue

            article = requests.get(link, headers=HEADERS)
            article_soup = BeautifulSoup(article.text, "html.parser")
            body = article_soup.get_text(" ", strip=True)

            summary = summarize_japanese(body)

            date_tag = article_soup.find("time")
            date = date_tag.get_text(strip=True) if date_tag else ""

            results.append({
                "title": title,
                "url": link,
                "summary": summary,
                "date": date
            })

    return results

# =====================
# メール送信
# =====================
def send_email(articles):
    if not articles:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "【量子技術ニュース】最新情報"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    html = "<html><body><h2>本日の量子技術ニュース</h2><ul>"
    for a in articles:
        html += f"""
        <li>
            <a href="{a['url']}">{a['title']}</a><br>
            {a['summary']}<br>
            <small>{a['date']}</small>
        </li><br>
        """
    html += "</ul></body></html>"

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.send_message(msg)

# =====================
# メイン処理
# =====================
def main():
    articles = []
    articles += fetch_quantum_insider()
    articles += fetch_quantinuum()

    print(f"DEBUG: article count = {len(articles)}")

    send_email(articles)

    for a in articles:
        sent_articles.append({
            "title": a["title"],
            "url": a["url"]
        })

    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
