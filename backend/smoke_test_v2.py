"""확장 라우터 스모크 테스트 — python backend/smoke_test_v2.py"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method, path, body=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, (json.loads(raw) if raw else None)


def main():
    ok = 0

    # analytics dashboard
    s, d = req("GET", "/api/analytics/dashboard")
    assert s == 200 and "categories" in d and "weak_areas" in d, (s, d)
    print(f"✓ analytics dashboard (concepts={d['total_concepts']})")
    ok += 1

    s, cats = req("GET", "/api/analytics/categories")
    assert s == 200 and len(cats) >= 8, (s, len(cats))
    print(f"✓ analytics categories ({len(cats)})")
    ok += 1

    s, weak = req("GET", "/api/analytics/weak-areas")
    assert s == 200, (s, weak)
    print(f"✓ analytics weak-areas ({len(weak)})")
    ok += 1

    s, tl = req("GET", "/api/analytics/timeline?days=7")
    assert s == 200, (s, tl)
    print(f"✓ analytics timeline ({len(tl)})")
    ok += 1

    # search
    s, r = req("GET", "/api/search?q=JWT")
    assert s == 200 and r["total"] >= 1, (s, r)
    print(f"✓ search JWT ({r['total']} hits)")
    ok += 1

    # study session
    s, sess = req("POST", "/api/study/sessions", {
        "only_unknown": True,
        "shuffle": True,
        "limit": 5,
    })
    assert s == 201 and sess["total"] >= 1, (s, sess)
    sid = sess["id"]
    print(f"✓ study session create (total={sess['total']})")
    ok += 1

    s, card = req("GET", f"/api/study/sessions/{sid}/current")
    assert s == 200 and card["term"], (s, card)
    print(f"✓ study current card ({card['term']})")
    ok += 1

    s, sess = req("POST", f"/api/study/sessions/{sid}/answer", {"is_known": True})
    assert s == 200 and sess["answered"] == 1, (s, sess)
    print("✓ study answer")
    ok += 1

    s, sess = req("POST", f"/api/study/sessions/{sid}/complete")
    assert s == 200 and sess["is_completed"] is True, (s, sess)
    print("✓ study complete")
    ok += 1

    # quiz generate (no session)
    s, qs = req("POST", "/api/quiz/generate", {"size": 5, "include_advanced": True})
    assert s == 200 and len(qs) >= 3, (s, len(qs))
    assert all("choices" in q and "correct_index" in q for q in qs)
    print(f"✓ quiz generate ({len(qs)} questions)")
    ok += 1

    # quiz game session
    s, gs = req("POST", "/api/quiz/sessions", {"size": 5, "source": "generated"})
    assert s == 201 and gs["total"] >= 1, (s, gs)
    qsid = gs["id"]
    print(f"✓ quiz session create (total={gs['total']})")
    ok += 1

    s, q = req("GET", f"/api/quiz/sessions/{qsid}")
    assert s == 200 and q["current_question"], (s, q)
    print("✓ quiz session get with question")
    ok += 1

    # answer correctly and incorrectly
    cur = q["current_question"]
    s, ar = req("POST", f"/api/quiz/sessions/{qsid}/answer", {"choice_index": cur["correct_index"]})
    assert s == 200 and ar["correct"] is True, (s, ar)
    print("✓ quiz answer correct")
    ok += 1

    wrong_idx = (cur["correct_index"] + 1) % len(cur["choices"])
    if ar.get("next_question"):
        nq = ar["next_question"]
        s, ar2 = req("POST", f"/api/quiz/sessions/{qsid}/answer", {
            "choice_index": (nq["correct_index"] + 1) % len(nq["choices"])
        })
        assert s == 200 and ar2["correct"] is False, (s, ar2)
        print("quiz answer wrong -> wrong-note saved")
        ok += 1

    s, res = req("GET", f"/api/quiz/sessions/{qsid}/result")
    assert s == 200 and "score" in res and "accuracy" in res, (s, res)
    print(f"quiz result score={res['score']}/{res['total']} accuracy={res['accuracy']}")
    ok += 1

    # review queue
    s, rq = req("GET", "/api/review/queue?limit=10")
    assert s == 200, (s, rq)
    print(f"review queue ({len(rq)} items)")
    ok += 1

    s, rs = req("GET", "/api/review/stats")
    assert s == 200 and "queue_size" in rs, (s, rs)
    print(f"review stats {rs}")
    ok += 1

    if rq:
        item = rq[0]
        s, msg = req("POST", "/api/review/complete", {
            "kind": item["kind"],
            "id": item["id"],
            "known": True,
        })
        assert s == 200, (s, msg)
        print(f"review complete ({item['kind']})")
        ok += 1

    # export / import
    s, exp = req("GET", "/api/data/export")
    assert s == 200 and len(exp["concepts"]) >= 40, (s, len(exp["concepts"]))
    print(f"data export ({len(exp['concepts'])} concepts)")
    ok += 1

    s, imp = req("POST", "/api/data/import", {
        "categories": exp["categories"],
        "concepts": exp["concepts"][:2],
    })
    assert s == 201 and imp["skipped"] >= 2, (s, imp)
    print(f"data import skipped={imp['skipped']}")
    ok += 1

    print(f"\nAll {ok} extended smoke tests passed.")


if __name__ == "__main__":
    main()
