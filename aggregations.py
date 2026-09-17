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