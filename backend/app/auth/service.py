"""JWT authentication service for PANAGAH."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.auth.schemas import TokenData, UserResponse

# ── Configuration ──────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(64))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Password Hashing ──────────────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False

class _PwdContext:
    def hash(self, secret: str) -> str:
        return hash_password(secret)
    def verify(self, secret: str, hash_str: str) -> bool:
        return verify_password(secret, hash_str)

pwd_context = _PwdContext()

# ── OAuth2 Scheme ─────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── In-Memory User Store (swap for DB in production) ──────────────────
class InMemoryUserStore:
    """Simple in-memory user store. Replace with SQLAlchemy in production."""

    def __init__(self):
        self._users: dict[str, dict] = {}
        self._by_email: dict[str, dict] = {}
        # Seed admin user
        self._seed_admin()

    def _seed_admin(self):
        admin = {
            "id": "usr_admin_001",
            "email": "admin@panagah.org",
            "hashed_password": pwd_context.hash("Admin@12345"),
            "full_name": "PANAGAH Admin",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        self._users[admin["id"]] = admin
        self._by_email[admin["email"]] = admin

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[dict]:
        return self._by_email.get(email.lower())

    def create(self, user_id: str, email: str, hashed_password: str,
               full_name: str, role: str = "engineer") -> dict:
        user = {
            "id": user_id,
            "email": email.lower(),
            "hashed_password": hashed_password,
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        self._users[user_id] = user
        self._by_email[email.lower()] = user
        return user

    def list_all(self) -> list[dict]:
        return list(self._users.values())


user_store = InMemoryUserStore()


# ── Token Functions ───────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


# ── User Functions ────────────────────────────────────────────────────
def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user by email and password."""
    user = user_store.get_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


# ── Dependency Functions ──────────────────────────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Get the current user from the JWT token."""
    return verify_token(token)


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Ensure the current user is active."""
    if current_user.user_id:
        user = user_store.get_by_id(current_user.user_id)
        if user and not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )
    return current_user


def require_role(*roles: str):
    """Dependency that requires the user to have one of the specified roles."""
    async def role_checker(current_user: TokenData = Depends(get_current_active_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not in required roles: {roles}",
            )
        return current_user
    return role_checker
