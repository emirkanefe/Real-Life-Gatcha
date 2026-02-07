import tkinter as tk
from tkinter import messagebox, ttk
import random
import json
import os
from datetime import datetime, timedelta

# --- SABİT AYARLAR ---
DOSYA_ADI = "gacha_data.json"
GOREV_BASI_ODUL = 20
WISH_MALIYETI = 160
WISH_10_MALIYETI = 1600
GUNLUK_LIMIT = 320

PITY_LIMIT_5 = 80  # 80'de garanti 5 yıldız
PITY_LIMIT_4 = 10  # 10'da garanti 4 yıldız (veya üstü)

DEFAULT_ODULLER = {
    "3_YILDIZ": ["Bir bölüm dizi izle", "Çikolata ye", "15 dk şekerleme yap", "Oyun oyna (30dk)"],
    "4_YILDIZ": ["Dışarıdan yemek söyle", "Sinemaya git", "Yeni bir kitap al", "Geç saatte yat"],
    "5_YILDIZ": ["Kıyafet alışverişi yap", "Pahalı bir restorana git", "Tam gün tembellik hakkı",
                 "Koleksiyon figürü al"]
}


class GachaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Genshin Life: Pity System")
        self.root.geometry("450x750")  # Biraz uzattık

        self.data = self.veri_yukle()
        self.gunluk_kontrol()

        # --- ARAYÜZ ---

        # 1. Üst Panel
        self.header_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        self.header_frame.pack(fill="x")

        self.elmas_label = tk.Label(self.header_frame, text=f"💎 {self.data['elmas']}", font=("Segoe UI", 24, "bold"),
                                    fg="cyan", bg="#2c3e50")
        self.elmas_label.pack()

        durum_renk = "#2ecc71" if self.data['gunluk_kazanilan'] < GUNLUK_LIMIT else "#e74c3c"
        self.limit_label = tk.Label(self.header_frame,
                                    text=f"Günlük Limit: {self.data['gunluk_kazanilan']}/{GUNLUK_LIMIT}",
                                    font=("Arial", 10), fg=durum_renk, bg="#2c3e50")
        self.limit_label.pack()

        # 2. Görev Listesi
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.gorev_widgets = []
        self.listeyi_guncelle()

        # 3. Alt Panel (Wish ve Pity)
        self.bottom_panel = tk.Frame(root, bg="#ecf0f1", pady=15)
        self.bottom_panel.pack(fill="x", side="bottom")

        # Pity Göstergeleri (YENİ)
        self.pity_frame = tk.Frame(self.bottom_panel, bg="#ecf0f1")
        self.pity_frame.pack(pady=5)

        self.pity_label_5 = tk.Label(self.pity_frame, text=f"5★ Pity: {self.data['pity_counter_5']}/{PITY_LIMIT_5}",
                                     font=("Arial", 10, "bold"), fg="#f39c12", bg="#ecf0f1")
        self.pity_label_5.pack(side="left", padx=10)

        self.pity_label_4 = tk.Label(self.pity_frame, text=f"4★ Pity: {self.data['pity_counter_4']}/{PITY_LIMIT_4}",
                                     font=("Arial", 10, "bold"), fg="#9b59b6", bg="#ecf0f1")
        self.pity_label_4.pack(side="left", padx=10)

        # Butonlar
        btn_container = tk.Frame(self.bottom_panel, bg="#ecf0f1")
        btn_container.pack()

        self.wish_btn = tk.Button(btn_container, text=f"x1 WISH\n({WISH_MALIYETI})", font=("Segoe UI", 10, "bold"),
                                  bg="#8e44ad", fg="white", width=12, height=2, command=lambda: self.wish_at(1))
        self.wish_btn.pack(side="left", padx=5)

        self.wish10_btn = tk.Button(btn_container, text=f"x10 WISH\n({WISH_10_MALIYETI})",
                                    font=("Segoe UI", 10, "bold"),
                                    bg="#f39c12", fg="white", width=12, height=2, command=lambda: self.wish_at(10))
        self.wish10_btn.pack(side="left", padx=5)

        self.settings_btn = tk.Button(self.bottom_panel, text="⚙️", font=("Arial", 12), command=self.ayarlari_ac)
        self.settings_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    # --- VERİ YÖNETİMİ ---
    def veri_yukle(self):
        varsayilan = {
            "elmas": 0, "gorevler": [], "oduller": DEFAULT_ODULLER,
            "son_reset_tarihi": "2000-01-01", "gunluk_kazanilan": 0,
            "pity_counter_5": 0,  # Kaç çekiş oldu (5 yıldız için)
            "pity_counter_4": 0  # Kaç çekiş oldu (4 yıldız için)
        }
        if not os.path.exists(DOSYA_ADI):
            with open(DOSYA_ADI, "w") as f: json.dump(varsayilan, f)
            return varsayilan
        with open(DOSYA_ADI, "r") as f:
            yuklenen = json.load(f)
            for key in varsayilan:
                if key not in yuklenen: yuklenen[key] = varsayilan[key]
            return yuklenen

    def veri_kaydet(self):
        with open(DOSYA_ADI, "w") as f: json.dump(self.data, f)

    def gunluk_kontrol(self):
        simdi = datetime.now()
        bugun = str(simdi.date() - timedelta(days=1)) if simdi.hour < 6 else str(simdi.date())
        if self.data["son_reset_tarihi"] != bugun:
            self.data["son_reset_tarihi"] = bugun
            self.data["gunluk_kazanilan"] = 0
            for gorev in self.data["gorevler"]: gorev["yapildi"] = False
            self.veri_kaydet()

    # --- FONKSİYONLAR ---
    def gorev_yapildi(self, index):
        gorev = self.data["gorevler"][index]
        if not gorev["yapildi"]:
            if self.data["gunluk_kazanilan"] >= GUNLUK_LIMIT:
                messagebox.showinfo("Limit Doldu", "Günlük elmas sınırına (320) ulaştın!")
            else:
                self.data["elmas"] += GOREV_BASI_ODUL
                self.data["gunluk_kazanilan"] += GOREV_BASI_ODUL
            gorev["yapildi"] = True
            self.veri_kaydet();
            self.arayuz_guncelle()

    def arayuz_guncelle(self):
        self.elmas_label.config(text=f"💎 {self.data['elmas']}")
        renk = "#2ecc71" if self.data['gunluk_kazanilan'] < GUNLUK_LIMIT else "#e74c3c"
        self.limit_label.config(text=f"Günlük Limit: {self.data['gunluk_kazanilan']}/{GUNLUK_LIMIT}", fg=renk)

        # Pity yazılarını güncelle
        self.pity_label_5.config(text=f"5★ Pity: {self.data['pity_counter_5']}/{PITY_LIMIT_5}")
        self.pity_label_4.config(text=f"4★ Pity: {self.data['pity_counter_4']}/{PITY_LIMIT_4}")

        self.listeyi_guncelle()

    def listeyi_guncelle(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        if not self.data["gorevler"]:
            tk.Label(self.scrollable_frame, text="Görev listen boş.", fg="gray").pack(pady=20)
            return
        for i, gorev in enumerate(self.data["gorevler"]):
            bg_color = "#dff9fb" if gorev["yapildi"] else "white"
            state = "disabled" if gorev["yapildi"] else "normal"
            btn_bg = "#bdc3c7" if gorev["yapildi"] else "#3498db"
            btn_text = "✅" if gorev["yapildi"] else f"Bitir ({GOREV_BASI_ODUL})"
            card = tk.Frame(self.scrollable_frame, bg=bg_color, pady=5, padx=5, relief="groove", bd=1)
            card.pack(fill="x", pady=2, padx=5)
            tk.Button(card, text=btn_text, bg=btn_bg, fg="white", state=state, width=10,
                      command=lambda idx=i: self.gorev_yapildi(idx)).pack(side="right")
            tk.Label(card, text=gorev["metin"], font=("Segoe UI", 11), bg=bg_color, anchor="w").pack(side="left",
                                                                                                     fill="x",
                                                                                                     expand=True)

    def tekli_cekim_hesapla(self):
        # Her çekişte sayaçları artır
        self.data["pity_counter_5"] += 1
        self.data["pity_counter_4"] += 1

        pity_5_active = self.data["pity_counter_5"] >= PITY_LIMIT_5
        pity_4_active = self.data["pity_counter_4"] >= PITY_LIMIT_4

        sans = random.random() * 100
        havuz = self.data["oduller"]

        sonuc = {}

        # 1. Önce 5 Yıldız Kontrolü (Pity VEYA Şans)
        if pity_5_active or sans <= 0.6:
            sonuc = {"renk": "#f1c40f", "yildiz": "★★★★★", "odul": random.choice(havuz["5_YILDIZ"])}
            self.data["pity_counter_5"] = 0  # Sıfırla
            self.data["pity_counter_4"] = 0  # 5 yıldız gelirse 4 yıldız pitysi de sıfırlanır (genelde)

        # 2. Sonra 4 Yıldız Kontrolü (Pity VEYA Şans)
        elif pity_4_active or sans <= 5.7:
            sonuc = {"renk": "#9b59b6", "yildiz": "★★★★", "odul": random.choice(havuz["4_YILDIZ"])}
            self.data["pity_counter_4"] = 0  # Sıfırla

        # 3. Hiçbiri değilse 3 Yıldız
        else:
            sonuc = {"renk": "#3498db", "yildiz": "★★★", "odul": random.choice(havuz["3_YILDIZ"])}

        return sonuc

    def wish_at(self, adet):
        maliyet = WISH_MALIYETI if adet == 1 else WISH_10_MALIYETI
        havuz = self.data["oduller"]
        if not havuz["5_YILDIZ"] or not havuz["4_YILDIZ"] or not havuz["3_YILDIZ"]:
            messagebox.showerror("Hata", "Ödül havuzu boş! Ayarlardan ödül ekle.")
            return

        if self.data["elmas"] >= maliyet:
            self.data["elmas"] -= maliyet

            sonuclar = []
            for _ in range(adet):
                # Her çekim için ayrı ayrı hesapla (Pity her adımda güncellenmeli)
                tek_sonuc = self.tekli_cekim_hesapla()
                sonuclar.append(tek_sonuc)

            self.veri_kaydet()
            self.arayuz_guncelle()
            self.sonuc_ekrani_goster(sonuclar)
        else:
            messagebox.showwarning("Yetersiz Bakiye", f"{maliyet} elmasın yok!")

    def sonuc_ekrani_goster(self, sonuclar):
        win = tk.Toplevel(self.root)
        win.title("WISH RESULTS")
        win.geometry("400x500")
        win.configure(bg="#2c3e50")

        tk.Label(win, text="✨ KAZANILANLAR ✨", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=10)

        canvas = tk.Canvas(win, bg="#2c3e50", highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#2c3e50")

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw", width=380)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")

        for item in sonuclar:
            row = tk.Frame(frame, bg=item["renk"], pady=5, padx=5)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=item["yildiz"], font=("Arial", 10, "bold"), bg=item["renk"], fg="white").pack(
                side="left")
            tk.Label(row, text=item["odul"], font=("Arial", 10, "bold"), bg=item["renk"], fg="white",
                     wraplength=250).pack(side="left", padx=5)

    def ayarlari_ac(self):
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Yönetim Paneli")
        self.settings_window.geometry("500x600")
        tab_control = ttk.Notebook(self.settings_window)

        tab_gorev = ttk.Frame(tab_control);
        tab_control.add(tab_gorev, text='Görev Listesi')
        add_frame = tk.Frame(tab_gorev, pady=10);
        add_frame.pack(fill="x")
        self.new_task_entry = tk.Entry(add_frame, width=30);
        self.new_task_entry.pack(side="left", padx=10)
        tk.Button(add_frame, text="Ekle", command=self.yeni_gorev_ekle, bg="#27ae60", fg="white").pack(side="left")
        self.gorev_listbox = tk.Listbox(tab_gorev);
        self.gorev_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        tk.Button(tab_gorev, text="Sil", command=self.gorev_sil, bg="#c0392b", fg="white").pack(pady=10)
        self.gorev_listbox_doldur()

        tab_odul = ttk.Frame(tab_control);
        tab_control.add(tab_odul, text='Ödül Havuzu')

        def create_area(title, color, key):
            tk.Label(tab_odul, text=title, fg=color, font=("bold")).pack(anchor="w", padx=10)
            txt = tk.Text(tab_odul, height=4, width=50);
            txt.pack(padx=10)
            txt.insert("1.0", "\n".join(self.data["oduller"][key]))
            return txt

        self.txt_3 = create_area("★★★ 3 Yıldız", "blue", "3_YILDIZ")
        self.txt_4 = create_area("★★★★ 4 Yıldız", "purple", "4_YILDIZ")
        self.txt_5 = create_area("★★★★★ 5 Yıldız", "#f39c12", "5_YILDIZ")
        tk.Button(tab_odul, text="Kaydet", command=self.odulleri_kaydet, bg="#2980b9", fg="white").pack(fill="x",
                                                                                                        padx=10,
                                                                                                        pady=10)
        tab_control.pack(expand=1, fill="both")

    def gorev_listbox_doldur(self):
        self.gorev_listbox.delete(0, tk.END)
        for g in self.data["gorevler"]: self.gorev_listbox.insert(tk.END, g["metin"])

    def yeni_gorev_ekle(self):
        txt = self.new_task_entry.get()
        if txt:
            self.data["gorevler"].append({"metin": txt, "yapildi": False})
            self.veri_kaydet();
            self.new_task_entry.delete(0, tk.END);
            self.gorev_listbox_doldur();
            self.arayuz_guncelle()

    def gorev_sil(self):
        secili = self.gorev_listbox.curselection()
        if secili:
            del self.data["gorevler"][secili[0]]
            self.veri_kaydet();
            self.gorev_listbox_doldur();
            self.arayuz_guncelle()

    def odulleri_kaydet(self):
        def get_list(widget): return [l for l in widget.get("1.0", tk.END).strip().split("\n") if l.strip()]

        self.data["oduller"]["3_YILDIZ"] = get_list(self.txt_3)
        self.data["oduller"]["4_YILDIZ"] = get_list(self.txt_4)
        self.data["oduller"]["5_YILDIZ"] = get_list(self.txt_5)
        self.veri_kaydet();
        messagebox.showinfo("Başarılı", "Ödüller güncellendi!")


if __name__ == "__main__":
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()