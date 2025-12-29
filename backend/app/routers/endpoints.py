from fastapi import APIRouter, status, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from backend.app.schemas import (
    UserResponse,
    UserRegister,
    UserLogin,
    Token,
    SettingsResponse,
    ThemeRequest
)
from backend.app.database import get_session
from backend.app.models import User, UserSettings
from backend.app.crud import (
    get_user_by_username,
    get_user_by_id,
    create_user,
    update_user,
    update_user_settings
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

security = HTTPBearer()


# ===== health checking =====

@router.get(
    path="/health-api",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def health_check():
    return {"message": "API is running"}


# ===== authorization and authentication =====

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    access_token = credentials.credentials
    try:
        payload: dict = decode_token(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"Invalid or expired token. JWTError: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    token_type: str = payload.get("type")

    if username is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user: User = await get_user_by_username(
        session=session,
        username=username
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="User is temporarily blocked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_logged_on:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user is not logged in",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/register",
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_session)
) -> User:
    if await get_user_by_username(session, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user_data.password)

    user: User = await create_user(
        session=session,
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )

    return user


@router.post("/login",
             response_model=Token,
             status_code=status.HTTP_202_ACCEPTED)
async def login(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session)
) -> JSONResponse:
    user: User = await get_user_by_username(session, user_data.username)

    if (not user) or (not verify_password(user_data.password, user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="User is temporarily blocked",
        )
    
    if user.is_logged_on:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="User alredy logged in"
        )
    
    user: User = await update_user(
        session=session,
        user_id=user.id,
        **{
            "is_logged_on": True
        }
    )

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
        content={
            "access_token": access_token,
            "token_type": "bearer"
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    response.status_code=status.HTTP_202_ACCEPTED

    return response


@router.post("/refresh",
             response_model=Token,
             status_code=status.HTTP_202_ACCEPTED)
async def refresh_access_token(
    request: Request,
    session: AsyncSession = Depends(get_session)
)-> Token | JSONResponse:
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
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content={"detail": f"Refresh token not decoded. ERR: {str(e)}"}
        )
        response.delete_cookie(
            key="refresh_token",
            secure=False,
            httponly=True,
        )
        return response

    if (user_id is None) or (token_type != "refresh"):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid refresh token"
        )

    user: User = await get_user_by_id(session, int(user_id))

    if (not user) or (not user.is_active):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="User incorrect or locked"
        )

    access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={
            "sub": user.username,
            "type": "access",
            "exp": access_token_expires
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/logout",
            response_model=None,
            status_code=status.HTTP_200_OK)
async def logout(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> JSONResponse:
    await update_user(
        session=session,
        user_id=user.id,
        **{
            "is_logged_on": False
        }
    )

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


# ===== authorized access =====

@router.get("/users/me",
            response_model=UserResponse,
            status_code=status.HTTP_200_OK)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


@router.get("/users/me/settings",
            response_model=SettingsResponse,
            status_code=status.HTTP_200_OK)
async def get_user_settings(
    current_user: User = Depends(get_current_user)
) -> SettingsResponse:
    settings: UserSettings = current_user.settings

    return SettingsResponse(
        theme=settings.theme
    )


@router.post("/users/me/settings/theme",
             response_model=None,
             status_code=status.HTTP_200_OK)
async def set_user_settings_theme(
    setting_data: ThemeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> dict:
    settings: UserSettings = current_user.settings
    
    await update_user_settings(
        session=session,
        user_serttings_id=settings.id,
        **{
            "theme": setting_data.theme
        }
    )

    return {"message": "Successed set theme"}

# TODO:
# GET /repo/send-analyze + FILE
# GET /repo/send-analyze/ws
# GET /repo/doc
# GET /repos/my
# GET /repos/public