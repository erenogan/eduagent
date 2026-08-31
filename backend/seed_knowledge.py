import os
import google.generativeai as genai
from dotenv import load_dotenv

from database import SessionLocal
import models

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EMBED_MODEL = "models/gemini-embedding-001"


DOKUMANLAR = [
    "Devamsızlık Politikası: Öğrenciler bir dönem içinde en fazla 10 gün "
    "devamsızlık hakkına sahiptir. 10 günü aşan devamsızlıklarda veli "
    "bilgilendirilir ve öğrenci koçuyla görüşme yapılır.",

    "Randevu Politikası: Öğrenciler koçlarıyla hafta içi 09:00-17:00 saatleri "
    "arasında, saat başı randevu oluşturabilir. Bir öğrenci aynı gün en fazla "
    "bir koçluk randevusu alabilir. Randevular en az 2 saat öncesinden iptal edilmelidir.",

    "Sınav Kuralları: Denemeler her iki haftada bir yapılır. Sınav sırasında "
    "kopya çeken öğrencinin sınavı geçersiz sayılır ve durum veliye bildirilir. "
    "Sınav sonuçları sınavdan 3 gün sonra sistemde yayınlanır.",

    "Koçluk Sistemi: Her öğrenciye bir akademik koç atanır. Koç, öğrencinin "
    "sınav performansını takip eder, haftalık çalışma planı önerir ve motivasyon "
    "desteği sağlar. Öğrenciler koçlarıyla düzenli görüşmeye teşvik edilir.",

    "Ders Değişikliği: Öğrenciler dönem başında seçtikleri ders programını "
    "ilk iki hafta içinde değiştirebilir. İki haftadan sonra ders değişikliği "
    "yalnızca kurum yönetiminin onayıyla yapılabilir.",
]


def embed_metin(metin: str):
    sonuc = genai.embed_content(
        model=EMBED_MODEL,
        content=metin,
        task_type="retrieval_document",
        output_dimensionality=768,
    )
    return sonuc["embedding"]


def main():
    db = SessionLocal()

    db.query(models.KnowledgeChunk).delete()
    db.commit()

    for metin in DOKUMANLAR:
        vektor = embed_metin(metin)
        parca = models.KnowledgeChunk(icerik=metin, embedding=vektor)
        db.add(parca)

    db.commit()
    db.close()
    print(f"{len(DOKUMANLAR)} doküman parçası yüklendi.")


if __name__ == "__main__":
    main()