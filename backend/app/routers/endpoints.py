from fastapi import APIRouter, status, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from backend.app.schemas import (
    UserResponse,
    UserRegister,
    UserLogin,
    Token
)
from backend.app.database import get_session
from backend.app.models import User
from backend.app.crud import (
    get_user_by_username,
    get_user_by_id
)
from backend.app.auth import (
    get_password_hash,
    verify_password,
    create_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)


router = APIRouter()


# ===== get authorized user =====

async def get_current_user():
    return 0

# ===== health checking =====

@router.get(
    path="/health-api",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {"message": "API is running"}


# ===== authorization and authentication =====

@router.post("/register",
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister,
                   db: AsyncSession = Depends(get_session)) -> User:
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user_data.password)

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )

    # TODO: РАбота с базой данных на добавление нового пользователя

    return user


@router.post("/login",
             response_model=Token,
             status_code=status.HTTP_200_OK)
async def login(user_data: UserLogin,
                db: AsyncSession = Depends(get_session)) -> JSONResponse:
    user = get_user_by_username(db, user_data.username)

    if (not user) or (not verify_password(user_data.password, user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    user.last_login = datetime.utcnow()

    # TODO: Работа с базой данных
    # db.commit()

    access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={
            "sub": user.username,
            "type": "access",
            "exp": access_token_expires
        }
    )

    refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_token(
        data={
            "user_id": user.id,
            "type": "refresh",
            "exp": refresh_token_expires
        }
    )

    response = JSONResponse(
        content=Token(
            access_token=access_token,
            token_type="bearer"
        )
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return response


@router.post("/refresh",
             response_model=Token,
             status_code=status.HTTP_200_OK)
async def refresh_access_token(request: Request,
                               db: AsyncSession = Depends(get_session))-> Token | JSONResponse:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookie"
        )

    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("user_id")
        token_type = payload.get("type")
    except Exception as e:
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": f"Refresh token not decoded. ERR: {str(e)}"}
        )
        response.delete_cookie(key="refresh_token", httponly=True)
        return response

    if (user_id is None) or (token_type != "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = get_user_by_id(db, int(user_id))

    if (not user) or (not user.is_active):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User incorrect or locked"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user.username, "type": "access"},
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/logout",
            response_model=None,
            status_code=status.HTTP_200_OK)
def logout() -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Successful logged out"}
    )
    response.delete_cookie(
        key="refresh_token",
        secure=False,
        httponly=True
    )
    return response


@router.get("/users/me",
            response_model=UserResponse,
            status_code=status.HTTP_200_OK)
def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user