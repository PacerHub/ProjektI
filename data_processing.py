"""Wczytywanie danych oraz transformacje analityczne na poziomie pojedynczego pacjenta."""

import pandas as pd
from constants import GRANICE_WIEKU, ETYKIETY_GRUP_WIEKOWYCH, EXAM_REGION, PROG_WYSOKIEGO_DLP_FAZY


def wczytaj_dane(sciezka):
    """Wczytuje plik CSV z danymi pacjentów do DataFrame."""
    return pd.read_csv(sciezka)

def waliduj_dane(dane):
    """Sprawdza dane pod kątem braków i wartości spoza sensownego zakresu.

    Nie rzuca wyjątku - zwraca (dane_oczyszczone, raport), żeby aplikacja
    mogła dalej działać, a Ty mogłeś zobaczyć, co zostało pominięte i dlaczego.
    """
    dane = dane.copy()
    problemy = []

    kolumny_wymagane = [
        "wiek", "bmi", "liczba_faz",
        "dlp_referencyjny_na_faze_mGy_cm", "dlp_zmierzony_na_faze_mGy_cm",
    ]

    # --- braki w kolumnach, które muszą mieć wartość ---
    for kolumna in kolumny_wymagane:
        brakujace = dane[dane[kolumna].isna()]
        if len(brakujace) > 0:
            problemy.append(f"{len(brakujace)} wierszy z brakującą wartością w '{kolumna}'")

    # --- wartości spoza sensownego zakresu ---
    def poza_zakresem(kolumna, zakres):
        dolny, gorny = zakres
        maska = (dane[kolumna] < dolny) | (dane[kolumna] > gorny)
        if maska.sum() > 0:
            problemy.append(
                f"{maska.sum()} wierszy z '{kolumna}' poza zakresem {zakres} "
                f"(np. patient_id: {dane.loc[maska, 'patient_id'].tolist()[:5]})"
            )
        return maska

    maska_odrzuconych = (
        dane[kolumny_wymagane].isna().any(axis=1)
        | poza_zakresem("wiek", ZAKRES_WIEKU)
        | poza_zakresem("bmi", ZAKRES_BMI)
        | poza_zakresem("liczba_faz", ZAKRES_LICZBY_FAZ)
        | (dane["dlp_referencyjny_na_faze_mGy_cm"] <= 0)
        | (dane["dlp_zmierzony_na_faze_mGy_cm"] < 0)
    )

    dane_oczyszczone = dane[~maska_odrzuconych].copy()

    if maska_odrzuconych.any():
        problemy.append(
            f"ŁĄCZNIE odrzucono {maska_odrzuconych.sum()} z {len(dane)} wierszy "
            f"(patient_id: {dane.loc[maska_odrzuconych, 'patient_id'].tolist()})"
        )

    return dane_oczyszczone, problemy


def oznacz_przekroczenia(dane):
    """Dodaje kolumny opisujące przekroczenie DLP: flagę bool i wartość liczbową."""
    dane = dane.copy()
    dane["przekroczenie_dlp"] = (
        dane["dlp_zmierzony_na_faze_mGy_cm"] > dane["dlp_referencyjny_na_faze_mGy_cm"]
    )
    dane["przekroczenie_o"] = (
        dane["dlp_zmierzony_na_faze_mGy_cm"] - dane["dlp_referencyjny_na_faze_mGy_cm"]
    )
    return dane


def filtruj_przekroczenia(dane):
    """Zwraca tylko wiersze pacjentów, u których doszło do przekroczenia DLP."""
    return dane[dane["przekroczenie_dlp"] == True]


def czy_pediatryczny(wiek):
    return bool(wiek < 16)


def czy_onkologiczny(wartosc_protokolu):
    return bool(wartosc_protokolu is True or wartosc_protokolu == True)


def czy_wielofazowy(liczba_faz):
    return int(liczba_faz) >= 2


def oblicz_stosunek_dlp(dlp_zmierzony, dlp_referencyjny):
    return float(dlp_zmierzony) / float(dlp_referencyjny)


def oblicz_procent_przekroczenia(stosunek_dlp):
    return round((stosunek_dlp - 1) * 100, 3)


