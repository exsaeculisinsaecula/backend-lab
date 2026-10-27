"""CRUD 스모크 테스트 — python backend/smoke_test.py"""
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

    # health
    s, b = req("GET", "/api/health")
    assert s == 200 and b["status"] == "ok", (s, b)
    print("✓ health")
    ok += 1

    # categories list
    s, cats = req("GET", "/api/categories")
    assert s == 200 and len(cats) == 8, (s, len(cats))
    print(f"✓ categories list ({len(cats)})")
    ok += 1

    # concept create / read / update / delete
    s, c = req("POST", "/api/concepts", {
        "category_id": "http",
        "term": "스모크 테스트 용어",
        "definition": "스모크 테스트 정의",
        "example": "예시 문장",
    })
    assert s == 201, (s, c)
    cid = c["id"]
    print(f"✓ concept create ({cid})")
    ok += 1

    s, c = req("GET", f"/api/concepts/{cid}")
    assert s == 200 and c["term"] == "스모크 테스트 용어", (s, c)
    print("✓ concept read")
    ok += 1

    s, c = req("PATCH", f"/api/concepts/{cid}", {"is_known": True, "term": "수정된 용어"})
    assert s == 200 and c["is_known"] is True and c["term"] == "수정된 용어", (s, c)
    print("✓ concept update")
    ok += 1

    s, _ = req("DELETE", f"/api/concepts/{cid}")
    assert s == 204, s
    s, _ = req("GET", f"/api/concepts/{cid}")
    assert s == 404, s
    print("✓ concept delete")
    ok += 1

    # quiz create / list / update / delete
    s, q = req("POST", "/api/quiz", {
        "category_id": "db",
        "question": "스모크 퀴즈 문제",
        "choices": ["선택1", "선택2", "선택3"],
        "correct_index": 1,
        "explanation": "해설",
    })
    assert s == 201, (s, q)
    qid = q["id"]
    assert q["choices"] == ["선택1", "선택2", "선택3"]
    print(f"✓ quiz create ({qid})")
    ok += 1

    s, q = req("PATCH", f"/api/quiz/{qid}", {"correct_index": 2})
    assert s == 200 and q["correct_index"] == 2, (s, q)
    print("✓ quiz update")
    ok += 1

    s, _ = req("DELETE", f"/api/quiz/{qid}")
    assert s == 204, s
    print("✓ quiz delete")
    ok += 1

    # wrong answer create (upsert) / update / delete
    s, w = req("POST", "/api/wrong-answers", {
        "source_id": "q1",
        "category_id": "http",
        "question_type": "심화",
        "question": "틀린 문제",
        "choices": ["A", "B", "C"],
        "correct_index": 0,
        "my_index": 1,
        "explanation": "왜 틀렸나",
    })
    assert s == 201, (s, w)
    wid = w["id"]
    print(f"✓ wrong create ({wid})")
    ok += 1

    # duplicate upsert increments count
    s, w2 = req("POST", "/api/wrong-answers", {
        "source_id": "q1",
        "category_id": "http",
        "question_type": "심화",
        "question": "틀린 문제",
        "choices": ["A", "B", "C"],
        "correct_index": 0,
        "my_index": 2,
        "explanation": "왜 틀렸나",
    })
    assert s == 201 and w2["id"] == wid and w2["count"] == 2 and w2["my_index"] == 2, (s, w2)
    print("✓ wrong upsert")
    ok += 1

    s, w = req("PATCH", f"/api/wrong-answers/{wid}", {"mastered": True})
    assert s == 200 and w["mastered"] is True, (s, w)
    print("✓ wrong update")
    ok += 1

    s, _ = req("DELETE", f"/api/wrong-answers/{wid}")
    assert s == 204, s
    print("✓ wrong delete")
    ok += 1

    # progress upsert + stats
    s, p = req("PUT", "/api/progress", {"date": "2026-10-27", "answered": 5, "correct": 4})
    assert s == 200 and p["answered"] == 5, (s, p)
    print("✓ progress upsert")
    ok += 1

    s, st = req("GET", "/api/stats")
    assert s == 200 and st["total_concepts"] >= 48, (s, st)
    print(f"✓ stats ({st})")
    ok += 1

    s, _ = req("DELETE", "/api/progress/reset")
    assert s == 200, s
    print("✓ progress reset")
    ok += 1

    print(f"\nAll {ok} smoke tests passed.")


if __name__ == "__main__":
    main()
