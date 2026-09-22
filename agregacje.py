"""Agregacje: zamiana surowych danych na liczby gotowe do wyświetlenia."""
import pandas as pd
from stałe import ETYKIETY_GRUP_WIEKOWYCH, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW
from przetwarzanie_danych import kategoria_wiekowa


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

def policz_klasyfikacje(wyniki):
    """Zlicza wystąpienia każdej klasyfikacji przyczyny przekroczenia, malejąco.

    Pomija wiersze oznaczone jako podejrzane (`waliduj_dane`) - dla nich
    klasyfikacja to tekst ostrzegawczy, nie prawdziwa przyczyna, więc
    nie ma sensu wliczać ich do statystyki.
    """
    klasyfikacje = [w["klasyfikacja"] for w in wyniki if not w.get("podejrzany")]
    return pd.Series(klasyfikacje).value_counts()
def wygeneruj_wnioski_pareto(counts):
    """Generuje krótki opis tekstowy najważniejszych obserwacji z rozkładu Pareto."""
    suma = counts.sum()
    if suma == 0:
        return "Brak przekroczeń dawki w bieżących danych."

    najczestsza = counts.index[0]
    udzial_najczestszej = counts.iloc[0] / suma * 100

    skumulowany = counts.cumsum() / suma * 100
    liczba_kategorii_do_80 = int((skumulowany < 80).sum()) + 1
    liczba_kategorii_do_80 = min(liczba_kategorii_do_80, len(counts))

    return (
        f"Najczęstsza przyczyna: '{najczestsza}' — {counts.iloc[0]} z {suma} przypadków "
        f"({udzial_najczestszej:.0f}%). "
        f"{liczba_kategorii_do_80} z {len(counts)} kategorii odpowiada łącznie za "
        f"{skumulowany.iloc[liczba_kategorii_do_80 - 1]:.0f}% wszystkich przekroczeń."
    )
def wygeneruj_wnioski_analizy(wyniki):
    """Generuje krótki opis najważniejszych obserwacji z tabeli analizy przyczyn."""
    wyniki_wazne = [w for w in wyniki if not w.get("podejrzany")]

    if not wyniki_wazne:
        return "Brak pacjentów z przekroczoną dawką w bieżących danych."

    n = len(wyniki_wazne)

    czynniki_counts = {
        klucz: sum(1 for w in wyniki_wazne if w["factors"][klucz]) for klucz in KLUCZE_CZYNNIKOW
    }
    najczestszy_klucz = max(czynniki_counts, key=czynniki_counts.get)
    udzial_czynnika = czynniki_counts[najczestszy_klucz] / n * 100

    okolice = pd.Series([w["okolica"] for w in wyniki_wazne]).value_counts()
    najczestsza_okolica = okolice.index[0]
    udzial_okolicy = okolice.iloc[0] / n * 100

    sredni_procent = sum(w["procent_przekroczenia"] for w in wyniki_wazne) / n

    etykieta_czynnika = ETYKIETY_CZYNNIKOW[najczestszy_klucz].replace("\n", " ")

    return (
        f"Najczęstszy czynnik: '{etykieta_czynnika}' — {czynniki_counts[najczestszy_klucz]} z {n} pacjentów "
        f"({udzial_czynnika:.0f}%). Najwięcej przekroczeń dotyczy okolicy '{najczestsza_okolica}' "
        f"({udzial_okolicy:.0f}% przypadków). Średnie przekroczenie dawki: {sredni_procent:.1f}%."
    )