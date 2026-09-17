"""Agregacje: zamiana surowych danych na liczby gotowe do wyświetlenia."""


def policz_wg_kolumny(dane, kolumna, sortuj_wg_indeksu=False):
    """Zlicza wystąpienia wartości w danej kolumnie DataFrame."""
    counts = dane[kolumna].value_counts()
    return counts.sort_index() if sortuj_wg_indeksu else counts