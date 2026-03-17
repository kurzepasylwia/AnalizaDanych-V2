import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

plt.style.use("seaborn-v0_8")

# KOLORY
KOLOR_TLO        = "#F0F4F8"
KOLOR_SIDEBAR    = "#1B3A5C"
KOLOR_HEADER     = "#1B3A5C"
KOLOR_ACCENT     = "#2E86C1"
KOLOR_ACCENT2    = "#27AE60"
KOLOR_BIALY      = "#FFFFFF"
KOLOR_TEKST      = "#1A1A2E"
KOLOR_SZARY      = "#8096A7"
KOLOR_KARTA      = "#FFFFFF"
KOLOR_BORDER     = "#D6E4F0"
KOLOR_BTN_HOVER  = "#1A6FA8"

# GLOBALNA ZMIENNA
df = None

# WCZYTANIE PLIKU CSV
def wczytaj_plik():
    global df
    sciezka = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if sciezka:
        df = pd.read_csv(sciezka)
        label_status.config(text="✅ Plik wczytany poprawnie", fg="#27ae60")



# POMOCNICZA: filtrowanie danych
def pobierz_przefiltrowane():
    if df is None:
        return None
    if entry_wiek_min.get() == "" or entry_wiek_max.get() == "":
        return None

    wiek_min = int(entry_wiek_min.get())
    wiek_max = int(entry_wiek_max.get())
    wynik = df[(df["Age"] >= wiek_min) & (df["Age"] <= wiek_max)].copy()

    wybrana_plec = var_plec.get()
    if wybrana_plec != "Wszyscy":
        wynik = wynik[wynik["Gender"] == wybrana_plec]

    wynik["BMI Category"] = wynik["BMI Category"].replace({"Normal Weight": "Normal"})
    return wynik

# STYL WYKRESÓW
def stylizuj_osie(axs_lista):
    for ax in axs_lista:
        ax.set_facecolor("#FAFCFF")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(KOLOR_BORDER)
        ax.spines["bottom"].set_color(KOLOR_BORDER)
        ax.tick_params(colors="#555555", labelsize=9)
        ax.grid(True, axis="y", alpha=0.4, linestyle="--", color="#D6E4F0")

# ZAKŁADKA 1: ANALIZA
def filtruj_dane():
    global df

    if df is None:
        label_status.config(text="❌ Najpierw wczytaj plik!", fg="#E74C3C")
        return
    if entry_wiek_min.get() == "" or entry_wiek_max.get() == "":
        label_status.config(text="❌ Wpisz zakres wieku!", fg="#E74C3C")
        return

    przefiltrowane = pobierz_przefiltrowane()

    if przefiltrowane is None or przefiltrowane.empty:
        label_status.config(text="❌ Brak danych dla podanych filtrów", fg="#E74C3C")
        return

    # STATYSTYKI DO KART
    srednie_kroki = przefiltrowane["Daily Steps"].mean()
    srednia_sen = przefiltrowane["Quality of Sleep"].mean()
    liczba = len(przefiltrowane)

    if srednia_sen >= 7:
        kolor_sen = "#27AE60"; status = "Dobry sen"
    elif srednia_sen >= 5:
        kolor_sen = "#F39C12"; status = "Przeciętny sen"
    else:
        kolor_sen = "#E74C3C"; status = "Zły sen"

    # Aktualizacja kart statystyk
    karta_liczba_val.config(text=str(liczba))
    karta_kroki_val.config(text=f"{srednie_kroki:.0f}")
    karta_sen_val.config(text=f"{srednia_sen:.1f}/10", fg=kolor_sen)
    karta_status_val.config(text=status, fg=kolor_sen)

    label_status.config(text="✅  Analiza zakończona", fg="#27AE60")
    rysuj_wykresy_glowne(przefiltrowane, frame_wykres_analiza)


