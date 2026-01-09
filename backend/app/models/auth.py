from pydantic import BaseModel, EmailStr
from typing import Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import hashlib
import jwt
from typing import Any, Dict
from app.databases.database import get_collection
from app.utils.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def _get_users_collection():
    return get_collection("users")


def _hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    # Chuẩn hoá sang UTF-8, sau đó SHA-256
    sha256_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.hash(sha256_digest)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    if not isinstance(plain_password, str):
        return False

    sha256_digest = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(sha256_digest, hashed_password)


def _create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)