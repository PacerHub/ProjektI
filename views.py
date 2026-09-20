"""Widoki aplikacji: jedna funkcja `pokaz_*` = jeden ekran wybierany przyciskiem."""

import pandas as pd
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from aggregations import (
    policz_wg_kolumny, policz_wg_grupy_wiekowej, policz_klasyfikacje,
    wygeneruj_wnioski_pareto, wygeneruj_wnioski_analizy,
)
from constants import KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW, KLASYFIKACJA_OPISY
from widgets import zbuduj_tabele, zbuduj_panel_podsumowania, Tooltip
from data_processing import filtruj_przekroczenia, zbuduj_liste_wynikow, filtruj_bezpieczne
from charts import (
    zbuduj_dashboard_przekroczenia, zbuduj_wykres_liczebnosci,
    zbuduj_wykres_kolowy_liczebnosci, zbuduj_wykres_pareto,
)

def _osadz_wykres(parent, fig):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return canvas


def pokaz_liczebnosc_wg_kolumny(parent, dane, kolumna, tytul, sortuj_wg_indeksu=False, typ_wykresu="slupkowy", kolory=None):
    counts = policz_wg_kolumny(filtruj_bezpieczne(dane), kolumna, sortuj_wg_indeksu)

    if typ_wykresu == "kolowy":
        fig = zbuduj_wykres_kolowy_liczebnosci(counts, tytul, kolory)
    else:
        fig = zbuduj_wykres_liczebnosci(counts, tytul, kolory)

    return _osadz_wykres(parent, fig)


def pokaz_dashboard_przekroczenia(parent, dane):
    pacjenci = filtruj_przekroczenia(filtruj_bezpieczne(dane))
    fig = zbuduj_dashboard_przekroczenia(pacjenci)
    return _osadz_wykres(parent, fig)

def _kolumny_tabeli_przyczyn():
    """Definicja kolumn tabeli: nazwy, nagłówki, szerokości, wyrównanie."""
    kolumny = ("patient_id", "okolica", "bmi", "kategoria_faz", "procent", "klasyfikacja", *KLUCZE_CZYNNIKOW)

    naglowki = {
        "patient_id": "Pacjent",
        "okolica": "Okolica anatomiczna",
        "bmi": "BMI (kategoria)",
        "kategoria_faz": "Liczba faz",
        "procent": "% przekroczenia",
        "klasyfikacja": "Klasyfikacja przyczyny",
        "pediatryczny": "<16 lat",
        "onkologiczny": "Onko",
        "wielofazowy": "Wielofazowe",
        "wysoki_dlp_fazy": "Wysokie DLP",
        "nadwaga_otylosc": "Nadwaga/\notyłość",
    }

    szerokosci = {
        "patient_id": 65,
        "okolica": 130,
        "bmi": 150,
        "kategoria_faz": 80,
        "procent": 100,
        "klasyfikacja": 200,
        **{klucz: 85 for klucz in KLUCZE_CZYNNIKOW},
    }

    kotwice = {"okolica": "w", "klasyfikacja": "w"}

    return kolumny, naglowki, szerokosci, kotwice


def _wiersz_tabeli_przyczyn(patient_id, wynik):
    """Buduje krotkę wartości do wstawienia w jeden wiersz tabeli przyczyn."""
    etykieta_pacjenta = f"⚠ {patient_id}" if wynik.get("podejrzany") else patient_id
    bmi_tekst = (
        f"{wynik['bmi']} ({wynik['kategoria_bmi']})" if wynik["bmi"] is not None else wynik["kategoria_bmi"]
    )
    procent_tekst = (
        f"{wynik['procent_przekroczenia']:+.3f}%" if wynik["procent_przekroczenia"] is not None else "—"
    )
    return (
        etykieta_pacjenta,
        wynik["okolica"],
        bmi_tekst,
        wynik["kategoria_faz"],
        procent_tekst,
        wynik["klasyfikacja"],
        *("✓" if wynik["factors"][klucz] else "" for klucz in KLUCZE_CZYNNIKOW),
    )


def _dodaj_tooltip_klasyfikacji(tabela):
    """Podpina tooltip z opisem klasyfikacji przyczyny do kolumny 'klasyfikacja'."""
    return Tooltip(
        tabela,
        kolumna_docelowa="#6",
        pobierz_tekst=lambda wiersz_id: KLASYFIKACJA_OPISY.get(
            tabela.set(wiersz_id, "klasyfikacja"),
            "Brak dodatkowego opisu dla tej klasyfikacji.",
        ),
    )

def pokaz_analize_przyczyn(parent, dane):
    pacjenci = filtruj_przekroczenia(dane)
    wyniki = zbuduj_liste_wynikow(pacjenci)

    zbuduj_panel_podsumowania(parent, wyniki, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW)

    tk.Label(
        parent,
        text=wygeneruj_wnioski_analizy(wyniki),
        font=("Cambria", 10),
        wraplength=1100,
        justify="center",
        pady=8,
    ).pack(fill="x")

    kolumny, naglowki, szerokosci, kotwice = _kolumny_tabeli_przyczyn()
    tabela = zbuduj_tabele(parent, kolumny, naglowki, szerokosci, kotwice)
    tabela.tag_configure("podejrzany", background="#fff3cd")

    for (_, wiersz), wynik in zip(pacjenci.iterrows(), wyniki):
        tagi = ("podejrzany",) if wynik.get("podejrzany") else ()
        tabela.insert("", "end", values=_wiersz_tabeli_przyczyn(wiersz["patient_id"], wynik), tags=tagi)

    _dodaj_tooltip_klasyfikacji(tabela)

    return tabela

def pokaz_liczbe_pacjentow_wg_wieku(parent, dane):
    counts = policz_wg_grupy_wiekowej(filtruj_bezpieczne(dane))
    fig = zbuduj_wykres_liczebnosci(counts, "Liczba pacjentów wg wieku")
    return _osadz_wykres(parent, fig)

def pokaz_pareto_przyczyn(parent, dane):
    """Widok 'Pareto przyczyn przekroczeń' - które przyczyny odpowiadają za większość przypadków."""
    pacjenci = filtruj_przekroczenia(filtruj_bezpieczne(dane))
    wyniki = zbuduj_liste_wynikow(pacjenci)
    counts = policz_klasyfikacje(wyniki)
    fig = zbuduj_wykres_pareto(counts)
    tk.Label(
        parent,
        text=wygeneruj_wnioski_pareto(counts),
        font=("Cambria", 10),
        wraplength=1100,
        justify="center",
        pady=8,
    ).pack(side="bottom", fill="x")
    return _osadz_wykres(parent, fig)