def rysuj_wykresy_glowne(przefiltrowane, kontener):
    for widget in kontener.winfo_children():
        widget.destroy()

    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    fig.patch.set_facecolor(KOLOR_TLO)
    stylizuj_osie(axs)

    kolory     = {"Male": "#2E86C1", "Female": "#E05C7A"}
    kolory_bmi = {"Normal": "#27AE60", "Overweight": "#F39C12", "Obese": "#E74C3C"}

    # Wykres 1: Scatter kroków vs jakość snu
    for plec in przefiltrowane["Gender"].unique():
        dane = przefiltrowane[przefiltrowane["Gender"] == plec]
        axs[0].scatter(dane["Daily Steps"], dane["Quality of Sleep"],
                       color=kolory.get(plec, "#999"),
                       alpha=0.7, s=48, edgecolors="white", linewidths=0.5, label=plec)
    z = np.polyfit(przefiltrowane["Daily Steps"], przefiltrowane["Quality of Sleep"], 1)
    p = np.poly1d(z)
    x_s = np.sort(przefiltrowane["Daily Steps"])
    axs[0].plot(x_s, p(x_s), color=KOLOR_ACCENT, linewidth=2,
                linestyle="--", alpha=0.7, label="Trend")
    axs[0].set_title("Kroki dzienne vs Jakość snu",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[0].set_xlabel("Kroki dziennie", color=KOLOR_SZARY, fontsize=9)
    axs[0].set_ylabel("Jakość snu (1–10)", color=KOLOR_SZARY, fontsize=9)
    axs[0].legend(fontsize=8, framealpha=0.6)
    axs[0].grid(True, alpha=0.25, linestyle="--", color=KOLOR_BORDER)

    # Wykres 2: Średnia kroków wg BMI
    kolejnosc  = [k for k in ["Normal", "Overweight", "Obese"]
                  if k in przefiltrowane["BMI Category"].unique()]
    srednie_bmi = przefiltrowane.groupby("BMI Category")["Daily Steps"].mean().reindex(kolejnosc)
    bars = axs[1].bar(srednie_bmi.index, srednie_bmi.values,
                      color=[kolory_bmi.get(k, "#999") for k in kolejnosc],
                      edgecolor="white", linewidth=1.2, width=0.5)
    for bar, val in zip(bars, srednie_bmi.values):
        axs[1].text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 40, f"{val:.0f}",
                    ha="center", va="bottom",
                    fontsize=9, color=KOLOR_TEKST, fontweight="bold")
    axs[1].set_title("Średnia liczba kroków wg BMI",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[1].set_ylabel("Średnia liczba kroków", color=KOLOR_SZARY, fontsize=9)
    axs[1].set_ylim(bottom=max(0, srednie_bmi.values.min() - 1000))

    # Wykres 3: Boxplot jakości snu wg BMI
    dane_bp = [przefiltrowane[przefiltrowane["BMI Category"] == k]["Quality of Sleep"].dropna()
               for k in kolejnosc]
    bp = axs[2].boxplot(dane_bp, tick_labels=kolejnosc, patch_artist=True,
                        medianprops=dict(color="white", linewidth=2.5),
                        whiskerprops=dict(color=KOLOR_SZARY, linewidth=1.2),
                        capprops=dict(color=KOLOR_SZARY, linewidth=1.2),
                        flierprops=dict(marker="o", markerfacecolor="#F39C12",
                                        markersize=4, alpha=0.6))
    for patch, k in zip(bp["boxes"], kolejnosc):
        patch.set_facecolor(kolory_bmi.get(k, "#999"))
        patch.set_alpha(0.75)
    axs[2].set_title("Rozkład jakości snu wg BMI",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[2].set_ylabel("Jakość snu (1–10)", color=KOLOR_SZARY, fontsize=9)

    plt.tight_layout(pad=1.8)
    canvas = FigureCanvasTkAgg(fig, master=kontener)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# ZAKŁADKA 2: PORÓWNANIE GRUP

def porownaj_grupy():
    global df
    if df is None:
        label_status.config(text="❌ Najpierw wczytaj plik!", fg="#E74C3C")
        return

    dane = df.copy()
    dane["BMI Category"] = dane["BMI Category"].replace({"Normal Weight": "Normal"})

    for widget in frame_wykres_porownanie.winfo_children():
        widget.destroy()

    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8))
    fig.patch.set_facecolor(KOLOR_TLO)
    stylizuj_osie(axs)

    szerokosc = 0.35
    kolory_plec = {"Male": "#2E86C1", "Female": "#E05C7A"}

    # Wykres 1: Kroki wg grupy wiekowej i płci
    dane["Grupa wiekowa"] = pd.cut(dane["Age"], bins=[0, 35, 45, 60],
                                    labels=["<35 lat", "35–45 lat", ">45 lat"])
    srednie = dane.groupby(["Grupa wiekowa", "Gender"],
                            observed=True)["Daily Steps"].mean().unstack()
    x = np.arange(len(srednie.index))
    axs[0].bar(x - szerokosc/2, srednie.get("Male",   [0]*len(x)),
               szerokosc, label="Male",   color="#2E86C1", edgecolor="white")
    axs[0].bar(x + szerokosc/2, srednie.get("Female", [0]*len(x)),
               szerokosc, label="Female", color="#E05C7A", edgecolor="white")
    axs[0].set_xticks(x)
    axs[0].set_xticklabels(srednie.index, fontsize=8)
    axs[0].set_title("Kroki wg grupy wiekowej i płci",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[0].set_ylabel("Średnia liczba kroków", color=KOLOR_SZARY, fontsize=9)
    axs[0].legend(fontsize=8)

    # Wykres 2: Boxplot jakości snu wg płci
    grupy = [dane[dane["Gender"] == p]["Quality of Sleep"].dropna()
             for p in ["Male", "Female"]]
    bp = axs[1].boxplot(grupy, tick_labels=["Male", "Female"], patch_artist=True,
                        medianprops=dict(color="white", linewidth=2.5),
                        whiskerprops=dict(color=KOLOR_SZARY),
                        capprops=dict(color=KOLOR_SZARY))
    for patch, kol in zip(bp["boxes"], ["#2E86C1", "#E05C7A"]):
        patch.set_facecolor(kol)
        patch.set_alpha(0.75)
    axs[1].set_title("Jakość snu wg płci",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[1].set_ylabel("Jakość snu (1–10)", color=KOLOR_SZARY, fontsize=9)

    # Wykres 3: Kroki wg BMI i płci
    kolory_bmi  = {"Normal": "#27AE60", "Overweight": "#F39C12", "Obese": "#E74C3C"}
    kolejnosc   = [k for k in ["Normal", "Overweight", "Obese"]
                   if k in dane["BMI Category"].unique()]
    bmi_plec    = dane.groupby(["BMI Category", "Gender"])["Daily Steps"].mean().unstack()
    bmi_plec    = bmi_plec.reindex(kolejnosc)
    x2 = np.arange(len(kolejnosc))
    axs[2].bar(x2 - szerokosc/2, bmi_plec.get("Male",   [0]*len(x2)),
               szerokosc, label="Male",   color="#2E86C1", edgecolor="white")
    axs[2].bar(x2 + szerokosc/2, bmi_plec.get("Female", [0]*len(x2)),
               szerokosc, label="Female", color="#E05C7A", edgecolor="white")
    axs[2].set_xticks(x2)
    axs[2].set_xticklabels(kolejnosc, fontsize=9)
    axs[2].set_title("Kroki wg BMI i płci",
                     fontsize=10, fontweight="bold", color=KOLOR_TEKST, pad=8)
    axs[2].set_ylabel("Średnia liczba kroków", color=KOLOR_SZARY, fontsize=9)
    axs[2].legend(fontsize=8)

    plt.tight_layout(pad=1.8)
    canvas = FigureCanvasTkAgg(fig, master=frame_wykres_porownanie)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    k = len(dane[dane["Gender"] == "Female"])
    m = len(dane[dane["Gender"] == "Male"])
    label_status.config(
        text=f"Wszyscy pacjenci: {len(dane)}   |   Kobiety: {k}   |   Mężczyźni: {m}",
        fg=KOLOR_ACCENT
    )


# ZAKŁADKA 3: EKSPORT CSV + PDF
def eksportuj_raport():
    global df
    if df is None:
        label_status_eksport.config(text="❌  Najpierw wczytaj plik!", fg="#E74C3C")
        return

    przefiltrowane = pobierz_przefiltrowane()
    if przefiltrowane is None or przefiltrowane.empty:
        label_status_eksport.config(
            text="❌  Ustaw filtry i kliknij 'Filtruj i analizuj' w zakładce Analiza",
            fg="#E74C3C"
        )
        return

    sciezka_bazowa = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Wybierz lokalizację i nazwę raportu"
    )
    if not sciezka_bazowa:
        return

    sciezka_bazowa = sciezka_bazowa.replace(".csv", "")
    sciezka_csv    = sciezka_bazowa + ".csv"
    sciezka_pdf    = sciezka_bazowa + ".pdf"

    # --- Eksport CSV ---
    przefiltrowane.to_csv(sciezka_csv, index=False)

 
    # Generowanie wykresu do PDF
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    kolory_bmi  = {"Normal": "#27AE60", "Overweight": "#F39C12", "Obese": "#E74C3C"}
    kolejnosc   = [k for k in ["Normal", "Overweight", "Obese"]
                   if k in przefiltrowane["BMI Category"].unique()]
    kolory_sc   = {"Male": "#2E86C1", "Female": "#E05C7A"}

    for plec in przefiltrowane["Gender"].unique():
        d = przefiltrowane[przefiltrowane["Gender"] == plec]
        axs[0].scatter(d["Daily Steps"], d["Quality of Sleep"],
                       color=kolory_sc.get(plec, "#999"),
                       alpha=0.6, s=28, label=plec)
    axs[0].set_title("Kroki vs Jakosc snu")
    axs[0].set_xlabel("Kroki dziennie")
    axs[0].set_ylabel("Jakosc snu")
    axs[0].legend(fontsize=8)

    sr_bmi = przefiltrowane.groupby("BMI Category")["Daily Steps"].mean().reindex(kolejnosc)
    axs[1].bar(sr_bmi.index, sr_bmi.values,
               color=[kolory_bmi.get(k, "#999") for k in kolejnosc],
               edgecolor="white")
    axs[1].set_title("Srednia liczba krokow wg BMI")
    axs[1].set_ylabel("Kroki")

    plt.tight_layout()
    wykres_path = sciezka_bazowa + "_temp.png"
    fig.savefig(wykres_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # PDF
    c = pdf_canvas.Canvas(sciezka_pdf, pagesize=A4)
    W, H = A4

    c.setFillColorRGB(0.106, 0.227, 0.361)
    c.rect(0, H - 80, W, 80, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, H - 45, "Raport analizy danych medycznych")
    c.setFont("Helvetica", 10)
    c.drawString(50, H - 65, "Analiza: dzienna liczba krokow vs BMI i jakosc snu")

    c.setFillColorRGB(0.106, 0.227, 0.361)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, H - 115, "Statystyki ogolne")

    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 11)

    statystyki = [
        f"Filtry: Wiek {entry_wiek_min.get()}-{entry_wiek_max.get()} lat,  Plec: {var_plec.get()}",
        f"Liczba pacjentow: {len(przefiltrowane)}",
        f"Srednia liczba krokow: {przefiltrowane['Daily Steps'].mean():.0f} krokow/dzien",
        f"Srednia jakosc snu: {przefiltrowane['Quality of Sleep'].mean():.2f} / 10",
        f"Mediana jakosci snu: {przefiltrowane['Quality of Sleep'].median():.1f}",
        f"Min. kroki: {przefiltrowane['Daily Steps'].min():.0f}   |   Max: {przefiltrowane['Daily Steps'].max():.0f}",
    ]
    y = H - 140
    for linia in statystyki:
        c.drawString(50, y, linia)
        y -= 20

    c.setFillColorRGB(0.106, 0.227, 0.361)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, "Srednie kroki wg BMI:")
    y -= 30
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    for kat in kolejnosc:
        sr = przefiltrowane[przefiltrowane["BMI Category"] == kat]["Daily Steps"].mean()
        c.drawString(70, y, f"{kat}: {sr:.0f} krokow/dzien")
        y -= 18

    c.drawImage(wykres_path, 40, y - 255, width=510, height=235)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 25, "Wygenerowano automatycznie — System analizy danych medycznych")
    c.save()

    if os.path.exists(wykres_path):
        os.remove(wykres_path)

    nazwa = os.path.basename(sciezka_bazowa)
    label_status_eksport.config(
        text=f"✅  Zapisano: {nazwa}.csv  i  {nazwa}.pdf",
        fg="#27AE60"
    )

