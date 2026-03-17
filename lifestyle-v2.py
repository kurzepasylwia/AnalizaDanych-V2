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

    label_wyniki.config(
        text=f"Liczba pacjentów: {liczba}   |   Śr. kroków/dzień: {srednie_kroki:.0f}   |   Śr. jakość snu: {srednia_sen:.2f}/10\nStatus: {status}",
        fg=kolor
    )

    rysuj_wykresy_glowne(przefiltrowane)


def rysuj_wykresy_glowne(przefiltrowane):
    for widget in frame_wykresy.winfo_children():
        widget.destroy()

    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    fig.patch.set_facecolor("#f8f9fa")

    for ax in axs:
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#cccccc")
        ax.spines["bottom"].set_color("#cccccc")
        ax.tick_params(colors="#555555", labelsize=9)
        ax.grid(True, axis="y", alpha=0.4, linestyle="--", color="#dddddd")

    kolory = {"Male": "#4a7dc4", "Female": "#e05c5c"}
    kolory_bmi = {"Normal": "#27ae60", "Overweight": "#f39c12", "Obese": "#e74c3c"}

    # Wykres 1: Scatter kroków vs jakość snu
    for plec in przefiltrowane["Gender"].unique():
        dane = przefiltrowane[przefiltrowane["Gender"] == plec]
        axs[0].scatter(
            dane["Daily Steps"], dane["Quality of Sleep"],
            color=kolory.get(plec, "#999999"),
            alpha=0.7, s=50, edgecolors="white", linewidths=0.5, label=plec
        )
    z = np.polyfit(przefiltrowane["Daily Steps"], przefiltrowane["Quality of Sleep"], 1)
    p = np.poly1d(z)
    x_sorted = np.sort(przefiltrowane["Daily Steps"])
    axs[0].plot(x_sorted, p(x_sorted), color="#333333",
                linewidth=2, linestyle="--", alpha=0.6, label="Trend")
    axs[0].set_title("Liczba kroków vs Jakość snu",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[0].set_xlabel("Liczba kroków dziennie", color="#555555")
    axs[0].set_ylabel("Jakość snu (1-10)", color="#555555")
    axs[0].legend(fontsize=9, framealpha=0.5)
    axs[0].grid(True, alpha=0.3, linestyle="--", color="#dddddd")

    # Wykres 2: Średnia kroków wg BMI
    kolejnosc = [k for k in ["Normal", "Overweight", "Obese"]
                 if k in przefiltrowane["BMI Category"].unique()]
    srednie_bmi = przefiltrowane.groupby("BMI Category")["Daily Steps"].mean().reindex(kolejnosc)
    kolory_bar = [kolory_bmi.get(k, "#999999") for k in kolejnosc]
    bars = axs[1].bar(srednie_bmi.index, srednie_bmi.values,
                      color=kolory_bar, edgecolor="white", linewidth=1, width=0.5)
    for bar, val in zip(bars, srednie_bmi.values):
        axs[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                    f"{val:.0f}", ha="center", va="bottom",
                    fontsize=9, color="#333333", fontweight="bold")
    axs[1].set_title("Średnia liczba kroków wg BMI",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[1].set_ylabel("Średnia liczba kroków", color="#555555")
    axs[1].set_ylim(bottom=max(0, srednie_bmi.values.min() - 1000))

    # Wykres 3: Boxplot jakości snu wg BMI
    dane_boxplot = [
        przefiltrowane[przefiltrowane["BMI Category"] == k]["Quality of Sleep"].dropna()
        for k in kolejnosc
    ]
    bp = axs[2].boxplot(
        dane_boxplot, labels=kolejnosc, patch_artist=True,
        medianprops=dict(color="white", linewidth=2.5),
        whiskerprops=dict(color="#555555", linewidth=1.2),
        capprops=dict(color="#555555", linewidth=1.2),
        flierprops=dict(marker="o", markerfacecolor="#f39c12", markersize=5, alpha=0.6)
    )
    for patch, kolor in zip(bp["boxes"], [kolory_bmi.get(k, "#999999") for k in kolejnosc]):
        patch.set_facecolor(kolor)
        patch.set_alpha(0.7)
    axs[2].set_title("Jakość snu wg kategorii BMI",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[2].set_ylabel("Jakość snu (1-10)", color="#555555")

    plt.tight_layout(pad=2.0)
    canvas = FigureCanvasTkAgg(fig, master=frame_wykresy)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)



# PORÓWNANIE GRUP

def porownaj_grupy():
    global df
    if df is None:
        label_status.config(text="❌ Najpierw wczytaj plik!", fg="red")
        return

    dane = df.copy()
    dane["BMI Category"] = dane["BMI Category"].replace({"Normal Weight": "Normal"})

    for widget in frame_wykresy.winfo_children():
        widget.destroy()

    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    fig.patch.set_facecolor("#f8f9fa")

    for ax in axs:
        ax.set_facecolor("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#cccccc")
        ax.spines["bottom"].set_color("#cccccc")
        ax.tick_params(colors="#555555", labelsize=9)
        ax.grid(True, axis="y", alpha=0.4, linestyle="--", color="#dddddd")

    szerokosc = 0.35

    # Wykres 1: Kroki wg grupy wiekowej i płci
    dane["Grupa wiekowa"] = pd.cut(dane["Age"], bins=[0, 35, 45, 60],
                                    labels=["Mlodsi (<35)", "Sredni (35-45)", "Starsi (>45)"])
    srednie = dane.groupby(["Grupa wiekowa", "Gender"], observed=True)["Daily Steps"].mean().unstack()
    x = np.arange(len(srednie.index))
    axs[0].bar(x - szerokosc/2, srednie.get("Male", [0]*len(x)),
               szerokosc, label="Male", color="#4a7dc4", edgecolor="white")
    axs[0].bar(x + szerokosc/2, srednie.get("Female", [0]*len(x)),
               szerokosc, label="Female", color="#e05c5c", edgecolor="white")
    axs[0].set_xticks(x)
    axs[0].set_xticklabels(srednie.index, fontsize=8)
    axs[0].set_title("Kroki wg grupy wiekowej i płci",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[0].set_ylabel("Średnia liczba kroków", color="#555555")
    axs[0].legend(fontsize=9)

    # Wykres 2: Boxplot jakości snu wg płci
    grupy_plec = [dane[dane["Gender"] == p]["Quality of Sleep"].dropna()
                  for p in ["Male", "Female"]]
    bp = axs[1].boxplot(grupy_plec, labels=["Male", "Female"], patch_artist=True,
                        medianprops=dict(color="white", linewidth=2.5),
                        whiskerprops=dict(color="#555555"),
                        capprops=dict(color="#555555"))
    for patch, kolor in zip(bp["boxes"], ["#4a7dc4", "#e05c5c"]):
        patch.set_facecolor(kolor)
        patch.set_alpha(0.7)
    axs[1].set_title("Jakość snu wg płci",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[1].set_ylabel("Jakość snu (1-10)", color="#555555")

    # Wykres 3: Kroki wg BMI i płci
    kolejnosc_bmi = [k for k in ["Normal", "Overweight", "Obese"]
                     if k in dane["BMI Category"].unique()]
    bmi_plec = dane.groupby(["BMI Category", "Gender"])["Daily Steps"].mean().unstack()
    bmi_plec = bmi_plec.reindex(kolejnosc_bmi)
    x2 = np.arange(len(kolejnosc_bmi))
    axs[2].bar(x2 - szerokosc/2, bmi_plec.get("Male", [0]*len(x2)),
               szerokosc, label="Male", color="#4a7dc4", edgecolor="white")
    axs[2].bar(x2 + szerokosc/2, bmi_plec.get("Female", [0]*len(x2)),
               szerokosc, label="Female", color="#e05c5c", edgecolor="white")
    axs[2].set_xticks(x2)
    axs[2].set_xticklabels(kolejnosc_bmi, fontsize=9)
    axs[2].set_title("Kroki wg BMI i płci",
                     fontsize=11, fontweight="bold", color="#333333", pad=10)
    axs[2].set_ylabel("Średnia liczba kroków", color="#555555")
    axs[2].legend(fontsize=9)

    plt.tight_layout(pad=2.0)
    canvas = FigureCanvasTkAgg(fig, master=frame_wykresy)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    label_wyniki.config(
        text=f"Tryb: Porównanie grup   |   Wszyscy pacjenci: {len(dane)}   |   Kobiety: {len(dane[dane['Gender']=='Female'])}   |   Mężczyźni: {len(dane[dane['Gender']=='Male'])}",
        fg="#2c3e50"
    )


# EKSPORT CSV + PDF

def eksportuj_raport():
    global df
    if df is None:
        label_status.config(text="❌ Brak danych do eksportu!", fg="red")
        return

    przefiltrowane = pobierz_przefiltrowane()
    if przefiltrowane is None or przefiltrowane.empty:
        messagebox.showwarning("Brak danych", "Najpierw ustaw filtry i kliknij 'Filtruj i analizuj'.")
        return

    # --- Eksport CSV ---
    sciezka_csv = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Zapisz dane jako CSV"
    )
    if sciezka_csv:
        przefiltrowane.to_csv(sciezka_csv, index=False)

    # --- Eksport PDF ---
    sciezka_pdf = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        title="Zapisz raport PDF"
    )
    if not sciezka_pdf:
        return

    # Generowanie wykresu do PDF
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    kolory_bmi = {"Normal": "#27ae60", "Overweight": "#f39c12", "Obese": "#e74c3c"}
    kolejnosc = [k for k in ["Normal", "Overweight", "Obese"]
                 if k in przefiltrowane["BMI Category"].unique()]
    kolory_scatter = {"Male": "#4a7dc4", "Female": "#e05c5c"}

    for plec in przefiltrowane["Gender"].unique():
        dane = przefiltrowane[przefiltrowane["Gender"] == plec]
        axs[0].scatter(dane["Daily Steps"], dane["Quality of Sleep"],
                       color=kolory_scatter.get(plec, "#999"),
                       alpha=0.6, s=30, label=plec)
    axs[0].set_title("Kroki vs Jakość snu")
    axs[0].set_xlabel("Kroki dziennie")
    axs[0].set_ylabel("Jakość snu")
    axs[0].legend(fontsize=8)

    srednie_bmi = przefiltrowane.groupby("BMI Category")["Daily Steps"].mean().reindex(kolejnosc)
    axs[1].bar(srednie_bmi.index, srednie_bmi.values,
               color=[kolory_bmi.get(k, "#999") for k in kolejnosc],
               edgecolor="white")
    axs[1].set_title("Średnia liczba kroków wg BMI")
    axs[1].set_ylabel("Kroki")

    plt.tight_layout()
    wykres_path = "wykres_raport_temp.png"
    fig.savefig(wykres_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Tworzenie PDF
    c = pdf_canvas.Canvas(sciezka_pdf, pagesize=A4)
    szerokosc, wysokosc = A4

    # Nagłówek
    c.setFillColorRGB(0.17, 0.24, 0.31)
    c.rect(0, wysokosc - 80, szerokosc, 80, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, wysokosc - 45, "Raport analizy danych medycznych")
    c.setFont("Helvetica", 10)
    c.drawString(50, wysokosc - 65, "Analiza: dzienna liczba kroków vs BMI i jakość snu")

    # Statystyki
    c.setFillColorRGB(0.17, 0.24, 0.31)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, wysokosc - 115, "Statystyki ogólne")

    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 11)
    wiek_min = entry_wiek_min.get()
    wiek_max = entry_wiek_max.get()
    plec_filtr = var_plec.get()

    statystyki = [
        f"Zastosowane filtry:  Wiek {wiek_min}-{wiek_max} lat,  Płeć: {plec_filtr}",
        f"Liczba pacjentów w analizie: {len(przefiltrowane)}",
        f"Średnia liczba kroków dziennie: {przefiltrowane['Daily Steps'].mean():.0f}",
        f"Średnia jakość snu: {przefiltrowane['Quality of Sleep'].mean():.2f} / 10",
        f"Mediana jakości snu: {przefiltrowane['Quality of Sleep'].median():.1f}",
        f"Min. kroki: {przefiltrowane['Daily Steps'].min():.0f}   |   Max. kroki: {przefiltrowane['Daily Steps'].max():.0f}",
    ]

    y = wysokosc - 140
    for linia in statystyki:
        c.drawString(50, y, linia)
        y -= 20

    # Tabela BMI
    c.setFillColorRGB(0.17, 0.24, 0.31)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, "Średnie kroki wg kategorii BMI:")
    y -= 30
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    for kat in kolejnosc:
        srednia = przefiltrowane[przefiltrowane["BMI Category"] == kat]["Daily Steps"].mean()
        c.drawString(70, y, f"{kat}: {srednia:.0f} kroków/dzień")
        y -= 18

    # Wykres
    c.drawImage(wykres_path, 40, y - 260, width=510, height=240)

    # Stopka
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 25, "Wygenerowano automatycznie przez System analizy danych medycznych")

    c.save()

    if os.path.exists(wykres_path):
        os.remove(wykres_path)

    label_status.config(text="✅ Raport CSV i PDF zapisany!", fg="#27ae60")



### GUI

root = tk.Tk()
root.title("Analiza kroków, BMI i jakości snu")
root.configure(bg="#ecf0f1")
root.geometry("1150x720")

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
