"""Publish one machine-owned snapshot to a stable Drive file ID.

This is Google OAuth, not Blueprint OAuth. Live credentials are required.
Only this script should write the published file. Tutor memory belongs elsewhere.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from study_sync import atomic_json

SCOPE = "https://www.googleapis.com/auth/drive.file"


def credentials(client_path, profile, interactive):
    import keyring
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    client = json.loads(client_path.read_text(encoding="utf-8"))
    if "installed" not in client:
        raise ValueError("use a Google Desktop app OAuth client")
    account_key = hashlib.sha256((client["installed"]["client_id"] + profile).encode()).hexdigest()
    raw = keyring.get_password("blueprint-study-drive", account_key)
    creds = Credentials.from_authorized_user_info(json.loads(raw), [SCOPE]) if raw else None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            if not interactive:
                raise RuntimeError("Google authorization expired or was revoked; rerun with --authorize") from None
            creds = None
    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError("Google sign-in required: run once with --authorize interactively")
        flow = InstalledAppFlow.from_client_config(client, [SCOPE], autogenerate_code_verifier=True)
        creds = flow.run_local_server(host="127.0.0.1", port=0, open_browser=True,
                                     timeout_seconds=180, access_type="offline", prompt="consent")
    keyring.set_password("blueprint-study-drive", account_key, creds.to_json())
    return creds


def publish(service, path, mapping_path):
    from googleapiclient.http import MediaIoBaseUpload

    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or snapshot.get("product") != "MCAT":
        raise ValueError("publish the output of study_sync.py export")
    learner = snapshot["learner_id"]
    local = json.loads(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {}
    if local and local.get("learner_id") != learner:
        raise ValueError("Drive mapping belongs to a different learner")
    owner_key = hashlib.sha256(learner.encode()).hexdigest()
    file_id = local.get("file_id")
    props = {"application": "blueprint-study-v1", "learner_key": owner_key}
    if not file_id:
        # Recover after a successful create followed by a local crash; avoid name-based duplicates.
        q = "trashed=false and appProperties has { key='application' and value='blueprint-study-v1' }"
        q += " and appProperties has { key='learner_key' and value='" + owner_key + "' }"
        found = service.files().list(q=q, fields="files(id),nextPageToken", pageSize=100).execute()
        if len(found.get("files", [])) > 1 or found.get("nextPageToken"):
            raise RuntimeError("multiple owned snapshots found; resolve the correct file before publishing")
        if found.get("files"):
            file_id = found["files"][0]["id"]
    media = MediaIoBaseUpload(io.BytesIO(path.read_bytes()), mimetype="application/json", resumable=True)
    if file_id:
        remote = service.files().get(fileId=file_id, fields="id,trashed,appProperties").execute()
        if remote.get("trashed") or remote.get("appProperties") != props:
            raise RuntimeError("refusing to overwrite a file not owned by this publisher")
        result = service.files().update(fileId=file_id, media_body=media,
                                        fields="id,name,webViewLink,modifiedTime").execute()
    else:
        result = service.files().create(body={"name": "MCAT_Study_State.json", "appProperties": props},
                                        media_body=media, fields="id,name,webViewLink,modifiedTime").execute()
    atomic_json(mapping_path, {"learner_id": learner, "file_id": result["id"]})
    return result


def main():
    from googleapiclient.discovery import build

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("snapshot", type=Path)
    p.add_argument("--client", type=Path, required=True)
    p.add_argument("--mapping", type=Path, default=Path("private/drive_mapping.json"))
    p.add_argument("--profile", default="default", help="distinct credential profile per Google account")
    p.add_argument("--authorize", action="store_true", help="allow interactive Google login")
    a = p.parse_args()
    creds = credentials(a.client, a.profile, a.authorize)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    print(json.dumps(publish(service, a.snapshot, a.mapping), indent=2))


if __name__ == "__main__":
    main()
