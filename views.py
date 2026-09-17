"""Widoki aplikacji: jedna funkcja `pokaz_*` = jeden ekran wybierany przyciskiem."""

import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from constants import KLASYFIKACJA_OPISY
from data_processing import filtruj_przekroczenia, analizuj_pacjenta
from aggregations import policz_wg_kolumny
from charts import zbuduj_wykres_liczebnosci
from widgets import zbuduj_tabele, Tooltip


def _osadz_wykres(parent, fig):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return canvas


def pokaz_liczebnosc_wg_kolumny(parent, dane, kolumna, tytul, sortuj_wg_indeksu=False, typ_wykresu="slupkowy", kolory=None):
    """Widok wspólny dla przycisków 'Liczba pacjentów wg ...' (słupkowy albo kołowy)."""
    counts = policz_wg_kolumny(dane, kolumna, sortuj_wg_indeksu)

    if typ_wykresu == "kolowy":
        fig = zbuduj_wykres_kolowy_liczebnosci(counts, tytul, kolory)
    else:
        fig = zbuduj_wykres_liczebnosci(counts, tytul, kolory)

    return _osadz_wykres(parent, fig)


def pokaz_tabele_przekroczenia(parent, dane):
    """Surowa tabela pacjentów z przekroczoną dawką (docelowo zastąpimy ją dashboardem)."""
    pacjenci = filtruj_przekroczenia(dane)
    kolumny = ("patient_id", "wiek", "badanie", "fazy", "onkologiczny",
               "dlp_referencyjny", "dlp_zmierzony", "przekroczenie", "dlp_lacznie")
    naglowki = {"patient_id": "Pacjent", "wiek": "Wiek", "badanie": "Rodzaj badania",
                "fazy": "Liczba faz", "onkologiczny": "Protokół onkologiczny",
                "dlp_referencyjny": "DPR na fazę", "dlp_zmierzony": "DLP zmierzone na fazę",
                "przekroczenie": "Przekroczenie", "dlp_lacznie": "DLP całego badania \n (informacyjnie)"}
    szerokosci = {"patient_id": 80, "wiek": 60, "badanie": 220, "fazy": 80,
                  "onkologiczny": 160, "dlp_referencyjny": 150, "dlp_zmierzony": 150,
                  "przekroczenie": 120, "dlp_lacznie": 120}
    tabela = zbuduj_tabele(parent, kolumny, naglowki, szerokosci, {"badanie": "w"})

    for _, wiersz in pacjenci.iterrows():
        onko = wiersz["protokol_onkologiczny_jamy_brzusznej"]
        onko_tekst = "nie dotyczy" if pd.isna(onko) else ("tak" if onko else "nie")
        tabela.insert("", "end", values=(
            wiersz["patient_id"], wiersz["wiek"], wiersz["rodzaj_badania_tk"],
            wiersz["liczba_faz"], onko_tekst,
            round(wiersz["dlp_referencyjny_na_faze_mGy_cm"], 1),
            round(wiersz["dlp_zmierzony_na_faze_mGy_cm"], 1),
            round(wiersz["przekroczenie_o"], 1),
            round(wiersz["dlp_zmierzony_lacznie_mGy_cm"], 1),
        ))

    Tooltip(tabela, "#3", lambda wid: tabela.set(wid, "badanie"))
    return tabela


def pokaz_analize_przyczyn(parent, dane):
    pacjenci = filtruj_przekroczenia(dane)
    kolumny = ("patient_id", "okolica", "bmi", "kategoria_faz", "procent", "klasyfikacja", "czynniki")
    naglowki = {"patient_id": "Pacjent", "okolica": "Okolica anatomiczna",
                "bmi": "BMI (kategoria)", "kategoria_faz": "Liczba faz",
                "procent": "% przekroczenia", "klasyfikacja": "Klasyfikacja przyczyny",
                "czynniki": "Aktywne czynniki"}
    szerokosci = {"patient_id": 70, "okolica": 150, "bmi": 160, "kategoria_faz": 90,
                  "procent": 110, "klasyfikacja": 230, "czynniki": 280}
    tabela = zbuduj_tabele(parent, kolumny, naglowki, szerokosci, {"okolica": "w", "klasyfikacja": "w"})

    for _, wiersz in pacjenci.iterrows():
        wynik = analizuj_pacjenta(wiersz)
        tabela.insert("", "end", values=(
            wiersz["patient_id"], wynik["okolica"],
            f"{wynik['bmi']} ({wynik['kategoria_bmi']})", wynik["kategoria_faz"],
            f"{wynik['procent_przekroczenia']:+.3f}%", wynik["klasyfikacja"],
            wynik["aktywne_czynniki"],
        ))

    Tooltip(tabela, "#6", lambda wid: KLASYFIKACJA_OPISY.get(
        tabela.set(wid, "klasyfikacja"), "Brak dodatkowego opisu dla tej klasyfikacji."))
    return tabela

def pokaz_liczbe_pacjentow_wg_wieku(parent, dane):
    counts = policz_wg_grupy_wiekowej(dane)
    fig = zbuduj_wykres_liczebnosci(counts, "Liczba pacjentów wg wieku")
    return _osadz_wykres(parent, fig)