from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Concept,
    QuizQuestion,
    QuizSession,
    QuizSessionAnswer,
    StudySession,
    StudySessionAnswer,
)
from app.schemas.study import StudyAnswerIn, StudyCardOut, StudySessionCreate, StudySessionOut


def _now() -> datetime:
    return datetime.now(timezone.utc)


class StudyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _filter_concepts(self, payload: StudySessionCreate) -> list[Concept]:
        query = self.db.query(Concept)
        if payload.category_id:
            query = query.filter(Concept.category_id == payload.category_id)
        if payload.only_unknown:
            query = query.filter(Concept.is_known.is_(False))
        if payload.only_known:
            query = query.filter(Concept.is_known.is_(True))
        items = query.order_by(Concept.term).all()
        if payload.shuffle:
            random.shuffle(items)
        return items[: payload.limit]

    def _card(self, concept: Concept, index: int, total: int) -> StudyCardOut:
        return StudyCardOut(
            index=index,
            total=total,
            concept_id=concept.id,
            term=concept.term,
            definition=concept.definition,
            example=concept.example,
            category_id=concept.category_id,
            is_known=concept.is_known,
        )

    def _to_out(self, session: StudySession, with_card: bool = True) -> StudySessionOut:
        concept_ids = json.loads(session.concept_ids_json or "[]")
        total = len(concept_ids)
        answers = session.answers or []
        known = sum(1 for a in answers if a.is_known)
        unknown = len(answers) - known

        current_card = None
        if with_card and not session.is_completed and session.current_index < total:
            concept = self.db.get(Concept, concept_ids[session.current_index])
            if concept:
                current_card = self._card(concept, session.current_index, total)

        meta = json.loads(session.filter_json or "{}")
        return StudySessionOut(
            id=session.id,
            category_id=meta.get("category_id"),
            current_index=session.current_index,
            total=total,
            answered=len(answers),
            known=known,
            unknown=unknown,
            is_completed=session.is_completed,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_card=current_card,
        )

    def create_session(self, payload: StudySessionCreate) -> StudySession:
        concepts = self._filter_concepts(payload)
        session = StudySession(
            id=f"ss-{uuid.uuid4().hex[:12]}",
            filter_json=json.dumps(payload.model_dump(), ensure_ascii=False),
            concept_ids_json=json.dumps([c.id for c in concepts]),
            current_index=0,
            is_completed=len(concepts) == 0,
            started_at=_now(),
            completed_at=_now() if not concepts else None,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, *, limit: int = 20) -> list[StudySession]:
        return (
            self.db.query(StudySession)
            .order_by(StudySession.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_session(self, session_id: str) -> StudySession | None:
        return self.db.get(StudySession, session_id)

    def to_out(self, session: StudySession, with_card: bool = True) -> StudySessionOut:
        return self._to_out(session, with_card=with_card)

    def current_card(self, session: StudySession) -> StudyCardOut | None:
        return self._to_out(session).current_card

    def answer(self, session: StudySession, payload: StudyAnswerIn) -> StudySession:
        if session.is_completed:
            return session
        concept_ids = json.loads(session.concept_ids_json or "[]")
        if session.current_index >= len(concept_ids):
            session.is_completed = True
            session.completed_at = _now()
            self.db.commit()
            return session

        concept_id = concept_ids[session.current_index]
        concept = self.db.get(Concept, concept_id)
        if concept:
            concept.is_known = payload.is_known

        self.db.add(
            StudySessionAnswer(
                session_id=session.id,
                concept_id=concept_id,
                is_known=payload.is_known,
                answered_at=_now(),
            )
        )
        session.current_index += 1
        if session.current_index >= len(concept_ids):
            session.is_completed = True
            session.completed_at = _now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def complete(self, session: StudySession) -> StudySession:
        session.is_completed = True
        session.completed_at = _now()
        self.db.commit()
        self.db.refresh(session)
        return session


class QuizGameService:
    """개념 카드 + 심화 문항으로 퀴즈를 생성하고 세션을 진행한다."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _choices_from(items: list[str], correct: str) -> tuple[list[str], int]:
        pool = list(dict.fromkeys(items))
        if correct not in pool:
            pool = [correct, *pool]
        random.shuffle(pool)
        return pool, pool.index(correct)

    def generate_questions(
        self,
        *,
        size: int = 10,
        category_id: str | None = None,
        include_advanced: bool = True,
        shuffle: bool = True,
    ) -> list[dict]:
        concept_query = self.db.query(Concept)
        if category_id:
            concept_query = concept_query.filter(Concept.category_id == category_id)
        concepts = concept_query.all()

        adv_query = self.db.query(QuizQuestion)
        if category_id:
            adv_query = adv_query.filter(QuizQuestion.category_id == category_id)
        advanced = adv_query.all() if include_advanced else []

        questions: list[dict] = []

        # 심화 문항 최대 40%
        adv_count = min(len(advanced), max(1 if advanced else 0, int(size * 0.4)))
        picked_adv = random.sample(advanced, k=min(adv_count, len(advanced))) if advanced else []
        for row in picked_adv:
            questions.append(
                {
                    "key": row.id,
                    "type": "advanced",
                    "question": row.question,
                    "choices": json.loads(row.choices_json),
                    "correct_index": row.correct_index,
                    "explanation": row.explanation,
                    "category_id": row.category_id,
                }
            )

        # 개념 기반 선다형
        need = max(0, size - len(questions))
        picked_concepts = random.sample(concepts, k=min(need, len(concepts))) if concepts else []
        modes = ["def", "term", "def"]
        for i, concept in enumerate(picked_concepts):
            others = [c for c in concepts if c.id != concept.id]
            if len(others) < 3:
                continue
            distractors = random.sample(others, k=3)
            mode = modes[i % len(modes)]
            if mode == "term":
                correct = concept.term
                options = [d.term for d in distractors]
                question = f"다음 정의에 해당하는 용어는?\n\n\"{concept.definition}\""
            else:
                correct = concept.definition
                options = [d.definition for d in distractors]
                question = f"\"{concept.term}\"의 올바른 정의는?"
            choices, correct_index = self._choices_from([correct, *options], correct)
            questions.append(
                {
                    "key": f"auto-{mode}-{concept.id}",
                    "type": f"concept-{mode}",
                    "question": question,
                    "choices": choices,
                    "correct_index": correct_index,
                    "explanation": concept.example or concept.definition,
                    "category_id": concept.category_id,
                }
            )

        if shuffle:
            random.shuffle(questions)
        return questions[:size]

    def generate_wrong_questions(self, *, size: int | None = None) -> list[dict]:
        from app.models import WrongAnswer

        rows = (
            self.db.query(WrongAnswer)
            .filter(WrongAnswer.mastered.is_(False))
            .order_by(WrongAnswer.updated_at.desc())
            .all()
        )
        if size:
            rows = rows[:size]
        questions = []
        for row in rows:
            questions.append(
                {
                    "key": f"wrong-{row.id}",
                    "type": "wrong",
                    "question": row.question,
                    "choices": json.loads(row.choices_json),
                    "correct_index": row.correct_index,
                    "explanation": row.explanation,
                    "category_id": row.category_id,
                }
            )
        return questions

    def create_session(
        self,
        *,
        source: str = "generated",
        size: int = 10,
        category_id: str | None = None,
        include_advanced: bool = True,
    ) -> QuizSession:
        if source == "wrong":
            questions = self.generate_wrong_questions(size=size or None)
        elif source == "db":
            rows = self.db.query(QuizQuestion)
            if category_id:
                rows = rows.filter(QuizQuestion.category_id == category_id)
            rows = rows.limit(size).all()
            questions = [
                {
                    "key": r.id,
                    "type": "advanced",
                    "question": r.question,
                    "choices": json.loads(r.choices_json),
                    "correct_index": r.correct_index,
                    "explanation": r.explanation,
                    "category_id": r.category_id,
                }
                for r in rows
            ]
            random.shuffle(questions)
        else:
            questions = self.generate_questions(
                size=size,
                category_id=category_id,
                include_advanced=include_advanced,
            )

        session = QuizSession(
            id=f"qs-{uuid.uuid4().hex[:12]}",
            source=source,
            filter_json=json.dumps(
                {
                    "size": size,
                    "category_id": category_id,
                    "include_advanced": include_advanced,
                },
                ensure_ascii=False,
            ),
            questions_json=json.dumps(questions, ensure_ascii=False),
            current_index=0,
            score=0,
            is_completed=len(questions) == 0,
            started_at=_now(),
            completed_at=_now() if not questions else None,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> QuizSession | None:
        return self.db.get(QuizSession, session_id)

    def list_sessions(self, *, limit: int = 20) -> list[QuizSession]:
        return (
            self.db.query(QuizSession)
            .order_by(QuizSession.started_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def questions_of(session: QuizSession) -> list[dict]:
        return json.loads(session.questions_json or "[]")

    def question_at(self, session: QuizSession, index: int) -> dict | None:
        questions = self.questions_of(session)
        if 0 <= index < len(questions):
            return questions[index]
        return None

    def to_out(self, session: QuizSession) -> dict:
        questions = self.questions_of(session)
        total = len(questions)
        current = self.question_at(session, session.current_index)
        answered = len(session.answers or [])
        accuracy = round(session.score / total * 100, 2) if total else None
        current_question = None
        if current and not session.is_completed:
            current_question = {
                "key": current["key"],
                "type": current.get("type", ""),
                "question": current["question"],
                "choices": current["choices"],
                "correct_index": current["correct_index"],
                "explanation": current.get("explanation", ""),
                "category_id": current.get("category_id", ""),
            }
        return {
            "id": session.id,
            "source": session.source,
            "current_index": session.current_index,
            "total": total,
            "score": session.score,
            "answered": answered,
            "is_completed": session.is_completed,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "current_question": current_question,
            "accuracy": accuracy,
        }

    def answer(self, session: QuizSession, choice_index: int) -> dict:
        from app.models import StudyProgress, WrongAnswer

        questions = self.questions_of(session)
        if session.is_completed or session.current_index >= len(questions):
            result = self.to_out(session)
            result["correct"] = False
            result["correct_index"] = -1
            result["selected_index"] = choice_index
            result["explanation"] = "이 세션은 이미 종료되었습니다."
            result["next_question"] = None
            result["is_completed"] = True
            result["accuracy"] = result["accuracy"]
            return result

        q = questions[session.current_index]
        is_correct = choice_index == q["correct_index"]
        if is_correct:
            session.score += 1

        self.db.add(
            QuizSessionAnswer(
                session_id=session.id,
                question_key=q["key"],
                my_index=choice_index,
                correct_index=q["correct_index"],
                is_correct=is_correct,
                answered_at=_now(),
            )
        )

        # 진도 집계
        from datetime import date as _date

        day = _date.today().isoformat()
        progress = self.db.query(StudyProgress).filter(StudyProgress.date == day).first()
        if not progress:
            progress = StudyProgress(date=day, answered=0, correct=0)
            self.db.add(progress)
        progress.answered += 1
        if is_correct:
            progress.correct += 1

        # 오답노트 자동 저장
        if not is_correct:
            self._upsert_wrong(q, choice_index)

        session.current_index += 1
        if session.current_index >= len(questions):
            session.is_completed = True
            session.completed_at = _now()

        self.db.commit()
        self.db.refresh(session)

        next_q = self.question_at(session, session.current_index)
        next_question = None
        if next_q and not session.is_completed:
            next_question = {
                "key": next_q["key"],
                "type": next_q.get("type", ""),
                "question": next_q["question"],
                "choices": next_q["choices"],
                "correct_index": next_q["correct_index"],
                "explanation": next_q.get("explanation", ""),
                "category_id": next_q.get("category_id", ""),
            }

        total = len(questions)
        accuracy = round(session.score / total * 100, 2) if total else None
        return {
            "correct": is_correct,
            "correct_index": q["correct_index"],
            "selected_index": choice_index,
            "explanation": q.get("explanation", ""),
            "score": session.score,
            "total": total,
            "next_question": next_question,
            "is_completed": session.is_completed,
            "accuracy": accuracy,
        }

    def _upsert_wrong(self, q: dict, my_index: int) -> None:
        from app.models import WrongAnswer

        source_id = q["key"]
        existing = (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.source_id == source_id,
                WrongAnswer.question == q["question"],
            )
            .first()
        )
        if existing:
            existing.my_index = my_index
            existing.mastered = False
            existing.count = (existing.count or 1) + 1
            return

        self.db.add(
            WrongAnswer(
                id=f"w-{uuid.uuid4().hex[:12]}",
                source_id=source_id,
                category_id=q.get("category_id", ""),
                question_type=q.get("type", ""),
                question=q["question"],
                choices_json=json.dumps(q["choices"], ensure_ascii=False),
                correct_index=q["correct_index"],
                my_index=my_index,
                explanation=q.get("explanation", ""),
                mastered=False,
                count=1,
            )
        )

    def result(self, session: QuizSession) -> dict:
        questions = self.questions_of(session)
        total = len(questions)
        answered = len(session.answers or [])
        wrong_list = []
        for a in session.answers or []:
            if not a.is_correct:
                q = next((x for x in questions if x["key"] == a.question_key), None)
                wrong_list.append(
                    {
                        "key": a.question_key,
                        "question": q["question"] if q else "",
                        "my_index": a.my_index,
                        "correct_index": a.correct_index,
                    }
                )
        return {
            "id": session.id,
            "source": session.source,
            "total": total,
            "answered": answered,
            "score": session.score,
            "accuracy": round(session.score / total * 100, 2) if total else None,
            "is_completed": session.is_completed,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "wrong_questions": wrong_list,
        }