### GUI

root = tk.Tk()
root.title("Analiza kroków, BMI i jakości snu")
root.configure(bg=KOLOR_TLO)
root.geometry("1200x740")
root.minsize(1100, 680)

# NAGŁÓWEK
header_frame = tk.Frame(root, bg=KOLOR_HEADER, height=64)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

tk.Label(header_frame,
         text="🏥  System Analizy Danych Medycznych",
         font=("Helvetica", 17, "bold"),
         bg=KOLOR_HEADER, fg="white").pack(side="left", padx=28, pady=18)

tk.Label(header_frame,
         text="Kroki dzienne  ·  BMI  ·  Jakość snu",
         font=("Helvetica", 10),
         bg=KOLOR_HEADER, fg="#A8C8E8").pack(side="right", padx=28, pady=18)

# GŁÓWNY OBSZAR
main_frame = tk.Frame(root, bg=KOLOR_TLO)
main_frame.pack(fill="both", expand=True)

# SIDEBAR
sidebar = tk.Frame(main_frame, bg=KOLOR_SIDEBAR, width=230)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="FILTRY DANYCH",
         font=("Helvetica", 9, "bold"),
         bg=KOLOR_SIDEBAR, fg="#7FB3D3").pack(pady=(24, 6), padx=20, anchor="w")

