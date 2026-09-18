"""Widoki aplikacji: jedna funkcja `pokaz_*` = jeden ekran wybierany przyciskiem."""

import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from constants import KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW, KLASYFIKACJA_OPISY
from data_processing import filtruj_przekroczenia, zbuduj_liste_wynikow
from aggregations import policz_wg_kolumny, policz_wg_grupy_wiekowej
from charts import zbuduj_dashboard_przekroczenia, zbuduj_wykres_liczebnosci, zbuduj_wykres_kolowy_liczebnosci
from widgets import zbuduj_tabele, zbuduj_panel_podsumowania, Tooltip


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


def pokaz_dashboard_przekroczenia(parent, dane):
    pacjenci = filtruj_przekroczenia(dane)
    fig = zbuduj_dashboard_przekroczenia(pacjenci)
    return _osadz_wykres(parent, fig)

def pokaz_analize_przyczyn(parent, dane):
    """Widok 'Analiza przyczyn przekroczeń' – panel podsumowania + tabela z checkboxami."""
    pacjenci = filtruj_przekroczenia(dane)
    wyniki = zbuduj_liste_wynikow(pacjenci)

    zbuduj_panel_podsumowania(parent, wyniki, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW)

    kolumny, naglowki, szerokosci, kotwice = _kolumny_tabeli_przyczyn()
    tabela = zbuduj_tabele(parent, kolumny, naglowki, szerokosci, kotwice)

    for (_, wiersz), wynik in zip(pacjenci.iterrows(), wyniki):
        tabela.insert("", "end", values=_wiersz_tabeli_przyczyn(wiersz["patient_id"], wynik))

    _dodaj_tooltip_klasyfikacji(tabela)

    return tabela

def pokaz_liczbe_pacjentow_wg_wieku(parent, dane):
    counts = policz_wg_grupy_wiekowej(dane)
    fig = zbuduj_wykres_liczebnosci(counts, "Liczba pacjentów wg wieku")
    return _osadz_wykres(parent, fig)