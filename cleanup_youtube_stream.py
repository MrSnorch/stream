import sys
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
    resp = requests.post(TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    })
    _raise_with_body(resp)
    return resp.json()["access_token"]


def delete_stream(token, stream_id):
    resp = requests.delete(
        f"{API_BASE}/liveStreams",
        params={"id": stream_id},
        headers={"Authorization": f"Bearer {token}"},
    )
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
