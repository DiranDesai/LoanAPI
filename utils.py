from fastapi import Depends
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt



# Secret key for encoding & decoding JWT
SECRET_KEY = "$2b$12$rRUvZq2IlUMss/ypmcBwbujoUj6X29TbyfbU0XOJTvR"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30




# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashPassword(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

