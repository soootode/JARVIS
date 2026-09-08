"""
auth.py - Jarvis-You Multi-User Authentication
------------------------------------------------
JWT-based auth: signup / login / get_current_user.
Mounted in main.py as `app.include_router(auth_router)`.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from database import User, get_session
from email_service import (
    build_email_verification_link,
    build_password_reset_link,
    send_password_reset_email,
    send_verification_email,
)

# FIX (Vercel): python-dotenv is a dev-convenience dependency for loading a
# local .env file. Vercel (and most serverless/production hosts) injects
# real environment variables directly and doesn't need it, so it may not be
# installed there. Fall back to a no-op `load_dotenv()` instead of crashing
# the whole module with an ImportError if the package is absent.
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

# FIX: auth.py reads JWT_SECRET_KEY from the environment at import time, and
# main.py imports auth *before* it calls load_dotenv() — so without this
# call here, .env would not have been loaded yet and the check below would
# always fail. load_dotenv() is idempotent, so calling it again in main.py
# afterwards is harmless.
load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "❌ JWT_SECRET_KEY در .env پیدا نشد.\n"
        "یک رشته تصادفی طولانی بساز (مثلاً: python -c \"import secrets; print(secrets.token_hex(32))\")\n"
        "و در .env بنویس: JWT_SECRET_KEY=your_generated_secret"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # یک هفته

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    display_name: Optional[str] = None
    onboarding_completed: bool


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    onboarding_completed: bool
    email_verified: bool = False


# ── Password reset / email verification schemas ─────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetTokenRequest(BaseModel):
    token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── Reset / verification token helpers (SECURITY) ────────────────────────────
# توکن خام فقط یک‌بار در ایمیل کاربر دیده می‌شود؛ در DB فقط SHA-256 آن ذخیره
# می‌شود (مثل bcrypt برای رمز، اینجا هم لو رفتن رکورد کافی نیست که توکن قابل
# استفاده باشد). بعد از مصرف، فیلدها null می‌شوند (single-use enforcement).

RESET_TOKEN_EXPIRE_MINUTES = 60  # 1 ساعت
VERIFICATION_TOKEN_EXPIRE_HOURS = 24


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _issue_user_token(user: User, kind: str) -> str:
    """توکن جدید صادر و هشش روی user ست می‌شود. kind: 'reset' | 'verification'."""
    raw = _generate_token()
    expires = (
        datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        if kind == "reset"
        else datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    )
    if kind == "reset":
        # SECURITY: فقط هش توکن در DB ذخیره می‌شود، نه خودش
        user.reset_password_token = _hash_token(raw)
        user.reset_password_expires_at = expires
    else:
        user.verification_token_hash = _hash_token(raw)
        user.verification_token_expires = expires
    return raw


def _consume_user_token(user: User, raw_token: str, kind: str) -> bool:
    """توکن را اعتبارسنجی می‌کند؛ معتبر بود → مصرف (null) و True برمی‌گرداند."""
    if kind == "reset":
        stored_hash, expires = user.reset_password_token, user.reset_password_expires_at
    else:
        stored_hash, expires = user.verification_token_hash, user.verification_token_expires

    if not stored_hash or not expires:
        return False
    if _hash_token(raw_token) != stored_hash:
        return False
    if datetime.utcnow() > expires:
        # توکن منقضی — همان‌جا پاکش کن تا رکورد بی‌اثر نماند
        if kind == "reset":
            user.reset_password_token = None
            user.reset_password_expires_at = None
        else:
            user.verification_token_hash = None
            user.verification_token_expires = None
        return False

    if kind == "reset":
        user.reset_password_token = None
        user.reset_password_expires_at = None
    else:
        user.verification_token_hash = None
        user.verification_token_expires = None
    return True


# ── JWT helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError("no sub claim")
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر یا منقضی شده است. دوباره وارد شوید.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependency: get_current_user ────────────────────────────────────────────

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    """
    FastAPI dependency. Use as:
        async def endpoint(current_user: User = Depends(get_current_user)):
    Raises 401 if the token is missing, invalid, expired, or the user
    no longer exists / is disabled.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="لطفاً ابتدا وارد شوید.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(token)
    session = get_session()
    try:
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="کاربر پیدا نشد یا غیرفعال است.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # detach a plain copy so it's safe to use after session.close()
        session.expunge(user)
        return user
    finally:
        session.close()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
