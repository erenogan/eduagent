from sqlalchemy.orm import Session
import models
from datetime import datetime, time as time_type, date as date_type
from sqlalchemy.exc import IntegrityError
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_exam_results(db: Session, student_id: int):
    """
    Verilen öğrencinin tüm sınav sonuçlarını,
    ders adı ve tarihe göre sıralı biçimde döner.
    """
    sonuclar = (
        db.query(models.ExamResult)
        .filter(models.ExamResult.student_id == student_id)
        .order_by(models.ExamResult.tarih)
        .all()
    )


    cikti = []
    for s in sonuclar:
        cikti.append({
            "ders": s.subject.ad,
            "sinav": s.sinav_adi,
            "net": s.net,
            "tarih": s.tarih.isoformat(),
        })
    return cikti

def get_student_schedule(db: Session, student_id: int):

    program = (
        db.query(models.Schedule)
        .filter(models.Schedule.student_id == student_id)
        .all()
    )

    cikti = []
    for p in program:
        cikti.append({
            "gun": p.gun,
            "ders": p.subject.ad,
            "saat": p.saat.strftime("%H:%M"),
        })

    return cikti

def get_coach(db: Session, student_id: int):
    """
    Öğrencinin koçunun bilgilerini döner.
    """
    ogrenci = (
        db.query(models.Student)
        .filter(models.Student.id == student_id)
        .first()
    )

    if ogrenci is None or ogrenci.coach is None:
        return {"mesaj": "Bu öğrenciye atanmış bir koç bulunamadı."}

    return {
        "koc_id": ogrenci.coach.id,
        "koc_adi": ogrenci.coach.ad,
    }


def get_coach_availability(db: Session, student_id: int, tarih: str):
    """
    Öğrencinin koçunun, verilen tarihte boş olan görüşme saatlerini döner.
    Çalışma saatleri sabit: 09:00-17:00, saat başı slotlar.
    Dolu randevular çıkarılır.
    """
    # 1. Öğrencinin koçunu bul
    ogrenci = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if ogrenci is None or ogrenci.coach is None:
        return {"mesaj": "Bu öğrenciye atanmış bir koç bulunamadı."}

    coach_id = ogrenci.coach.id

    # 2. Tarihi doğrula
    try:
        tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
    except ValueError:
        return {"mesaj": "Tarih formatı geçersiz. Beklenen format: YYYY-MM-DD."}

    # 3. Sabit çalışma slotları (09:00 - 16:00, saat başı)
    tum_slotlar = [time_type(saat, 0) for saat in range(9, 17)]

    # 4. O koçun o tarihteki dolu randevularını çek
    dolu_randevular = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.coach_id == coach_id,
            models.Appointment.tarih == tarih_obj,
            models.Appointment.durum == "confirmed",
        )
        .all()
    )
    dolu_saatler = {r.saat for r in dolu_randevular}

    # 5. Boş slotları hesapla
    bos_slotlar = [
        s.strftime("%H:%M")
        for s in tum_slotlar
        if s not in dolu_saatler
        if s not in dolu_saatler
    ]

    return {
        "koc_adi": ogrenci.coach.ad,
        "tarih": tarih,
        "bos_saatler": bos_slotlar,
    }

def create_appointment(db: Session, student_id: int, tarih: str, saat: str):
    """..."""
    # ... geri kalan kod
    """
    Öğrencinin koçuyla randevu oluşturur.
    Önce kontrol eder (geçmiş tarih, çalışma saati, dolu slot),
    sonra veritabanına yazar. Constraint son güvenlik ağıdır.
    """
    # 1. Öğrenciyi ve koçunu bul
    ogrenci = db.query(models.Student).filter(
        models.Student.id == student_id
    ).first()

    if ogrenci is None or ogrenci.coach is None:
        return {"basarili": False, "mesaj": "Koç bulunamadı."}

    coach_id = ogrenci.coach.id

    # 2. Tarih ve saati doğrula (format)
    try:
        tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
    except ValueError:
        return {"basarili": False, "mesaj": "Tarih formatı geçersiz (YYYY-MM-DD bekleniyor)."}

    try:
        saat_obj = datetime.strptime(saat, "%H:%M").time()
    except ValueError:
        return {"basarili": False, "mesaj": "Saat formatı geçersiz (HH:MM bekleniyor)."}

    # 3. Geçmiş tarih kontrolü
    if tarih_obj < date_type.today():
        return {"basarili": False, "mesaj": "Geçmiş bir tarihe randevu oluşturulamaz."}

    # 4. Çalışma saati kontrolü (09:00 - 16:00 arası, saat başı)
    if saat_obj.minute != 0 or saat_obj.hour < 9 or saat_obj.hour > 16:
        return {"basarili": False, "mesaj": "Randevular yalnızca 09:00-16:00 arası, saat başı alınabilir."}

    # 5. Nazik dolu kontrolü (kullanıcıya güzel mesaj için)
    mevcut = db.query(models.Appointment).filter(
        models.Appointment.coach_id == coach_id,
        models.Appointment.tarih == tarih_obj,
        models.Appointment.saat == saat_obj,
        models.Appointment.durum == "confirmed",
    ).first()

    if mevcut is not None:
        return {"basarili": False, "mesaj": "Bu saat dolu, lütfen başka bir saat seçin."}

    # 6. Randevuyu yaz (constraint son güvenlik ağı)
    yeni_randevu = models.Appointment(
        student_id=student_id,
        coach_id=coach_id,
        tarih=tarih_obj,
        saat=saat_obj,
        durum="confirmed",
    )
    db.add(yeni_randevu)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"basarili": False, "mesaj": "Bu saat az önce dolduruldu, lütfen başka bir saat seçin."}

    return {
        "basarili": True,
        "mesaj": "Randevu oluşturuldu.",
        "koc_adi": ogrenci.coach.ad,
        "tarih": tarih,
        "saat": saat,
    }
def search_knowledge_base(db: Session, soru: str):
    """
    Kurum bilgi tabanında soruya en yakın parçaları bulur (vektör arama).
    """
    # 1. Soruyu vektöre çevir
    sonuc = genai.embed_content(
        model="models/gemini-embedding-001",
        content=soru,
        task_type="retrieval_query",
        output_dimensionality=768,
    )
    soru_vektoru = sonuc["embedding"]

    # 2. En yakın 3 parçayı bul (pgvector cosine distance)
    yakin_parcalar = (
        db.query(models.KnowledgeChunk)
        .order_by(models.KnowledgeChunk.embedding.cosine_distance(soru_vektoru))
        .limit(3)
        .all()
    )

    # 3. Parçaların metinlerini döndür
    return {
        "kaynaklar": [p.icerik for p in yakin_parcalar]
    }