"use client";

import { useState } from "react";

export default function LoginPage() {
  const [kullaniciAdi, setKullaniciAdi] = useState("");
  const [sifre, setSifre] = useState("");
  const [hata, setHata] = useState("");
  const [yukleniyor, setYukleniyor] = useState(false);

  async function girisYap() {
    setHata("");
    setYukleniyor(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", kullaniciAdi);
      formData.append("password", sifre);

      const res = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!res.ok) {
        setHata("Kullanıcı adı veya şifre hatalı.");
        setYukleniyor(false);
        return;
      }

      const data = await res.json();
      // Token'ı tarayıcıda sakla
      localStorage.setItem("token", data.access_token);
      // Sohbet sayfasına yönlendir
      window.location.href = "/sohbet";
    } catch {
      setHata("Sunucuya bağlanılamadı.");
      setYukleniyor(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
        <h1 className="text-2xl font-semibold text-slate-800 text-center">
          Nova Eğitim Kurumları
        </h1>
        <p className="text-sm text-slate-500 text-center mt-1 mb-6">
          Öğrenci Asistanına Hoş Geldiniz
        </p>

        <div className="space-y-3">
          <input
            type="text"
            placeholder="Kullanıcı adı"
            value={kullaniciAdi}
            onChange={(e) => setKullaniciAdi(e.target.value)}
            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <input
            type="password"
            placeholder="Şifre"
            value={sifre}
            onChange={(e) => setSifre(e.target.value)}
            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400"
          />

          {hata && <p className="text-sm text-red-500">{hata}</p>}

          <button
            onClick={girisYap}
            disabled={yukleniyor}
            className="w-full bg-slate-800 text-white py-2 rounded-lg hover:bg-slate-700 transition disabled:opacity-50"
          >
            {yukleniyor ? "Giriş yapılıyor..." : "Giriş Yap"}
          </button>
        </div>
      </div>
    </div>
  );
}