async def signup(payload: SignupRequest):
    session = get_session()
    try:
        existing = session.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise HTTPException(status_code=400, detail="این ایمیل قبلاً ثبت شده است.")
        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="رمز عبور باید حداقل ۸ کاراکتر باشد.")

        user = User(
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            display_name=payload.display_name,
            onboarding_completed=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # ایمیل تأیید (best-effort — شکست ارسال نباید ثبت‌نام را بشکند)
        try:
            raw = _issue_user_token(user, "verification")
            session.commit()
            send_verification_email(user.email, build_email_verification_link(raw))
        except Exception as e:
            print(f"⚠️ auth: verification email failed: {e}")

        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            onboarding_completed=user.onboarding_completed,
        )
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    session = get_session()
    try:
        user = session.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="ایمیل یا رمز عبور اشتباه است.")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="این حساب غیرفعال شده است.")

        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            onboarding_completed=user.onboarding_completed,
        )
    finally:
        session.close()


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        onboarding_completed=current_user.onboarding_completed,
        email_verified=bool(current_user.email_verified),
    )


# ── Password reset & email verification endpoints ───────────────────────────

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    درخواست لینک بازیابی رمز. برای جلوگیری از user enumeration، پاسخ همیشه
    یک پیام عمومی است — چه ایمیل وجود داشته باشد چه نه.
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.email == payload.email.lower()).first()
        if user and user.is_active:
            raw = _issue_user_token(user, "reset")
            session.commit()
            send_password_reset_email(user.email, build_password_reset_link(raw))
    finally:
        session.close()

    return {"status": "success", "message": "اگر این ایمیل ثبت شده باشد، لینک بازیابی برایتان ارسال شد."}


@router.post("/verify-reset-token")
async def verify_reset_token(payload: ResetTokenRequest):
    """پیش‌بررسی UX: آیا توکن ریست معتبر است؟ (بدون مصرف کردنش)"""
    session = get_session()
    try:
        user = (
            session.query(User)
            .filter(User.reset_password_token == _hash_token(payload.token))
            .first()
        )
        valid = bool(
            user
            and user.reset_password_expires_at
            and datetime.utcnow() <= user.reset_password_expires_at
        )
        return {"valid": valid}
    finally:
        session.close()


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="رمز عبور باید حداقل ۸ کاراکتر باشد.")

    session = get_session()
    try:
        user = (
            session.query(User)
            .filter(User.reset_password_token == _hash_token(payload.token))
            .first()
        )
        # توکن نامعتبر/منقضی → همان خطای عمومی (invalidation after use تضمین می‌کند
        # هر توکن فقط یک‌بار قابل استفاده باشد)
        if not user or not _consume_user_token(user, payload.token, "reset"):
            raise HTTPException(
                status_code=400,
                detail="لینک بازیابی نامعتبر یا منقضی شده است. دوباره درخواست دهید.",
            )

        user.hashed_password = hash_password(payload.new_password)
        # کسی که رمز را ریست کرد صاحبِ صندوق ایمیل است → تأیید ایمیل هم حساب می‌شود
        user.email_verified = True
        session.commit()
        return {"status": "success", "message": "رمز عبور با موفقیت تغییر کرد. حالا وارد شوید."}
    finally:
        session.close()


@router.post("/verify-email")
async def verify_email(payload: ResetTokenRequest):
    session = get_session()
    try:
        user = (
            session.query(User)
            .filter(User.verification_token_hash == _hash_token(payload.token))
            .first()
        )
        if not user or not _consume_user_token(user, payload.token, "verification"):
            raise HTTPException(
                status_code=400,
                detail="لینک تأیید نامعتبر یا منقضی شده است.",
            )
        user.email_verified = True
        session.commit()
        return {"status": "success", "message": "ایمیل شما تأیید شد. خوش آمدید!"}
    finally:
        session.close()


@router.post("/resend-verification")
async def resend_verification(current_user: User = Depends(get_current_user)):
    """ارسال مجدد ایمیل تأیید برای کاربر لاگین‌کرده‌ی تأییدنشده."""
    if current_user.email_verified:
        return {"status": "success", "message": "ایمیل شما قبلاً تأیید شده است."}

    # re-attach: current_user از سشن دیگری expunge شده
    session = get_session()
    try:
        user = session.get(User, current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="کاربر پیدا نشد.")
        raw = _issue_user_token(user, "verification")
        session.commit()
        send_verification_email(user.email, build_email_verification_link(raw))
    finally:
        session.close()
    return {"status": "success", "message": "ایمیل تأیید دوباره ارسال شد."}
