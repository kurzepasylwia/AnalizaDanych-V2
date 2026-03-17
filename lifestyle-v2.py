import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, messagebox
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
header = tk.Label(
    root,
    text="Analiza kroków dziennych, BMI i jakości snu",
    font=("Arial", 18, "bold"),
    bg="#2C3E50", fg="white", pady=15
)
header.pack(fill="x")

# PANEL FORMULARZA
frame_form = tk.Frame(root, bg="#ecf0f1")
frame_form.pack(pady=15)

# Etykiety - wiersz 0
tk.Label(frame_form, text="Wiek od:", font=("Arial", 9),
         bg="#ecf0f1", fg="#333333").grid(row=0, column=1, padx=5)
tk.Label(frame_form, text="Wiek do:", font=("Arial", 9),
         bg="#ecf0f1", fg="#333333").grid(row=0, column=2, padx=5)
tk.Label(frame_form, text="Płeć:", font=("Arial", 9),
         bg="#ecf0f1", fg="#333333").grid(row=0, column=3, padx=5)

# Przyciski i pola - wiersz 1
btn_wczytaj = tk.Button(
    frame_form, text="Wczytaj CSV", command=wczytaj_plik,
    bg="#3498db", fg="white", relief="flat", padx=12, pady=8
)
btn_wczytaj.grid(row=1, column=0, padx=6)

entry_wiek_min = tk.Entry(frame_form, justify="center", width=7)
entry_wiek_min.insert(0, "27")
entry_wiek_min.grid(row=1, column=1, padx=5)

entry_wiek_max = tk.Entry(frame_form, justify="center", width=7)
entry_wiek_max.insert(0, "59")
entry_wiek_max.grid(row=1, column=2, padx=5)

var_plec = tk.StringVar(value="Wszyscy")
option_plec = tk.OptionMenu(frame_form, var_plec, "Wszyscy", "Male", "Female")
option_plec.config(bg="white", relief="flat", width=8)
option_plec.grid(row=1, column=3, padx=5)

btn_filtruj = tk.Button(
    frame_form, text="Filtruj i analizuj", command=filtruj_dane,
    bg="#2ecc71", fg="white", relief="flat", padx=12, pady=8
)
btn_filtruj.grid(row=1, column=4, padx=6)

btn_porownaj = tk.Button(
    frame_form, text="Porównaj grupy", command=porownaj_grupy,
    bg="#e67e22", fg="white", relief="flat", padx=12, pady=8
)
btn_porownaj.grid(row=1, column=5, padx=6)

btn_eksport = tk.Button(
    frame_form, text="Eksportuj raport", command=eksportuj_raport,
    bg="#c0392b", fg="white", relief="flat", padx=12, pady=8
)
btn_eksport.grid(row=1, column=6, padx=6)

label_status = tk.Label(root, text="", bg="#ecf0f1", font=("Arial", 9))
label_status.pack()

# PANEL STATYSTYK
panel_statystyki = tk.Frame(root, bg="white", bd=1, relief="solid")
panel_statystyki.pack(pady=8, padx=50, fill="x")

tk.Label(panel_statystyki, text="Panel statystyk",
         font=("Arial", 14, "bold"), bg="white").pack(pady=5)

label_wyniki = tk.Label(panel_statystyki, text="", font=("Arial", 12), bg="white")
label_wyniki.pack(pady=8)

# PANEL WYKRESÓW
frame_wykresy = tk.Frame(root, bg="#ecf0f1")
frame_wykresy.pack(fill="both", expand=True, padx=40, pady=10)

root.mainloop()
