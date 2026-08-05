import sys
import time
import requests

CLIENT_ID = sys.argv[1]
CLIENT_SECRET = sys.argv[2]
REFRESH_TOKEN = sys.argv[3]
TITLE = sys.argv[4] if len(sys.argv) > 4 else "Live Stream"
DESCRIPTION = sys.argv[5] if len(sys.argv) > 5 else ""
THUMBNAIL = sys.argv[6] if len(sys.argv) > 6 else None

CATEGORY_ID = "20"  # Gaming
LANGUAGE = "en"

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


def create_broadcast(token):
    resp = requests.post(
        f"{API_BASE}/liveBroadcasts",
        params={"part": "snippet,status,contentDetails"},
        headers={"Authorization": f"Bearer {token}"},
        json={
            "snippet": {
                "title": TITLE,
                "description": DESCRIPTION,
                "scheduledStartTime": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            },
            "status": {"privacyStatus": "public"},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": True},
        },
    )
    _raise_with_body(resp)
    return resp.json()["id"]


def create_stream(token):
    resp = requests.post(
        f"{API_BASE}/liveStreams",
        params={"part": "snippet,cdn"},
        headers={"Authorization": f"Bearer {token}"},
        json={
            "snippet": {"title": TITLE},
            "cdn": {
                "frameRate": "variable",
                "ingestionType": "rtmp",
                "resolution": "variable",
            },
        },
    )
    _raise_with_body(resp)
    data = resp.json()
    ingestion = data["cdn"]["ingestionInfo"]
    return data["id"], ingestion["ingestionAddress"], ingestion["streamName"]


def bind_broadcast(token, broadcast_id, stream_id):
    resp = requests.post(
        f"{API_BASE}/liveBroadcasts/bind",
        params={"id": broadcast_id, "part": "id,contentDetails", "streamId": stream_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    _raise_with_body(resp)


def set_thumbnail(token, broadcast_id, path):
    content_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        image_data = f.read()
    resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/thumbnails/set",
        params={"videoId": broadcast_id, "uploadType": "media"},
        headers={"Authorization": f"Bearer {token}", "Content-Type": content_type},
        data=image_data,
    )
    _raise_with_body(resp)


def set_video_metadata(token, video_id):
    body = {
        "id": video_id,
        "snippet": {
            "title": TITLE,
            "description": DESCRIPTION,
            "categoryId": CATEGORY_ID,
            "defaultLanguage": LANGUAGE,
        },
    }
    delays = [0, 2, 4, 8, 16]
    for i, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        resp = requests.put(
            f"{API_BASE}/videos",
            params={"part": "snippet"},
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        if resp.ok:
            return
        print(f"set_video_metadata attempt {i + 1} failed: {resp.status_code}", file=sys.stderr)
    _raise_with_body(resp)


def main():
    token = get_access_token()
    broadcast_id = create_broadcast(token)
    with open("yt_broadcast_id.txt", "w") as f:
        f.write(broadcast_id)

    stream_id, ingestion_address, stream_name = create_stream(token)
    with open("yt_stream_id.txt", "w") as f:
        f.write(stream_id)

    bind_broadcast(token, broadcast_id, stream_id)

    try:
        set_video_metadata(token, broadcast_id)
    except requests.exceptions.HTTPError:
        print("Warning: failed to set category/language, continuing anyway", file=sys.stderr)

    if THUMBNAIL:
        set_thumbnail(token, broadcast_id, THUMBNAIL)

    with open("yt_rtmp_url.txt", "w") as f:
        f.write(f"{ingestion_address}/{stream_name}")

    print(f"Broadcast ID: {broadcast_id}", file=sys.stderr)
    print(f"RTMP target written to yt_rtmp_url.txt", file=sys.stderr)


if __name__ == "__main__":
    main()
