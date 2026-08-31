import os
import json
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy.orm import Session

import tools

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"


ARAC_TANIMLARI = [
    {
        "type": "function",
        "function": {
            "name": "get_exam_results",
            "description": "Giriş yapmış öğrencinin sınav sonuçlarını getirir. "
                           "Öğrenci sınav performansını, netlerini, hangi derste "
                           "nasıl gittiğini sorduğunda kullanılır.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_schedule",
            "description": "Giriş yapmış öğrencinin ders programını getirir. "
                           "Öğrenci hangi gün hangi dersi olduğunu, ders saatlerini, "
                           "programını sorduğunda kullanılır.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_coach",
            "description": "Giriş yapmış öğrencinin koçunun kim olduğunu getirir. "
                           "Öğrenci koçunu, danışmanını sorduğunda kullanılır.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
{
        "type": "function",
        "function": {
            "name": "get_coach_availability",
            "description": "Öğrencinin koçunun belirli bir tarihteki boş görüşme "
                           "saatlerini getirir. Öğrenci koçuyla randevu almak, "
                           "görüşmek istediğinde ve bir tarih belirttiğinde kullanılır.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tarih": {
                        "type": "string",
                        "description": "Görüşme tarihi, YYYY-MM-DD formatında. Örn: 2026-08-28",
                    },
                },
                "required": ["tarih"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
                        "description": "Öğrencinin koçuyla randevu oluşturur ve veritabanına kaydeder. "
                           "Öğrenci bir tarih ve saat belirterek randevu almak istediğinde "
                           "bu aracı DOĞRUDAN çağır. Tarih ve saat verilmişse tereddüt etme, "
                           "randevuyu oluştur. Uygunluk ve çakışma kontrolünü araç kendisi yapar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tarih": {
                        "type": "string",
                        "description": "Randevu tarihi, YYYY-MM-DD formatında.",
                    },
                    "saat": {
                        "type": "string",
                        "description": "Randevu saati, HH:MM formatında. Örn: 15:00",
                    },
                },
                "required": ["tarih", "saat"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Kurum kuralları ve politikaları hakkındaki soruları "
                           "yanıtlamak için bilgi tabanında arama yapar. Devamsızlık, "
                           "randevu kuralları, sınav kuralları, koçluk sistemi, ders "
                           "değişikliği gibi KURUMSAL konular sorulduğunda kullanılır. "
                           "Öğrencinin kişisel verisi (sınav, program) için KULLANILMAZ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "soru": {
                        "type": "string",
                        "description": "Kullanıcının kurum kuralıyla ilgili sorusu.",
                    },
                },
                "required": ["soru"],
            },
        },
    },
]


def agent_calistir(kullanici_mesaji: str, db: Session, student_id: int, gecmis: list = None) -> str:
    mesajlar = [
        {
            "role": "system",
            "content": (
                "Sen Nova Eğitim Kurumları'nın öğrenci asistanısın. "
                "Adın EduAgent. Öğrencilere eğitim verileri konusunda yardımcı olursun.\n\n"

                "TEMEL KURALLAR:\n"
                "- Yalnızca araçlardan gelen gerçek verilere dayan. "
                "Veri yoksa veya bir bilgiye erişemiyorsan bunu açıkça söyle, ASLA uydurma.\n"
                "- Kitap, kaynak, kurs veya dışarıdan bilgi ÖNERME. "
                "Sadece öğrencinin sistemdeki verisini yorumla.\n"
                "- Sana verilmeyen bir konuda tahmin yürütme. "
                "Örneğin öğrencinin hangi konularda zayıf olduğunu ancak veride varsa söyle.\n\n"
                  "- Tarih hesabı yapma ve kullanıcıya 'yarın hangi gün' diye SORMA. "
        "Ders programı sorulduğunda, öğrenci 'yarın' veya 'bugün' dese bile, "
        "programın tamamını gün adlarıyla listele (örn. 'Pazartesi Matematik "
        "ve Fizik, Salı Türkçe dersin var'). Öğrenci ilgili günü kendisi görsün.\n"

                "ÜSLUP:\n"
                "- Türkçe, samimi ama profesyonel konuş.\n"
                       "- Öz ol ama kuru olma. Uzun listeler ve tablolar kullanma; "
        "3-5 cümlelik bir değerlendirme yap ve gerekiyorsa öğrenciye "
        "kısa, veriye dayalı bir yönlendirme ekle (örn. hangi derse "
        "ağırlık vermesi gerektiği). Ama kaynak, kitap veya çalışma "
        "planı ÖNERME.\n"
                "- Öğrenciyi gereksiz yere motive etme konuşması yapma, emoji kullanma.\n"
                "- Sadece sorulan şeye cevap ver, ekstra öneri yığını sunma."
            ),
        },

    ]
    if gecmis:
        for m in gecmis:
            rol = "user" if m["rol"] == "kullanici" else "assistant"
            mesajlar.append({"role": rol, "content": m["icerik"]})

        # Yeni mesajı ekle
    mesajlar.append({"role": "user", "content": kullanici_mesaji})


    ilk_cevap = client.chat.completions.create(
        model=MODEL,
        messages=mesajlar,
        tools=ARAC_TANIMLARI,
        tool_choice="auto",
    )

    cevap_mesaji = ilk_cevap.choices[0].message


    if not cevap_mesaji.tool_calls:

        return cevap_mesaji.content

    mesajlar.append({
        "role": "assistant",
        "content": cevap_mesaji.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in cevap_mesaji.tool_calls
        ],
    })
    for arac_cagrisi in cevap_mesaji.tool_calls:
        arac_adi = arac_cagrisi.function.name


        if arac_adi == "get_exam_results":
            sonuc = tools.get_exam_results(db, student_id)
        elif arac_adi == "get_student_schedule":
            sonuc = tools.get_student_schedule(db, student_id)
        elif arac_adi == "get_coach":
            sonuc = tools.get_coach(db, student_id)
        elif arac_adi == "get_coach_availability":
            import json as _json
            args = _json.loads(arac_cagrisi.function.arguments)
            sonuc = tools.get_coach_availability(db, student_id, args.get("tarih"))
        elif arac_adi == "create_appointment":
            args = json.loads(arac_cagrisi.function.arguments)
            sonuc = tools.create_appointment(
            db, student_id, args.get("tarih"), args.get("saat")
            )
        elif arac_adi == "search_knowledge_base":
            args = json.loads(arac_cagrisi.function.arguments)
            sonuc = tools.search_knowledge_base(db, args.get("soru"))
        else:
            sonuc = {"hata": "bilinmeyen araç"}


        mesajlar.append({
            "role": "tool",
            "tool_call_id": arac_cagrisi.id,
            "name": arac_adi,
            "content": json.dumps(sonuc, ensure_ascii=False),
        })

    # 4. Model, araç sonuçlarıyla nihai cevabı yazsın
    ikinci_cevap = client.chat.completions.create(
        model=MODEL,
        messages=mesajlar,
    )

    return ikinci_cevap.choices[0].message.content

