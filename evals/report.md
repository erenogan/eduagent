# EduAgent Eval Raporu

Son koşu: 2026-09-08 12:51

## Tool Seçimi

- Toplam: 40
- Doğru: 35
- Doğruluk: %88
- Ortalama süre: 5.9s

### Yanlış Case'ler

- `t039` "kantin kaçta açılıyor" — beklenen: `None`, gerçekleşen: `search_knowledge_base`
- `t040` "okulun telefon numarası ne" — beklenen: `None`, gerçekleşen: `search_knowledge_base`
- `t041` "sınav kağıdımı görebilir miyim" — beklenen: `None`, gerçekleşen: `search_knowledge_base`
- `t043` "sınavda kopya çekersem ne olur, hem de benim sınav notlarım ne" — beklenen: `get_exam_results`, gerçekleşen: `search_knowledge_base`
- `t049` "koçumla görüşmek istiyorum" — beklenen: `get_coach_availability`, gerçekleşen: `None`

## Baseline Analizi (Tool Seçimi)

İlk baseline: **%88 (35/40)**. 5 hatalı case incelendiğinde, üç farklı durum ortaya çıktı:

### 1. Test setinin kendi hatası (2 case)

- **t049** "koçumla görüşmek istiyorum" — Beklenen `get_coach_availability` idi, ancak
  bu araç zorunlu bir `tarih` parametresi alıyor. Tarih verilmediğinde agent'ın doğru
  davranışı, önce kullanıcıya tarih sormaktır (tek turda araç çağıramaz). Yani agent
  doğru davrandı, beklenen değer hatalıydı. Çok turlu (multi-turn) akışlar tek case ile
  ölçülemez.
- **t043** "sınavda kopya çekersem ne olur, hem de sınav notlarım ne" — İki niyetli bir
  soru. Agent kurumsal kısmı (`search_knowledge_base`) seçti; bu savunulabilir bir tercih.
  Beklenen değer tartışmalıydı.

### 2. Gerçek davranış: RAG'in fazla çağrılması (3 case)

- **t039** "kantin kaçta açılıyor", **t040** "okulun telefon numarası ne",
  **t041** "sınav kağıdımı görebilir miyim" — Bu kurumsal sorular bilgi tabanında
  yer almıyor. Agent yine de `search_knowledge_base`'i çağırıp (boş sonuç alıp)
  "bilmiyorum" diyor. Sonuç kullanıcı için doğru, ancak gereksiz bir araç çağrısı
  yapılıyor (gecikme + maliyet israfı).

### Nasıl düzeltilebilir (bilinçli olarak uygulanmadı)

Sistem talimatına, bilgi tabanının kapsadığı konuların açıkça listelenmesi ve bu
kapsam dışındaki kurumsal sorularda arama yapmadan "bu konuda bilgim yok" denmesi
kuralı eklenebilir. Bu değişiklik t039-t041'i düzeltmesi beklenir. Baseline'ın
dürüstlüğünü korumak için bu iyileştirme raporlanmış ancak uygulanmamıştır; bir
sonraki iterasyonda A/B olarak ölçülebilir.
## Retrieval (RAG Getirme Kalitesi)

Ölçüt: recall@5 (doğru dokümanın ilk 5 sonuçta gelmesi).

- Ölçülen case: 18 (null case'ler hariç)
- recall@5: **%100 (18/18)**

Çoğu case'de doğru doküman 1. sırada geldi. Null case'ler (korpusta karşılığı
olmayan sorular) retrieval recall'dan hariç tutuldu; onların doğru davranışı
("bilmiyorum" demesi) tool suite'inde ölçülür.

> Not: Korpus şu an 5 parça. Daha büyük korpuslarda recall düşebilir; bu eval
> tam da o durumda kritik hale gelir.

## Otomasyon (Planlanan)

Eval şu an elle koşuluyor:
- `python evals/run_eval.py --suite tools`
- `python evals/run_eval.py --suite retrieval`

GitHub Actions ile her push'ta otomatik koşacak ve doğruluk eşiğin (baseline − 5 puan)
altına düşerse build kırılacak şekilde genişletilebilir. API anahtarları GitHub
Secrets ile sağlanır. Bu entegrasyon bir sonraki iterasyona bırakılmıştır.
