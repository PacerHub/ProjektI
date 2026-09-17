"""Agregacje: zamiana surowych danych na liczby gotowe do wyświetlenia."""
from constants import ETYKIETY_GRUP_WIEKOWYCH
from data_processing import kategoria_wiekowa


def policz_wg_grupy_wiekowej(dane):
    grupy = dane["wiek"].apply(kategoria_wiekowa)
    counts = grupy.value_counts()
    return counts.reindex(ETYKIETY_GRUP_WIEKOWYCH, fill_value=0)

def policz_wg_kolumny(dane, kolumna, sortuj_wg_indeksu=False):
    """Zlicza wystąpienia wartości w danej kolumnie DataFrame."""
    counts = dane[kolumna].value_counts()
    return counts.sort_index() if sortuj_wg_indeksu else counts

def policz_kategorie_onkologiczne(kolumna_onko):
    kategorie = kolumna_onko.apply(
        lambda x: "tak" if x is True or x == True
        else ("nie" if x is False or x == False else "nie dotyczy")
    )
    return kategorie.value_counts()

def policz_aktywne_czynniki(wyniki, klucz_czynnika):
    return sum(1 for wynik in wyniki if wynik["factors"][klucz_czynnika])