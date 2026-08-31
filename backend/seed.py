from datetime import date, time
from database import SessionLocal, engine, Base
import models
import bcrypt

def hash_sifre(sifre: str) -> str:
    return bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Temiz başlangıç: tabloları sıfırla
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# --- Koç ---
koc = models.Coach(ad="Mehmet Demir")
db.add(koc)
db.commit()
db.refresh(koc)

# --- Öğrenci (demo hesabı) ---
ogrenci = models.Student(
    ad="Ahmet Yılmaz",
    sinif="12-A",
    alan="Sayısal",
    coach_id=koc.id,
    kullanici_adi="ahmet",
    sifre_hash=hash_sifre("1234"),
)
db.add(ogrenci)
db.commit()
db.refresh(ogrenci)

# --- Dersler ---
dersler = {}
for ders_adi in ["Matematik", "Fizik", "Türkçe", "Kimya", "Biyoloji"]:
    d = models.Subject(ad=ders_adi)
    db.add(d)
    db.commit()
    db.refresh(d)
    dersler[ders_adi] = d

# --- Sınav sonuçları (gerçekçi desen) ---
# Matematik: yükselen, Fizik: düşen, Türkçe: stabil
sinav_verisi = {
    "Matematik": [21, 23, 26, 28],   # yükseliş
    "Fizik":     [18, 15, 14, 12],   # düşüş
    "Türkçe":    [31, 30, 32, 31],   # stabil
}
tarihler = [date(2026, 6, 1), date(2026, 6, 15), date(2026, 7, 1), date(2026, 7, 15)]

for ders_adi, netler in sinav_verisi.items():
    for i, net in enumerate(netler):
        sonuc = models.ExamResult(
            student_id=ogrenci.id,
            subject_id=dersler[ders_adi].id,
            sinav_adi=f"TYT Deneme {i+1}",
            net=net,
            tarih=tarihler[i],
        )
        db.add(sonuc)
db.commit()

# --- Ders programı ---
program = [
    ("Pazartesi", "Matematik", time(10, 0)),
    ("Pazartesi", "Fizik", time(13, 30)),
    ("Salı", "Türkçe", time(16, 0)),
]
for gun, ders_adi, saat in program:
    p = models.Schedule(
        student_id=ogrenci.id,
        subject_id=dersler[ders_adi].id,
        gun=gun,
        saat=saat,
    )
    db.add(p)
db.commit()

ogrenci_id = ogrenci.id
db.close()
print("Sahte veri yüklendi.")
print(f"Demo öğrenci id: {ogrenci_id}")