from fastapi import APIRouter, HTTPException, status

from app.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, auth: AuthServiceDep) -> TokenOut:
    """회원가입 즉시 JWT를 발급합니다."""
    if auth.get_by_email(payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 가입된 이메일입니다")
    user = auth.create_user(
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )
    token = create_access_token(subject=user.id)
    return TokenOut(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, auth: AuthServiceDep) -> TokenOut:
    user = auth.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id)
    return TokenOut(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return user