# SEPARATOR
tk.Frame(sidebar, bg="#2E5F8A", height=1).pack(fill="x", padx=16, pady=4)

# Wczytaj plik
btn_wczytaj = tk.Button(sidebar, text="📂  Wczytaj plik CSV",
                         command=wczytaj_plik,
                         bg="#2E86C1", fg="white",
                         relief="flat", bd=0,
                         font=("Helvetica", 10, "bold"),
                         padx=14, pady=10,
                         cursor="hand2",
                         activebackground="#1A6FA8",
                         activeforeground="white")
btn_wczytaj.pack(fill="x", padx=16, pady=(10, 4))

label_plik = tk.Label(sidebar, text="Brak pliku",
                       font=("Helvetica", 8),
                       bg=KOLOR_SIDEBAR, fg="#7FB3D3",
                       wraplength=190)
label_plik.pack(padx=16, pady=(0, 12), anchor="w")

tk.Frame(sidebar, bg="#2E5F8A", height=1).pack(fill="x", padx=16, pady=4)

# Wiek - od
tk.Label(sidebar, text="Wiek od:",
         font=("Helvetica", 9, "bold"),
         bg=KOLOR_SIDEBAR, fg="#BDD7EE").pack(padx=20, pady=(12, 2), anchor="w")
entry_wiek_min = tk.Entry(sidebar, justify="center", width=16,
                           font=("Helvetica", 11),
                           bg="#243F5C", fg="white",
                           insertbackground="white",
                           relief="flat", bd=6)
