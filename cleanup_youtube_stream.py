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


def get_broadcast_status(token, broadcast_id):
    resp = requests.get(
        f"{API_BASE}/liveBroadcasts",
        params={"id": broadcast_id, "part": "status"},
        headers={"Authorization": f"Bearer {token}"},
    )
    _raise_with_body(resp)
    items = resp.json().get("items", [])
    if not items:
        return None
    return items[0]["status"]["lifeCycleStatus"]


def wait_for_broadcast_complete(token, broadcast_id):
    delays = [0, 15, 30, 60, 60, 60]
    for i, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        status = get_broadcast_status(token, broadcast_id)
        print(f"Broadcast status check {i + 1}: {status}", file=sys.stderr)
        if status == "complete":
            return True
    return False


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
    broadcast_id = read_id("yt_broadcast_id.txt")

    if not stream_id:
        print("No stream id file found, nothing to clean up.", file=sys.stderr)
        return

    token = get_access_token()

    if broadcast_id:
        wait_for_broadcast_complete(token, broadcast_id)

    delete_stream(token, stream_id)
    print(f"Deleted stream {stream_id}", file=sys.stderr)


if __name__ == "__main__":
    main()
