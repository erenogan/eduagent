import os
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import SessionLocal
import models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_SURESI_DK = 60 * 24


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- Şifre işlemleri ---
def hash_sifre(sifre: str) -> str:
    return bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def dogrula_sifre(girilen: str, saklanan_hash: str) -> bool:
    return bcrypt.checkpw(girilen.encode("utf-8"), saklanan_hash.encode("utf-8"))


# --- Token üretme ---
def token_uret(student_id: int) -> str:
    son_gecerlilik = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_SURESI_DK)
    veri = {"sub": str(student_id), "exp": son_gecerlilik}
    return jwt.encode(veri, SECRET_KEY, algorithm=ALGORITHM)


# --- DB oturumu (her istek için) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Token'dan giriş yapan öğrenciyi bul ---
def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Student:
    hata = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz kimlik bilgisi",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get("sub")
        if student_id is None:
            raise hata
    except JWTError:
        raise hata

    ogrenci = db.query(models.Student).filter(models.Student.id == int(student_id)).first()
    if ogrenci is None:
        raise hata
    return ogrenci