import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk


# =========================
# WCZYTANIE DANYCH
# =========================

dane = pd.read_csv("ct_patients_data.csv")

dane["dlp_referencyjny_lacznie"] = (
        dane["dlp_referencyjny_na_faze_mGy_cm"]
        * dane["liczba_faz"]
)

dane["przekroczenie_dlp"] = (
        dane["dlp_zmierzony_lacznie_mGy_cm"]
        > dane["dlp_referencyjny_lacznie"]
)

dane["przekroczenie_o"] = (
        dane["dlp_zmierzony_lacznie_mGy_cm"]
        - dane["dlp_referencyjny_lacznie"]
)


# =========================
# FUNKCJA POKAZUJĄCA WYKRES
# =========================

def pokaz_wykres(event=None):
    global canvas

    wybrany_wykres = wybor.get()

    if wybrany_wykres == "Liczba pacjentów wg rodzaju badania":
        liczba_badan = dane["rodzaj_badania_tk"].value_counts()

    elif wybrany_wykres == "Liczba pacjentów wg wieku":
        liczba_badan = dane["wiek"].value_counts().sort_index()

    elif wybrany_wykres == "Liczba pacjentów wg płci":
        liczba_badan = dane["plec"].value_counts().sort_index()

    elif wybrany_wykres == "Pacjenci z przekroczoną dawką":
        liczba_badan = dane["przekroczenie_dlp"].value_counts()

        pacjenci_przekroczenie = dane[dane["przekroczenie_dlp"] == True]

        tabela = ttk.Treeview(
            miejsce_na_wykres,
            columns=(
                "patient_id",
                "wiek",
                "badanie",
                "fazy",
                "onkologiczny",
                "dlp_referencyjny",
                "dlp_zmierzony",
                "przekroczenie"
            ),
            show="headings"
        )

        tabela.heading("patient_id", text="Pacjent")
        tabela.heading("wiek", text="Wiek")
        tabela.heading("badanie", text="Rodzaj badania")
        tabela.heading("fazy", text="Liczba faz")
        tabela.heading("onkologiczny", text="Protokół onkologiczny")
        tabela.heading("dlp_referencyjny", text="DLP referencyjne")
        tabela.heading("dlp_zmierzony", text="DLP zmierzone")
        tabela.heading("przekroczenie", text="Przekroczenie")

        tabela.pack(fill="both", expand=True)

        for _, wiersz in pacjenci_przekroczenie.iterrows():
            tabela.insert(
                "",
                "end",
                values=(
                    wiersz["patient_id"],
                    wiersz["wiek"],
                    wiersz["rodzaj_badania_tk"],
                    wiersz["liczba_faz"],
                    wiersz["protokol_onkologiczny_jamy_brzusznej"],
                    wiersz["dlp_referencyjny_lacznie"],
                    wiersz["dlp_zmierzony_lacznie_mGy_cm"],
                    wiersz["przekroczenie_o"]
                )
            )

        return
    # Tworzymy wykres
    fig, ax = plt.subplots(figsize=(10, 6))

    # Jeżeli istnieje poprzedni wykres - usuwamy go
    if canvas is not None:
        canvas.get_tk_widget().destroy()

    print("Wybrano:", wybrany_wykres)

    # Rysowanie wykresu
    liczba_badan.plot(kind="bar", ax=ax)

    ax.set_title(wybrany_wykres)
    ax.set_xlabel(wybrany_wykres)
    ax.set_yticks(range(0, liczba_badan.max() + 1))
    ax.set_ylabel("Liczba pacjentów")

    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    # Umieszczenie wykresu w Tkinterze
    canvas = FigureCanvasTkAgg(
        fig,
        master=miejsce_na_wykres
    )

    canvas.draw()

    canvas.get_tk_widget().pack(
        fill="both",
        expand=True
    )


# =========================
# TWORZYMY GŁÓWNE OKNO
# =========================

okno = tk.Tk()

okno.title("Analiza dawek TK")
okno.geometry("800x600")


# =========================
# NAPIS
# =========================

napis = tk.Label(
    okno,
    text="Analiza danych pacjentów TK",
    font=("Arial", 18)
)

napis.pack(pady=30)


# =========================
# PANEL WYBORU
# =========================

panel_wyboru = tk.Frame(okno)
panel_wyboru.pack(pady=10)


rodzaje_wykresow = [
    "Liczba pacjentów wg rodzaju badania",
    "Liczba pacjentów wg wieku",
    "Liczba pacjentów wg płci",
    "Pacjenci z przekroczoną dawką"
]


wybor = ttk.Combobox(
    panel_wyboru,
    values=rodzaje_wykresow,
    state="readonly"
)

wybor.pack(side="left", padx=5)

wybor.set(rodzaje_wykresow[0])

wybor.bind("<<ComboboxSelected>>", pokaz_wykres)


# =========================
# PRZYCISK
# =========================

#przycisk = tk.Button(
    #panel_wyboru,
    #text="Pokaż wykres",
    #command=pokaz_wykres
#)

#przycisk.pack(side="left", padx=5)


# =========================
# MIEJSCE NA WYKRES
# =========================

miejsce_na_wykres = tk.Frame(okno)

miejsce_na_wykres.pack(
    fill="both",
    expand=True
)


# Na początku nie ma jeszcze wykresu
canvas = None

print(dane[[
    "patient_id",
    "dlp_referencyjny_lacznie",
    "dlp_zmierzony_lacznie_mGy_cm",
    "przekroczenie_dlp"
]])


# =========================
# URUCHOMIENIE PROGRAMU
# =================

okno.mainloop()
