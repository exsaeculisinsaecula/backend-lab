from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import categories, concepts, progress, quiz, wrong_answers

app = FastAPI(
    title="Backend Lab API",
    description="백엔드 핵심 개념 학습 사이트 — 개념·퀴즈·오답노트 CRUD",
    version="1.0.0",
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
    return {"status": "ok"}


app.include_router(categories.router)
app.include_router(concepts.router)
app.include_router(quiz.router)
app.include_router(wrong_answers.router)
app.include_router(progress.router)