entry_wiek_min.insert(0, "27")
entry_wiek_min.pack(padx=16, pady=(0, 8), fill="x")

# Wiek - do
tk.Label(sidebar, text="Wiek do:",
         font=("Helvetica", 9, "bold"),
         bg=KOLOR_SIDEBAR, fg="#BDD7EE").pack(padx=20, pady=(4, 2), anchor="w")
entry_wiek_max = tk.Entry(sidebar, justify="center", width=16,
                           font=("Helvetica", 11),
                           bg="#243F5C", fg="white",
                           insertbackground="white",
                           relief="flat", bd=6)
entry_wiek_max.insert(0, "59")
entry_wiek_max.pack(padx=16, pady=(0, 8), fill="x")

# Wybór płci
tk.Label(sidebar, text="Płeć:",
         font=("Helvetica", 9, "bold"),
         bg=KOLOR_SIDEBAR, fg="#BDD7EE").pack(padx=20, pady=(4, 2), anchor="w")
var_plec = tk.StringVar(value="Wszyscy")
option_plec = tk.OptionMenu(sidebar, var_plec, "Wszyscy", "Male", "Female")
option_plec.config(bg="#243F5C", fg="white", relief="flat",
                   font=("Helvetica", 10), width=14,
                   activebackground="#2E86C1",
                   highlightthickness=0)
