import sys
import os
import json
import time
from datetime import datetime
from collections import defaultdict

# Backend'i import edebilmek için yolu ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import agent
from database import SessionLocal
import models

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DEMO_STUDENT_ID = 1
EVAL_DIR = os.path.dirname(__file__)


def load_cases(dosya):
    cases = []
    yol = os.path.join(EVAL_DIR, dosya)
    with open(yol, "r", encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if satir:
                cases.append(json.loads(satir))
    return cases


# ============ TOOL SUITE ============

def run_tools_suite():
    cases = load_cases("cases_tools.jsonl")
    db = SessionLocal()

    sonuclar = []
    toplam_sure = 0

    for case in cases:
        baslangic = time.time()
        cikti = agent.agent_calistir(
            case["soru"], db, DEMO_STUDENT_ID, eval_modu=True,
        )
        sure_ms = int((time.time() - baslangic) * 1000)
        toplam_sure += sure_ms

        secilenler = cikti["secilen_toollar"]
        beklenen = case["beklenen_tool"]

        if beklenen is None:
            case_dogru = len(secilenler) == 0
        else:
            case_dogru = beklenen in secilenler

        gerceklesen = secilenler[0] if secilenler else None

        sonuclar.append({
            "id": case["id"],
            "soru": case["soru"],
            "beklenen": beklenen,
            "gerceklesen": gerceklesen,
            "dogru": case_dogru,
            "sure_ms": sure_ms,
        })

        durum = "OK   " if case_dogru else "YANLIS"
        print(f"[{durum}] {case['id']}: beklenen={beklenen}, gerceklesen={gerceklesen} ({sure_ms}ms)")
        time.sleep(3)

    db.close()
    return sonuclar, toplam_sure


def ozet_bas(sonuclar, toplam_sure):
    toplam = len(sonuclar)
    dogru = sum(1 for s in sonuclar if s["dogru"])
    dogruluk = (dogru / toplam) * 100 if toplam else 0
    ort_sure = (toplam_sure / toplam / 1000) if toplam else 0

    print("\n" + "=" * 50)
    print(f"Toplam: {toplam} | Dogru: {dogru} | Dogruluk: %{dogruluk:.0f} | Ort. sure: {ort_sure:.1f}s")
    print("=" * 50)

    yanlislar = [s for s in sonuclar if not s["dogru"]]
    if yanlislar:
        print("\nYANLIS CASE'LER:")
        for s in yanlislar:
            print(f"  {s['id']}: \"{s['soru']}\"")
            print(f"       beklenen={s['beklenen']}, gerceklesen={s['gerceklesen']}")

    confusion = defaultdict(lambda: defaultdict(int))
    for s in sonuclar:
        confusion[str(s["beklenen"])][str(s["gerceklesen"])] += 1

    print("\nKARISIKLIK (beklenen -> gerceklesen):")
    for beklenen, gerceklesenler in confusion.items():
        for gerceklesen, adet in gerceklesenler.items():
            isaret = "OK" if beklenen == gerceklesen else "!!"
            print(f"  [{isaret}] {beklenen} -> {gerceklesen}: {adet}")

    return {"toplam": toplam, "dogru": dogru, "dogruluk": dogruluk, "ort_sure_s": ort_sure}


def kaydet(sonuclar, ozet):
    results_dir = os.path.join(EVAL_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)

    damga = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_yol = os.path.join(results_dir, f"tools_{damga}.json")
    with open(json_yol, "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "sonuclar": sonuclar}, f, ensure_ascii=False, indent=2)
    print(f"\nSonuclar kaydedildi: {json_yol}")

    report_yol = os.path.join(EVAL_DIR, "report.md")
    with open(report_yol, "w", encoding="utf-8") as f:
        f.write("# EduAgent Eval Raporu\n\n")
        f.write(f"Son koşu: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Tool Seçimi\n\n")
        f.write(f"- Toplam: {ozet['toplam']}\n")
        f.write(f"- Doğru: {ozet['dogru']}\n")
        f.write(f"- Doğruluk: %{ozet['dogruluk']:.0f}\n")
        f.write(f"- Ortalama süre: {ozet['ort_sure_s']:.1f}s\n\n")

        yanlislar = [s for s in sonuclar if not s["dogru"]]
        if yanlislar:
            f.write("### Yanlış Case'ler\n\n")
            for s in yanlislar:
                f.write(f"- `{s['id']}` \"{s['soru']}\" — beklenen: `{s['beklenen']}`, gerçekleşen: `{s['gerceklesen']}`\n")
    print(f"Rapor güncellendi: {report_yol}")


# ============ RETRIEVAL SUITE ============

def embed_soru(soru):
    sonuc = genai.embed_content(
        model="models/gemini-embedding-001",
        content=soru,
        task_type="retrieval_query",
        output_dimensionality=768,
    )
    return sonuc["embedding"]


def run_retrieval_suite():
    cases = load_cases("cases_retrieval.jsonl")
    db = SessionLocal()

    sonuclar = []

    for case in cases:
        baslangic = time.time()
        soru_vek = embed_soru(case["soru"])

        yakinlar = (
            db.query(models.KnowledgeChunk)
            .order_by(models.KnowledgeChunk.embedding.cosine_distance(soru_vek))
            .limit(5)
            .all()
        )
        sure_ms = int((time.time() - baslangic) * 1000)

        getirilen_docidler = [p.doc_id for p in yakinlar]
        beklenen = case["beklenen_doc_id"]

        if beklenen is None:
            case_dogru = None
        else:
            case_dogru = beklenen in getirilen_docidler

        sonuclar.append({
            "id": case["id"],
            "soru": case["soru"],
            "beklenen": beklenen,
            "getirilen": getirilen_docidler,
            "dogru": case_dogru,
            "sure_ms": sure_ms,
        })

        if case_dogru is None:
            durum = "SKIP "
        elif case_dogru:
            durum = "OK   "
        else:
            durum = "YANLIS"
        print(f"[{durum}] {case['id']}: beklenen={beklenen}, getirilen={getirilen_docidler} ({sure_ms}ms)")
        time.sleep(1)

    db.close()

    olculen = [s for s in sonuclar if s["dogru"] is not None]
    dogru = sum(1 for s in olculen if s["dogru"])
    toplam = len(olculen)
    recall = (dogru / toplam) * 100 if toplam else 0

    print("\n" + "=" * 50)
    print(f"Retrieval recall@5: {dogru}/{toplam} = %{recall:.0f}")
    print("=" * 50)

    yanlislar = [s for s in olculen if not s["dogru"]]
    if yanlislar:
        print("\nYANLIS (dogru parca ilk 5'te yok):")
        for s in yanlislar:
            print(f"  {s['id']}: \"{s['soru']}\" beklenen={s['beklenen']}")
            print(f"       getirilen={s['getirilen']}")

    return sonuclar


# ============ MAIN ============

if __name__ == "__main__":
    suite = sys.argv[2] if len(sys.argv) > 2 else "tools"

    if suite == "tools":
        sonuclar, toplam_sure = run_tools_suite()
        ozet = ozet_bas(sonuclar, toplam_sure)
        kaydet(sonuclar, ozet)
    elif suite == "retrieval":
        run_retrieval_suite()
    else:
        print("Bilinmeyen suite. 'tools' veya 'retrieval' kullan.")