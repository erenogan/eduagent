from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import models
from auth import get_db, dogrula_sifre, token_uret, get_current_student


import tools


app = FastAPI(title="EduAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def kok():
    return {"mesaj": "EduAgent ayakta"}


# --- Giriş ---
@app.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Kullanıcıyı bul
    ogrenci = db.query(models.Student).filter(
        models.Student.kullanici_adi == form.username
    ).first()

    # Yoksa ya da şifre yanlışsa reddet
    if ogrenci is None or not dogrula_sifre(form.password, ogrenci.sifre_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
        )

    # Token üret ve dön
    token = token_uret(ogrenci.id)
    return {"access_token": token, "token_type": "bearer"}


# --- Korumalı test endpoint'i: "ben kimim?" ---
@app.get("/ben-kimim")
def ben_kimim(ogrenci: models.Student = Depends(get_current_student)):
    return {
        "id": ogrenci.id,
        "ad": ogrenci.ad,
        "sinif": ogrenci.sinif,
        "kullanici_adi": ogrenci.kullanici_adi,
    }

@app.get("/sinav-sonuclarim")
def sinav_sonuclarim(
    ogrenci: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return tools.get_exam_results(db, ogrenci.id)


from pydantic import BaseModel
import agent


class GecmisMesaj(BaseModel):
    rol: str
    icerik: str


class SohbetMesaji(BaseModel):
    mesaj: str
    gecmis: list[GecmisMesaj] = []


@app.post("/sohbet")
def sohbet(
    istek: SohbetMesaji,
    ogrenci: models.Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    gecmis = [{"rol": m.rol, "icerik": m.icerik} for m in istek.gecmis]
    cevap = agent.agent_calistir(istek.mesaj, db, ogrenci.id, gecmis)
    return {"cevap": cevap}