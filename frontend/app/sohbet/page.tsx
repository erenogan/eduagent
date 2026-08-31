"use client";

import { useState, useEffect, useRef } from "react";

type Mesaj = {
  rol: "kullanici" | "asistan";
  icerik: string;
};

export default function SohbetPage() {
  const [mesajlar, setMesajlar] = useState<Mesaj[]>([]);
  const [girdi, setGirdi] = useState("");
  const [yukleniyor, setYukleniyor] = useState(false);
  const sonMesajRef = useRef<HTMLDivElement>(null);

  // Giriş kontrolü: token yoksa giriş sayfasına at
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/";
    }
  }, []);

  // Yeni mesaj gelince en alta kaydır
  useEffect(() => {
    sonMesajRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mesajlar]);

  async function mesajGonder() {
    if (!girdi.trim() || yukleniyor) return;

    const kullaniciMesaji = girdi.trim();
    setGirdi("");
    setMesajlar((onceki) => [...onceki, { rol: "kullanici", icerik: kullaniciMesaji }]);
    setYukleniyor(true);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/sohbet", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ mesaj: kullaniciMesaji, gecmis: mesajlar }),      });

      if (!res.ok) {
        setMesajlar((onceki) => [
          ...onceki,
          { rol: "asistan", icerik: "Bir hata oluştu. Lütfen tekrar deneyin." },
        ]);
        setYukleniyor(false);
        return;
      }

      const data = await res.json();
      setMesajlar((onceki) => [...onceki, { rol: "asistan", icerik: data.cevap }]);
    } catch {
      setMesajlar((onceki) => [
        ...onceki,
        { rol: "asistan", icerik: "Sunucuya bağlanılamadı." },
      ]);
    } finally {
      setYukleniyor(false);
    }
  }

  function cikisYap() {
    localStorage.removeItem("token");
    window.location.href = "/";
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Üst bar */}
      <header className="bg-white border-b border-slate-100 px-6 py-4 flex justify-between items-center">
        <h1 className="font-semibold text-slate-800">Nova Öğrenci Asistanı</h1>
        <button
          onClick={cikisYap}
          className="text-sm text-slate-500 hover:text-slate-800"
        >
          Çıkış
        </button>
      </header>

      {/* Mesajlar */}
      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-2xl w-full mx-auto space-y-4">
        {mesajlar.length === 0 && (
          <p className="text-center text-slate-400 mt-10">
            Merhaba! Sana nasıl yardımcı olabilirim? <br />
            Sınavların, ders programın veya koç randevun hakkında sorabilirsin.
          </p>
        )}

        {mesajlar.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.rol === "kullanici" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-2xl whitespace-pre-wrap ${
                m.rol === "kullanici"
                  ? "bg-slate-800 text-white"
                  : "bg-white border border-slate-200 text-slate-800"
              }`}
            >
              {m.icerik}
            </div>
          </div>
        ))}

        {yukleniyor && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 text-slate-400 px-4 py-2 rounded-2xl">
              yazıyor...
            </div>
          </div>
        )}

        <div ref={sonMesajRef} />
      </div>

      {/* Girdi alanı */}
      <div className="bg-white border-t border-slate-100 px-4 py-4">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            type="text"
            value={girdi}
            onChange={(e) => setGirdi(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && mesajGonder()}
            placeholder="Bir şeyler yaz..."
            className="flex-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <button
            onClick={mesajGonder}
            disabled={yukleniyor}
            className="bg-slate-800 text-white px-5 py-2 rounded-lg hover:bg-slate-700 transition disabled:opacity-50"
          >
            Gönder
          </button>
        </div>
      </div>
    </div>
  );
}