option_plec["menu"].config(bg="#243F5C", fg="white")
option_plec.pack(padx=16, pady=(0, 14), fill="x")

tk.Frame(sidebar, bg="#2E5F8A", height=1).pack(fill="x", padx=16, pady=4)

# Przycisk filtruj
btn_filtruj = tk.Button(sidebar, text="🔍  Filtruj i analizuj",
                         command=filtruj_dane,
                         bg="#27AE60", fg="white",
                         relief="flat", bd=0,
                         font=("Helvetica", 10, "bold"),
                         padx=14, pady=10,
                         cursor="hand2",
                         activebackground="#1E8449",
                         activeforeground="white")
btn_filtruj.pack(fill="x", padx=16, pady=(10, 6))

# Status
label_status = tk.Label(sidebar, text="",
                          font=("Helvetica", 8),
                          bg=KOLOR_SIDEBAR, fg="#7FB3D3",
                          wraplength=190)
label_status.pack(padx=16, pady=4, anchor="w")

# Wersja programu (na dole)
tk.Label(sidebar, text="v1.0  |  Python + tkinter",
         font=("Helvetica", 7),
         bg=KOLOR_SIDEBAR, fg="#4A7FA8").pack(side="bottom", pady=14)


# Zawartość
content = tk.Frame(main_frame, bg=KOLOR_TLO)
content.pack(side="left", fill="both", expand=True)

# STYL ZAKŁADEK
style = ttk.Style()
style.theme_use("default")
style.configure("Medical.TNotebook",
                background=KOLOR_TLO,
                borderwidth=0)
style.configure("Medical.TNotebook.Tab",
                background="#D6E4F0",
                foreground=KOLOR_TEKST,
                font=("Helvetica", 10, "bold"),
                padding=[20, 8],
                borderwidth=0)
style.map("Medical.TNotebook.Tab",
          background=[("selected", KOLOR_ACCENT)],
          foreground=[("selected", "white")])

notebook = ttk.Notebook(content, style="Medical.TNotebook")
notebook.pack(fill="both", expand=True, padx=16, pady=12)

# ZAKŁADKA 1: ANALIZA
tab_analiza = tk.Frame(notebook, bg=KOLOR_TLO)
notebook.add(tab_analiza, text="  📊  Analiza  ")

# Karty statystyk
frame_karty = tk.Frame(tab_analiza, bg=KOLOR_TLO)
frame_karty.pack(fill="x", padx=10, pady=(12, 8))

def zrob_karte(parent, tytul, domyslna_val, kolor_tytul=KOLOR_SZARY):
    karta = tk.Frame(parent, bg=KOLOR_KARTA,
                     relief="flat", bd=0,
                     highlightbackground=KOLOR_BORDER,
                     highlightthickness=1)
    karta.pack(side="left", fill="both", expand=True, padx=6, pady=4)
    tk.Label(karta, text=tytul,
             font=("Helvetica", 8, "bold"),
             bg=KOLOR_KARTA, fg=kolor_tytul).pack(pady=(10, 2))
    val_label = tk.Label(karta, text=domyslna_val,
                          font=("Helvetica", 18, "bold"),
                          bg=KOLOR_KARTA, fg=KOLOR_TEKST)
    val_label.pack(pady=(0, 10))
    return val_label

