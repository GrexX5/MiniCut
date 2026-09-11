"""Test Etape 5 — quotas, rate-limit, nettoyage (sans telechargement)."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app
from app.services import quotas
from app.utils import cleanup

client = TestClient(app, raise_server_exceptions=False)
passed, failed = [], []


def check(name, fn):
    try:
        fn()
        passed.append(name)
        print(f"  [OK] {name}")
    except Exception as e:  # noqa: BLE001
        failed.append(name)
        print(f"  [KO] {name} : {type(e).__name__}: {str(e)[:300]}")


print("[1] Quota anonyme epuise -> 429 via API")
def t_quota_429():
    # Sature le quota du jour pour la cle testclient (robuste au changement de jour),
    # puis verifie que l'API refuse avec 429 SANS lancer de telechargement.
    for _ in range(3):
        ok, _, _ = quotas.check_and_consume_quota("ip:testclient", False)
        if not ok:
            break
    r = client.post(
        "/api/jobs",
        json={"url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ", "start": 0, "end": 5},
    )
    assert r.status_code == 429, (r.status_code, r.text[:200])
check("quota-anon-429", t_quota_429)

print("[2] Logique quotas (cles jetables, sans download)")
def t_quota_logic():
    stamp = str(int(time.time()))
    ok, used, limit = quotas.check_and_consume_quota(f"ip:e2e-fake-{stamp}", False)
    assert (ok, used, limit) == (True, 1, 1), (ok, used, limit)
    ok2, used2, _ = quotas.check_and_consume_quota(f"ip:e2e-fake-{stamp}", False)
    assert ok2 is False and used2 == 1, (ok2, used2)
    oka, useda, limita = quotas.check_and_consume_quota(f"user:e2e-fake-{stamp}", True)
    assert oka is True and limita == 10, (oka, useda, limita)
check("quota-logic", t_quota_logic)

print("[3] Header x-user-id -> quota etendu via API")
def t_user_quota():
    r = client.get("/api/quota", headers={"x-user-id": "e2e-clerk-1"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["limit"] == 10 and body["authenticated"] is True, body
check("quota-user-header", t_user_quota)

print("[4] Rafale /api/info -> 429 rate-limit")
def t_ratelimit():
    codes = [
        client.post("/api/info", json={"url": "https://example.com/x"}).status_code
        for _ in range(15)
    ]
    n429 = sum(1 for c in codes if c == 429)
    assert n429 >= 1, codes
    print(f"      codes={codes}")
check("rate-limit", t_ratelimit)

print("[5] Nettoyage auto (TTL)")
def t_cleanup():
    from app.config import get_settings
    tmp = get_settings().tmp_path
    p1 = tmp / "e2e_del.txt"
    p1.write_text("x")
    cleanup.schedule_deletion(p1, delay=1)
    time.sleep(2.5)
    assert not p1.exists(), "schedule_deletion n'a pas supprime"
    p2 = tmp / "e2e_old.txt"
    p2.write_text("x")
    old = time.time() - 9999
    os.utime(p2, (old, old))
    n = cleanup.purge_expired_tmp(max_age_seconds=60)
    assert n >= 1 and not p2.exists(), n
check("cleanup-ttl", t_cleanup)

print(f"\nResultat : {len(passed)} OK / {len(failed)} KO")
sys.exit(1 if failed else 0)
