from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Concept, QuizQuestion, User, WrongAnswer
from app.schemas.study import SearchHit, SearchOut


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _score(text: str, query: str) -> float:
        t = text.lower()
        q = query.lower()
        if t == q:
            return 3.0
        if t.startswith(q):
            return 2.0
        if q in t:
            return 1.0
        tokens = [x for x in q.split() if x]
        if tokens and all(tok in t for tok in tokens):
            return 0.5
        return 0.0

    def search(self, user: User, q: str, *, limit: int = 20) -> SearchOut:
        query = (q or "").strip()
        if not query:
            return SearchOut(query=q, total=0, hits=[])

        hits: list[SearchHit] = []

        for c in self.db.query(Concept).all():
            s = max(
                self._score(c.term, query),
                self._score(c.definition, query) * 0.6,
            )
            if s > 0:
                hits.append(
                    SearchHit(
                        kind="concept",
                        id=c.id,
                        title=c.term,
                        snippet=c.definition[:120],
                        category_id=c.category_id,
                        score=s,
                    )
                )

        for row in self.db.query(QuizQuestion).all():
            s = self._score(row.question, query) * 0.8
            if s > 0:
                hits.append(
                    SearchHit(
                        kind="quiz",
                        id=row.id,
                        title=row.question[:80],
                        snippet=row.explanation[:120] if row.explanation else "",
                        category_id=row.category_id,
                        score=s,
                    )
                )

        for w in self.db.query(WrongAnswer).filter(WrongAnswer.user_id == user.id).all():
            s = self._score(w.question, query) * 0.7
            if s > 0:
                hits.append(
                    SearchHit(
                        kind="wrong",
                        id=w.id,
                        title=w.question[:80],
                        snippet=w.explanation[:120] if w.explanation else "",
                        category_id=w.category_id,
                        score=s,
                    )
                )

        hits.sort(key=lambda h: h.score, reverse=True)
        hits = hits[:limit]
        return SearchOut(query=query, total=len(hits), hits=hits)