def czy_wysokie_dlp_fazy(stosunek_dlp, prog=PROG_WYSOKIEGO_DLP_FAZY):
    return stosunek_dlp >= prog


def czy_nadwaga_lub_otylosc(jest_pediatryczny, bmi):
    return bool((not jest_pediatryczny) and bmi >= 25)


def kategoria_liczby_faz(liczba_faz):
    if liczba_faz == 1:
        return "1 faza"
    if liczba_faz == 2:
        return "2 fazy"
    return f"więcej faz ({liczba_faz})"


def kategoria_bmi(wiek, bmi):
    if wiek < 16:
        return "nie dotyczy (pacjent pediatryczny)"
    if bmi < 18.5:
        return "niedowaga"
    if bmi < 25:
        return "waga prawidłowa"
    if bmi < 30:
        return "nadwaga"
    return "otyłość"


def ustal_okolice_anatomiczna(rodzaj_badania):
    return EXAM_REGION.get(rodzaj_badania, "nieznana")


def wyznacz_czynniki(wiek, bmi, liczba_faz, protokol_onko_raw, stosunek_dlp):
    jest_pediatryczny = czy_pediatryczny(wiek)
    return {
        "pediatryczny": jest_pediatryczny,
        "onkologiczny": czy_onkologiczny(protokol_onko_raw),
        "wielofazowy": czy_wielofazowy(liczba_faz),
        "wysoki_dlp_fazy": czy_wysokie_dlp_fazy(stosunek_dlp),
        "nadwaga_otylosc": czy_nadwaga_lub_otylosc(jest_pediatryczny, bmi),
    }


def klasyfikuj_przyczyne(factors):
    label_map = {
        "pediatryczny": "pacjent <16 lat",
        "onkologiczny": "protokół onkologiczny",
        "wielofazowy": "wielofazowe badanie",
        "wysoki_dlp_fazy": "wysokie DLP pojedynczej fazy",
        "nadwaga_otylosc": "nadwaga/otyłość pacjenta",
    }
    aktywne = [nazwa for nazwa, jest_aktywny in factors.items() if jest_aktywny]
    if len(aktywne) == 0:
        return "przekroczenie wymagające indywidualnej analizy", []
    if len(aktywne) == 1:
        return label_map[aktywne[0]], [label_map[aktywne[0]]]
    return "połączenie kilku czynników", [label_map[a] for a in aktywne]


def analizuj_pacjenta(wiersz):
    wiek = wiersz["wiek"]
    bmi = float(wiersz["bmi"])
    liczba_faz = int(wiersz["liczba_faz"])
    protokol_onko_raw = wiersz["protokol_onkologiczny_jamy_brzusznej"]

    stosunek_dlp = oblicz_stosunek_dlp(
        wiersz["dlp_zmierzony_na_faze_mGy_cm"],
        wiersz["dlp_referencyjny_na_faze_mGy_cm"],
    )

    factors = wyznacz_czynniki(wiek, bmi, liczba_faz, protokol_onko_raw, stosunek_dlp)
    klasyfikacja, aktywne_czynniki = klasyfikuj_przyczyne(factors)

    return {
        "okolica": ustal_okolice_anatomiczna(wiersz["rodzaj_badania_tk"]),
        "kategoria_faz": kategoria_liczby_faz(liczba_faz),
        "bmi": round(bmi, 1),
        "kategoria_bmi": kategoria_bmi(wiek, bmi),
        "procent_przekroczenia": oblicz_procent_przekroczenia(stosunek_dlp),
        "klasyfikacja": klasyfikacja,
        "aktywne_czynniki": ", ".join(aktywne_czynniki) if aktywne_czynniki else "brak",
        "factors": factors,
    }
def kategoria_wiekowa(wiek):
    for gorna_granica, etykieta in zip(GRANICE_WIEKU, ETYKIETY_GRUP_WIEKOWYCH):
        if wiek <= gorna_granica:
            return etykieta
    return ETYKIETY_GRUP_WIEKOWYCH[-1]

def zbuduj_liste_wynikow(pacjenci):
    """Uruchamia analizę dla każdego wiersza DataFrame i zwraca listę wyników."""
    return [analizuj_pacjenta(wiersz) for _, wiersz in pacjenci.iterrows()]