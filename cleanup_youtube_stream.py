import sys
import time
import requests

CLIENT_ID = sys.argv[1]
CLIENT_SECRET = sys.argv[2]
REFRESH_TOKEN = sys.argv[3]

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


def delete_stream(token, stream_id):
    delays = [0, 15, 30, 60, 120]
    for i, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        resp = requests.delete(
            f"{API_BASE}/liveStreams",
            params={"id": stream_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.ok:
            return
        print(f"delete_stream attempt {i + 1} failed: {resp.status_code}", file=sys.stderr)
        print(resp.text, file=sys.stderr)
    _raise_with_body(resp)


def read_id(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def main():
    stream_id = read_id("yt_stream_id.txt")

    if not stream_id:
        print("No stream id file found, nothing to clean up.", file=sys.stderr)
        return

    token = get_access_token()
    delete_stream(token, stream_id)
    print(f"Deleted stream {stream_id}", file=sys.stderr)


if __name__ == "__main__":
    main()
