import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    title = title.strip().lower()
    for a in sent_articles:
        if a["title"].strip().lower() == title:
            return True
    return False

# =====================
# 日本語要約（約200 words 目安）
# =====================
def summarize_japanese(text, max_chars=900):
    """
    約200 words相当の日本語要約（簡易）
    """
    text = text.replace("\n", " ").strip()

    # 余計な空白整理
    while "  " in text:
        text = text.replace("  ", " ")

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "…"

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
            link = a_tag.get("href", "")
            if not link:
                continue

            if not link.startswith("http"):
                link = base + link

            if is_duplicate(title, link):
                continue

            content_r = requests.get(link, headers=HEADERS)
            content_soup = BeautifulSoup(content_r.text, "html.parser")
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
        url = base + path
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        for card in soup.select("a"):
            link = card.get("href", "")
            if not link.startswith("/"):
                continue

            full_url = base + link
            title = card.get_text(strip=True)

            if not title:
                continue

            if is_duplicate(title, full_url):
                continue

            article_r = requests.get(full_url, headers=HEADERS)
            article_soup = BeautifulSoup(article_r.text, "html.parser")
            body = article_soup.get_text(" ", strip=True)

            summary = summarize_japanese(body)

            date_tag = article_soup.find("time")
            date = date_tag.get_text(strip=True) if date_tag else ""

            results.append({
                "title": title,
                "url": full_url,
                "summary": summary,
                "date": date
            })

    return results

# =====================
# メール送信
# =====================
def send_email(articles):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "【量子技術ニュース】本日の最新情報"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    if not articles:
        html = """
        <html><body>
        <h2>本日の量子技術ニュース</h2>
        <p>本日は新規ニュースがありませんでした。</p>
        </body></html>
        """
    else:
        html = "<html><body><h2>本日の量子技術ニュース</h2><ul>"
        for a in articles:
            html += f"""
            <li>
                <a href="{a['url']}"><strong>{a['title']}</strong></a><br>
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
