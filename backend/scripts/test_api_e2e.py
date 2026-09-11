"""Test E2E Etape 3 — API complete via TestClient (pas de serveur requis).

Couvre : /health, /api/info (OK + URL invalide), /api/jobs (clip trop long -> 400),
job valide -> polling -> /api/download -> MP4, quota consomme.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app

YT = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
client = TestClient(app)
passed, failed = [], []


def check(name, fn):
    try:
        fn()
        passed.append(name)
        print(f"  [OK] {name}")
    except Exception as e:  # noqa: BLE001
        failed.append(name)
        print(f"  [KO] {name} : {type(e).__name__}: {str(e)[:300]}")


def t_health():
    r = client.get("/health")
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True


def t_info():
    r = client.post("/api/info", json={"url": YT})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True, body
    assert body["data"]["duration"] > 600, body["data"]
    title = body["data"]["title"]
    assert "Blender" in title or "Buck" in title, body["data"]


def t_info_bad():
    r = client.post("/api/info", json={"url": "https://example.com/video"})
    body = r.json()
    assert body["ok"] is False and "error" in body, body


def t_job_toolong():
    r = client.post("/api/jobs", json={"url": YT, "start": 0, "end": 9999})
    assert r.status_code == 400, (r.status_code, r.text[:200])


job_id: dict = {}


def t_job_create():
    r = client.post("/api/jobs", json={"url": YT, "start": 10, "end": 25})
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body["ok"] is True and body["job_id"], body
    job_id["id"] = body["job_id"]
    print(f"      job_id={job_id['id']} quota={body.get('quota')}")


print("[1] GET /health")
check("health", t_health)
print("[2] POST /api/info (YouTube)")
check("info-youtube", t_info)
print("[3] POST /api/info (URL invalide)")
check("info-invalide", t_info_bad)
print("[4] POST /api/jobs (clip trop long -> 400)")
check("job-trop-long", t_job_toolong)
print("[5] POST /api/jobs (10s -> 25s) + polling + download")
check("job-create", t_job_create)

final = None
if job_id.get("id"):
    jid = job_id["id"]
    deadline = time.time() + 420
    while time.time() < deadline:
        r = client.get(f"/api/jobs/{jid}")
        assert r.status_code == 200, r.text[:200]
        st = r.json()
        print(f"      status={st['status']} progress={st.get('progress')}")
        if st["status"] in ("done", "error"):
            final = st
            break
        time.sleep(10)


def t_job_done():
    assert final is not None, "timeout: job jamais termine"
    assert final["status"] == "done", final


def t_download():
    assert final and final["status"] == "done"
    r = client.get(f"/api/download/{job_id['id']}")
    assert r.status_code == 200, (r.status_code, r.text[:200] if len(r.content) < 500 else "")
    assert "video/mp4" in r.headers.get("content-type", ""), dict(r.headers)
    assert len(r.content) > 1_000_000, f"fichier suspect: {len(r.content)} octets"
    print(f"      MP4 = {len(r.content) / 1e6:.1f} Mo")


check("job-done", t_job_done)
if final and final["status"] == "done":
    check("download-mp4", t_download)


def t_quota():
    r = client.get("/api/quota")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["used"] >= 1, body  # le job ci-dessus a consomme 1 unite


print("[6] GET /api/quota")
check("quota-consomme", t_quota)

print(f"\nResultat : {len(passed)} OK / {len(failed)} KO")
sys.exit(1 if failed else 0)