karta_liczba_val = zrob_karte(frame_karty, "LICZBA PACJENTÓW", "—")
karta_kroki_val  = zrob_karte(frame_karty, "ŚR. KROKÓW / DZIEŃ", "—")
karta_sen_val    = zrob_karte(frame_karty, "ŚR. JAKOŚĆ SNU", "—")
karta_status_val = zrob_karte(frame_karty, "STATUS", "—")

# Wykresy analizy
frame_wykres_analiza = tk.Frame(tab_analiza, bg=KOLOR_TLO)
frame_wykres_analiza.pack(fill="both", expand=True, padx=10, pady=(0, 10))

# ZAKŁADKA 2: PORÓWNANIE GRUP
tab_porownanie = tk.Frame(notebook, bg=KOLOR_TLO)
notebook.add(tab_porownanie, text="  👥  Porównanie grup  ")

btn_porownaj = tk.Button(tab_porownanie,
                          text="▶  Wygeneruj porównanie grup",
                          command=porownaj_grupy,
                          bg=KOLOR_ACCENT, fg="white",
                          relief="flat", bd=0,
                          font=("Helvetica", 10, "bold"),
                          padx=20, pady=10,
                          cursor="hand2",
                          activebackground=KOLOR_BTN_HOVER)
btn_porownaj.pack(pady=(16, 8))

tk.Label(tab_porownanie,
         text="Porównuje kroki i jakość snu między grupami wiekowymi, płcią i kategoriami BMI",
         font=("Helvetica", 9), bg=KOLOR_TLO, fg=KOLOR_SZARY).pack()

frame_wykres_porownanie = tk.Frame(tab_porownanie, bg=KOLOR_TLO)
frame_wykres_porownanie.pack(fill="both", expand=True, padx=10, pady=(8, 10))

# ZAKŁADKA 3: EKSPORT
tab_eksport = tk.Frame(notebook, bg=KOLOR_TLO)
notebook.add(tab_eksport, text="  💾  Eksport  ")

frame_eksport_center = tk.Frame(tab_eksport, bg=KOLOR_TLO)
frame_eksport_center.pack(expand=True)

tk.Label(frame_eksport_center,
         text="Eksport raportu",
         font=("Helvetica", 16, "bold"),
         bg=KOLOR_TLO, fg=KOLOR_TEKST).pack(pady=(40, 6))

tk.Label(frame_eksport_center,
         text="Zapisuje przefiltrowane dane do pliku CSV\noraz generuje raport PDF z wykresami i statystykami.",
         font=("Helvetica", 10),
         bg=KOLOR_TLO, fg=KOLOR_SZARY,
         justify="center").pack(pady=(0, 24))

# Infobox
info_box = tk.Frame(frame_eksport_center, bg="#EBF5FB",
                     highlightbackground=KOLOR_BORDER,
                     highlightthickness=1)
info_box.pack(pady=(0, 24), padx=40, fill="x")

tk.Label(info_box,
         text="ℹ️   Przed eksportem ustaw filtry w pasku bocznym\ni kliknij 'Filtruj i analizuj' w zakładce Analiza.",
         font=("Helvetica", 9),
         bg="#EBF5FB", fg="#1B4F72",
         justify="left").pack(padx=16, pady=12)

btn_eksport = tk.Button(frame_eksport_center,
                         text="💾  Eksportuj CSV + PDF",
                         command=eksportuj_raport,
                         bg="#E74C3C", fg="white",
                         relief="flat", bd=0,
                         font=("Helvetica", 12, "bold"),
                         padx=32, pady=14,
                         cursor="hand2",
                         activebackground="#C0392B")
btn_eksport.pack()

label_status_eksport = tk.Label(frame_eksport_center, text="",
                                  font=("Helvetica", 10),
                                  bg=KOLOR_TLO, fg="#27AE60")
label_status_eksport.pack(pady=16)

root.mainloop()