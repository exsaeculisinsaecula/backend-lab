from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import (
    analytics,
    auth,
    categories,
    concepts,
    progress,
    quiz,
    quiz_game,
    review,
    search,
    study,
    transfer,
    wrong_answers,
)

app = FastAPI(
    title="Backend Lab API",
    description=(
        "백엔드 핵심 개념 학습 API — "
        "JWT 로그인 · 개념 카드 · 퀴즈 게임 · 오답노트 · 복습 큐 · 분석 · 검색 · 백업\n\n"
        "모든 학습 API는 Bearer 토큰이 필요하며, 데이터는 로그인 사용자 단위로 격리됩니다."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": "3.0.0", "auth": "jwt-bearer"}


# ── 인증 (공개) ─────────────────────────────────────────────
app.include_router(auth.router)

# ── 콘텐츠 CRUD (인증 필요) ─────────────────────────────────
app.include_router(categories.router)
app.include_router(concepts.router)
app.include_router(quiz.router)
app.include_router(wrong_answers.router)
app.include_router(progress.router)

# ── 학습 플로우 ─────────────────────────────────────────────
app.include_router(study.router)
app.include_router(quiz_game.router)
app.include_router(review.router)

# ── 분석 · 검색 · 백업 ─────────────────────────────────────
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(transfer.router)
