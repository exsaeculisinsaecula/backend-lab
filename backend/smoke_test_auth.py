"""JWT 인증 + 사용자 격리 스모크 테스트"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method, path, body=None, token=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, (json.loads(raw) if raw else None)
        except Exception:
            return e.code, {"detail": raw.decode("utf-8", errors="replace")[:200]}


def main():
    ok = 0
    ts = __import__("time").time()
    email_a = f"a{int(ts)}@test.com"
    email_b = f"b{int(ts)}@test.com"

    # health public
    s, h = req("GET", "/api/health", token=None)
    assert s == 200, (s, h)
    print("✓ health public (no auth)")
    ok += 1

    # register A
    s, r = req("POST", "/api/auth/register", {
        "email": email_a, "username": "alice", "password": "secret12"
    }, token=None)
    assert s == 201 and r.get("access_token"), (s, r)
    token_a = r["access_token"]
    user_a = r["user"]["id"]
    print(f"✓ register alice ({user_a})")
    ok += 1

    # register B
    s, r = req("POST", "/api/auth/register", {
        "email": email_b, "username": "bob", "password": "secret12"
    }, token=None)
    assert s == 201 and r.get("access_token"), (s, r)
    token_b = r["access_token"]
    user_b = r["user"]["id"]
    print(f"✓ register bob ({user_b})")
    ok += 1

    # login
    s, r = req("POST", "/api/auth/login", {
        "email": email_a, "password": "secret12"
    }, token=None)
    assert s == 200 and r["access_token"], (s, r)
    print("✓ login")
    ok += 1

    # bad login
    s, r = req("POST", "/api/auth/login", {
        "email": email_a, "password": "wrong"
    }, token=None)
    assert s == 401, (s, r)
    print("✓ login rejected wrong password")
    ok += 1

    # me
    s, r = req("GET", "/api/auth/me", token=token_a)
    assert s == 200 and r["email"] == email_a, (s, r)
    print("✓ me")
    ok += 1

    # protected without token
    s, r = req("GET", "/api/concepts")
    assert s == 401, (s, r)
    print("✓ concepts blocked without token")
    ok += 1

    # list concepts with token
    s, concepts = req("GET", "/api/concepts", token=token_a)
    assert s == 200 and len(concepts) >= 10, (s, len(concepts or []))
    print(f"✓ concepts list ({len(concepts)})")
    ok += 1

    cid = concepts[0]["id"]
    assert concepts[0]["is_known"] is False

    # mark known for A
    s, c = req("POST", f"/api/concepts/{cid}/mark?is_known=true", token=token_a)
    assert s == 200 and c["is_known"] is True, (s, c)
    print("✓ mark concept known (alice)")
    ok += 1

    # B still not known
    s, concepts_b = req("GET", "/api/concepts", token=token_b)
    b_known = next(x for x in concepts_b if x["id"] == cid)
    assert b_known["is_known"] is False, b_known
    print("✓ known state isolated per user")
    ok += 1

    # study session for A
    s, sess = req("POST", "/api/study/sessions", {
        "only_unknown": True, "limit": 3
    }, token=token_a)
    assert s == 201 and sess["total"] >= 1, (s, sess)
    sid = sess["id"]
    print(f"✓ study session A ({sid})")
    ok += 1

    # B cannot access A's session
    s, r = req("GET", f"/api/study/sessions/{sid}", token=token_b)
    assert s == 403, (s, r)
    print("✓ study session forbidden for other user")
    ok += 1

    # quiz session for A + wrong answer
    s, gs = req("POST", "/api/quiz/sessions", {"size": 3, "source": "generated"}, token=token_a)
    assert s == 201 and gs["current_question"], (s, gs)
    qsid = gs["id"]
    q = gs["current_question"]
    wrong = (q["correct_index"] + 1) % len(q["choices"])
    s, ar = req("POST", f"/api/quiz/sessions/{qsid}/answer", {"choice_index": wrong}, token=token_a)
    assert s == 200 and ar["correct"] is False, (s, ar)
    print("✓ quiz wrong answer saved")
    ok += 1

    # A has wrong answers, B has none
    s, wa = req("GET", "/api/wrong-answers", token=token_a)
    s2, wb = req("GET", "/api/wrong-answers", token=token_b)
    assert s == 200 and len(wa) >= 1
    assert s2 == 200 and len(wb) == 0, (len(wb), wb)
    print(f"✓ wrong answers isolated (A={len(wa)}, B={len(wb)})")
    ok += 1

    # B cannot patch A's wrong answer
    wid = wa[0]["id"]
    s, r = req("PATCH", f"/api/wrong-answers/{wid}", {"mastered": True}, token=token_b)
    assert s == 403, (s, r)
    print("✓ wrong answer patch forbidden for other user")
    ok += 1

    # analytics per user
    s, da = req("GET", "/api/analytics/dashboard", token=token_a)
    s2, db = req("GET", "/api/analytics/dashboard", token=token_b)
    assert s == 200 and da["open_wrong"] >= 1
    assert s2 == 200 and db["open_wrong"] == 0
    print(f"✓ dashboard isolated (A open_wrong={da['open_wrong']}, B={db['open_wrong']})")
    ok += 1

    # export only own data
    s, exp = req("GET", "/api/data/export", token=token_b)
    assert s == 200 and len(exp["wrong_answers"]) == 0, exp
    print("✓ export scoped to user")
    ok += 1

    # invalid token
    s, r = req("GET", "/api/concepts", token="bad.token.here")
    assert s == 401, (s, r)
    print("✓ invalid token rejected")
    ok += 1

    print(f"\nAll {ok} auth isolation tests passed.")


if __name__ == "__main__":
    main()
