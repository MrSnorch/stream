"""
Отправляет сообщение(я) из message.txt в чат YouTube Live.
Чтобы отправить 2 (или больше) сообщения — разделите их в message.txt строкой '---' на отдельной строке.
YouTube Data API не поддерживает закрепление сообщений в чате программно
(нет соответствующего метода в liveChatMessages) — закрепление доступно
только вручную через YouTube Studio.
Использует те же CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN, что и create_youtube_stream.py.
Требует файл yt_live_chat_id.txt, который пишет create_youtube_stream.py.
"""
import sys
import time
import requests

CLIENT_ID = sys.argv[1]
CLIENT_SECRET = sys.argv[2]
REFRESH_TOKEN = sys.argv[3]

MESSAGE_FILE = "message.txt"
LIVE_CHAT_ID_FILE = "yt_live_chat_id.txt"

TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/youtube/v3"


def _raise_with_body(resp):
    if not resp.ok:
        print(f"HTTP {resp.status_code} error body:", file=sys.stderr)
        print(resp.text, file=sys.stderr)
    resp.raise_for_status()


def get_access_token():
    delays = [0, 3, 6]
    for i, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        resp = requests.post(TOKEN_URL, data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        })
        if resp.ok:
            return resp.json()["access_token"]
        print(f"get_access_token attempt {i + 1} failed: {resp.status_code}", file=sys.stderr)
    _raise_with_body(resp)


def send_message(token, live_chat_id, message):
    resp = requests.post(
        f"{API_BASE}/liveChat/messages",
        params={"part": "snippet"},
        headers={"Authorization": f"Bearer {token}"},
        json={
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": message},
            },
        },
    )
    _raise_with_body(resp)
    return resp.json()


def load_messages():
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    parts = [p.strip() for p in content.split("\n---\n")]
    return [p for p in parts if p]


def main():
    messages = load_messages()
    if not messages:
        print("message.txt пуст, нечего отправлять", file=sys.stderr)
        sys.exit(1)

    with open(LIVE_CHAT_ID_FILE) as f:
        live_chat_id = f.read().strip()

    token = get_access_token()

    for i, message in enumerate(messages):
        try:
            send_message(token, live_chat_id, message)
        except requests.HTTPError as e:
            print(f"Сообщение {i + 1}/{len(messages)} НЕ отправлено: {message!r}", file=sys.stderr)
            print(f"Ошибка YouTube: {e.response.status_code} {e.response.text}", file=sys.stderr)
            continue
        print(f"Сообщение {i + 1}/{len(messages)} отправлено: {message!r}")


if __name__ == "__main__":
    main()
