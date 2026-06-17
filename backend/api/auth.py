"""API routes for user authentication 鈥?register, login, profile.

Uses JWT (HS256) with configurable expiry.  Passwords hashed with bcrypt.
"""

from datetime import UTC, datetime, timedelta

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.db.database import _get_backend
from backend.limiter import limiter
from core.config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET, RATE_LIMIT_AUTH

router = APIRouter()
security = HTTPBearer(auto_error=False)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Schemas
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    display_name: str


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    created_at: str


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Password helpers 鈥?bcrypt
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def _hash_password(password: str) -> str:
    """Hash a password with bcrypt (automatic salt, 12 rounds)."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(plain: str, stored: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
    except ValueError:
        return False


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# JWT helpers
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def _create_token(username: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> str | None:
    """Decode a JWT and return the username, or ``None`` if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """FastAPI dependency: extract the authenticated username from the Bearer token.

    Returns ``"guest"`` if no token is provided (backward-compatible).
    Raises 401 if a token is provided but invalid.
    """
    if credentials is None:
        return "guest"

    username = _decode_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Routes
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
@router.post("/auth/register", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def register(req: RegisterRequest, request: Request) -> AuthResponse:
    if len(req.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    existing_rows = _get_backend().execute("SELECT id FROM users WHERE username = ?", (req.username,))
    existing = existing_rows[0] if existing_rows else None
    if existing:
        raise HTTPException(409, "Username already taken")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _get_backend().execute(
        "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
        (req.username, _hash_password(req.password), req.display_name or req.username, now),
    )

    token = _create_token(req.username)
    return AuthResponse(
        access_token=token,
        username=req.username,
        display_name=req.display_name or req.username,
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def login(req: LoginRequest, request: Request) -> AuthResponse:
    rows = _get_backend().execute(
        "SELECT password_hash, display_name FROM users WHERE username = ?",
        (req.username,),
    )
    row = rows[0] if rows else None
    if not row:
        raise HTTPException(401, "Invalid username or password")

    if not _verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Invalid username or password")

    token = _create_token(req.username)
    return AuthResponse(
        access_token=token,
        username=req.username,
        display_name=row["display_name"] or req.username,
    )


@router.get("/auth/me", response_model=UserInfo)
def get_me(username: str = Depends(get_current_user)) -> UserInfo:
    if username == "guest":
        raise HTTPException(401, "Not authenticated")

    rows = _get_backend().execute(
        "SELECT id, username, display_name, created_at FROM users WHERE username = ?",
        (username,),
    )
    row = rows[0] if rows else None
    if not row:
        raise HTTPException(404, "User not found")

    return UserInfo(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        created_at=row["created_at"],
    )
