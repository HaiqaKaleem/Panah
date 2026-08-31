"""Authentication API endpoints — login, register, profile, refresh."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.schemas import (
    PasswordChange,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    hash_password,
    user_store,
    TokenData,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201,
             summary="Register a new user account")
async def register(user: UserCreate):
    """
    Register a new user.

    - **email**: Valid email address
    - **password**: Min 8 characters
    - **full_name**: User's display name
    - **role**: `admin`, `engineer`, `reviewer`, or `field_agent`
    """
    # Check existing
    existing = user_store.get_by_email(user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    created = user_store.create(
        user_id=user_id,
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        role=user.role,
    )

    return UserResponse(**{k: v for k, v in created.items() if k != "hashed_password"})


@router.post("/login", response_model=Token, summary="Login and get JWT token")
async def login(credentials: UserLogin):
    """
    Authenticate with email and password.

    Returns a JWT access token valid for 1 hour.
    """
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"], "role": user["role"]}
    )

    user_data = {k: v for k, v in user.items() if k != "hashed_password"}

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(**user_data),
    )


@router.post("/login/form", response_model=Token,
             summary="Login via OAuth2 form (for Swagger UI)")
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login using the Swagger UI 'Authorize' button."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"], "role": user["role"]}
    )

    user_data = {k: v for k, v in user.items() if k != "hashed_password"}

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(**user_data),
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(current_user: TokenData = Depends(get_current_active_user)):
    """Get the authenticated user's profile."""
    user = user_store.get_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**{k: v for k, v in user.items() if k != "hashed_password"})


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(current_user: TokenData = Depends(get_current_active_user)):
    """Get a new access token (requires valid existing token)."""
    user = user_store.get_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"], "role": user["role"]}
    )

    user_data = {k: v for k, v in user.items() if k != "hashed_password"}

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(**user_data),
    )


@router.get("/users", response_model=list[UserResponse], summary="List all users (admin only)")
async def list_users(current_user: TokenData = Depends(get_current_active_user)):
    """List all registered users. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return [
        UserResponse(**{k: v for k, v in u.items() if k != "hashed_password"})
        for u in user_store.list_all()
    ]
