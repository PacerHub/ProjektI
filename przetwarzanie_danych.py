# Wczytywanie danych oraz transformacje analityczne na poziomie pojedynczego pacjenta.

import pandas as pd

from stale import (
    EXAM_REGION, PROG_WYSOKIEGO_DLP_FAZY, GRANICE_WIEKU, ETYKIETY_GRUP_WIEKOWYCH,
    ZAKRES_WIEKU, ZAKRES_BMI, ZAKRES_LICZBY_FAZ, KLUCZE_CZYNNIKOW, BADANIA_BEZ_DPR, WIEK_PEDIATRYCZNY, PROGI_BMI,
    PROG_NADWAGI, ETYKIETA_BMI_PEDIATRYCZNY, KATEGORIE_BMI, ETYKIETY_KLASYFIKACJI, KLASYFIKACJA_BRAK_CZYNNIKA,
    KLASYFIKACJA_KILKA_CZYNNIKOW, WARTOSC_WSZYSTKIE, KLUCZ_BRAK_CZYNNIKA
)


def wczytaj_dane(sciezka):
    # Wczytuje plik CSV z danymi pacjentów do DataFrame.
    return pd.read_csv(sciezka)


def oznacz_podejrzane_dane(dane):
    # Oznaczanie wierszy z brakami lub wartościami spoza sensownego zakresu, BEZ usuwania ich.
    dane = dane.copy()
    dane["podejrzany_wiersz"] = False
    dane["powod_podejrzenia"] = ""
    # Badania, dla których przepisy nie określają DPR – brak DPR to NIE jest błąd danych
    dane["brak_dpr"] = dane["rodzaj_badania_tk"].isin(BADANIA_BEZ_DPR)

    kolumny_wymagane = ["wiek", "bmi", "liczba_faz",
                        "dlp_referencyjny_na_faze_mGy_cm", "dlp_zmierzony_na_faze_mGy_cm"]

    for idx, wiersz in dane.iterrows():
        powody = []

        for kolumna in kolumny_wymagane:
            if kolumna == "dlp_referencyjny_na_faze_mGy_cm" and wiersz["brak_dpr"]:
                continue  # brak DPR w przepisach, a nie brak danych
            if bool(pd.isna(wiersz[kolumna])):
                powody.append(f"brak wartości w '{kolumna}'")

        if bool(pd.notna(wiersz["wiek"])) and not (ZAKRES_WIEKU[0] <= wiersz["wiek"] <= ZAKRES_WIEKU[1]):
            powody.append(f"wiek poza zakresem {ZAKRES_WIEKU}")

        if bool(pd.notna(wiersz["bmi"])) and not (ZAKRES_BMI[0] <= wiersz["bmi"] <= ZAKRES_BMI[1]):
            powody.append(f"BMI poza zakresem {ZAKRES_BMI}")

        if bool(pd.notna(wiersz["liczba_faz"])) and not (
                ZAKRES_LICZBY_FAZ[0] <= wiersz["liczba_faz"] <= ZAKRES_LICZBY_FAZ[1]):
            powody.append(f"liczba faz poza zakresem {ZAKRES_LICZBY_FAZ}")

        if bool(pd.notna(wiersz["dlp_referencyjny_na_faze_mGy_cm"])) and wiersz["dlp_referencyjny_na_faze_mGy_cm"] <= 0:
            powody.append("DPR <= 0")

        if bool(pd.notna(wiersz["dlp_zmierzony_na_faze_mGy_cm"])) and wiersz["dlp_zmierzony_na_faze_mGy_cm"] < 0:
            powody.append("DLP ujemne")

        if powody:
            dane.at[idx, "podejrzany_wiersz"] = True
            dane.at[idx, "powod_podejrzenia"] = "; ".join(powody)

    return dane


def oznacz_przekroczenia(dane):
    # Dodaje kolumny opisujące przekroczenie DLP: flagę bool i wartość liczbową.
    dane = dane.copy()
    dane["przekroczenie_dlp"] = (
            dane["dlp_zmierzony_na_faze_mGy_cm"] > dane["dlp_referencyjny_na_faze_mGy_cm"]
    )
    dane["przekroczenie_o"] = (
            dane["dlp_zmierzony_na_faze_mGy_cm"] - dane["dlp_referencyjny_na_faze_mGy_cm"]
    )
    return dane


def czy_pediatryczny(wiek):
    return bool(wiek < WIEK_PEDIATRYCZNY)


def czy_onkologiczny(wartosc_protokolu):
    return bool(wartosc_protokolu is True or wartosc_protokolu == True)


def czy_wielofazowy(liczba_faz):
    return int(liczba_faz) >= 2


def czy_wysokie_dlp_fazy(stosunek_dlp, prog=PROG_WYSOKIEGO_DLP_FAZY):
    return stosunek_dlp >= prog


def czy_nadwaga_lub_otylosc(jest_pediatryczny, bmi):
    return bool((not jest_pediatryczny) and bmi >= PROG_NADWAGI)


def oblicz_stosunek_dlp(dlp_zmierzony, dlp_referencyjny):
    return float(dlp_zmierzony) / float(dlp_referencyjny)


def oblicz_procent_przekroczenia(stosunek_dlp):
    return round((stosunek_dlp - 1) * 100, 3)


def kategoria_liczby_faz(liczba_faz):
    if liczba_faz == 1:
        return "1 faza"
    if liczba_faz == 2:
        return "2 fazy"
    return f"więcej faz ({liczba_faz})"


def kategoria_bmi(wiek, bmi):
    if wiek < WIEK_PEDIATRYCZNY:
        return ETYKIETA_BMI_PEDIATRYCZNY
    for prog, kategoria in zip(PROGI_BMI, KATEGORIE_BMI):
        if bmi < prog:
            return kategoria
    return KATEGORIE_BMI[-1]


def kategoria_wiekowa(wiek):
    for gorna_granica, etykieta in zip(GRANICE_WIEKU, ETYKIETY_GRUP_WIEKOWYCH):
        if wiek <= gorna_granica:
            return etykieta
    return ETYKIETY_GRUP_WIEKOWYCH[-1]


def kategoria_onkologiczna(wartosc_protokolu):
    """'tak' / 'nie' / 'nie dotyczy' (puste pole = badanie nie dotyczy jamy brzusznej)."""
    if bool(pd.isna(wartosc_protokolu)):
        return "nie dotyczy"
    return "tak" if czy_onkologiczny(wartosc_protokolu) else "nie"


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
    aktywne = [ETYKIETY_KLASYFIKACJI[nazwa] for nazwa, jest_aktywny in factors.items() if jest_aktywny]
    if len(aktywne) == 0:
        return KLASYFIKACJA_BRAK_CZYNNIKA, []
    if len(aktywne) == 1:
        return aktywne[0], aktywne
    return KLASYFIKACJA_KILKA_CZYNNIKOW, aktywne


def analizuj_podejrzany_wiersz(wiersz):
    """Wynik dla wiersza do weryfikacji: pokazuje wszystkie dane, które da się wiarygodnie
    wyliczyć, a '—' tylko tam, gdzie wartości brakuje lub jest błędna."""
    wiek = wiersz["wiek"]
    bmi = wiersz["bmi"]
    liczba_faz = wiersz["liczba_faz"]
    dpr = wiersz["dlp_referencyjny_na_faze_mGy_cm"]
    dlp = wiersz["dlp_zmierzony_na_faze_mGy_cm"]

    wiek_ok = bool(pd.notna(wiek)) and ZAKRES_WIEKU[0] <= wiek <= ZAKRES_WIEKU[1]
    bmi_ok = bool(pd.notna(bmi)) and ZAKRES_BMI[0] <= bmi <= ZAKRES_BMI[1]

    # Kategoria BMI zależy od wieku, więc liczymy ją tylko przy poprawnym wieku i BMI
    if bool(pd.isna(bmi)):
        kategoria = "—"
    elif not bmi_ok:
        kategoria = "poza zakresem"
    elif wiek_ok:
        kategoria = kategoria_bmi(wiek, bmi)
    else:
        kategoria = "—"

    # % przekroczenia tylko przy sensownych wartościach (DPR = 0 -> dzielenie przez zero)
    procent = None
    if bool(pd.notna(dpr)) and bool(pd.notna(dlp)) and dpr > 0 and dlp >= 0:
        procent = oblicz_procent_przekroczenia(oblicz_stosunek_dlp(dlp, dpr))

    return {
        "okolica": ustal_okolice_anatomiczna(wiersz["rodzaj_badania_tk"]),
        "kategoria_faz": kategoria_liczby_faz(int(liczba_faz)) if bool(pd.notna(liczba_faz)) else "—",
        "bmi": round(float(bmi), 1) if bool(pd.notna(bmi)) else None,
        "kategoria_bmi": kategoria,
        "procent_przekroczenia": procent,
        "klasyfikacja": f"⚠ dane do weryfikacji ({wiersz.get('powod_podejrzenia', 'nieznany powód')})",
        "aktywne_czynniki": "brak (dane niepełne/błędne)",
        "factors": {klucz: False for klucz in KLUCZE_CZYNNIKOW},
        "podejrzany": True,
    }


def analizuj_pacjenta(wiersz):
    # Łączy powyższe pojedyncze transformacje w pełny wynik analizy dla jednego wiersza danych
    if wiersz.get("podejrzany_wiersz", False):
        return analizuj_podejrzany_wiersz(wiersz)

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
        "podejrzany": False,
    }


def zbuduj_rekordy_przyczyn(pacjenci):
    """Wynik analizy każdego pacjenta + dane potrzebne w tabeli filtra (wiek, płeć, badanie, grupa wiekowa)."""
    rekordy = []
    for _, wiersz in pacjenci.iterrows():
        wynik = analizuj_pacjenta(wiersz)
        wiek = wiersz["wiek"]
        rekordy.append({
            **wynik,
            "patient_id": wiersz["patient_id"],
            "wiek": wiek,
            "plec": wiersz["plec"],
            "rodzaj_badania": wiersz["rodzaj_badania_tk"],
            "grupa_wiekowa": kategoria_wiekowa(wiek) if bool(pd.notna(wiek)) else "—",
            "dpr": wiersz["dlp_referencyjny_na_faze_mGy_cm"],
            "dlp": wiersz["dlp_zmierzony_na_faze_mGy_cm"],
        })
    return rekordy


def filtruj_bezpieczne(dane):
    # Zwraca tylko wiersze BEZ oznaczenia 'podejrzany' - do wykresów zbiorczych/agregacji
    if "podejrzany_wiersz" not in dane.columns:
        return dane
    return dane[~dane["podejrzany_wiersz"]]


def filtruj_przekroczenia(dane):
    # Zwraca tylko wiersze pacjentów, u których doszło do przekroczenia DLP.
    return dane[dane["przekroczenie_dlp"]]


def filtruj_wg_plci(pacjenci, wybor):
    """Zwraca podzbiór pacjentów wg wyboru filtra: 'wszystkie' | 'kobiety' | 'mezczyzni'."""
    if wybor == "kobiety":
        return pacjenci[pacjenci["plec"] == "K"]
    if wybor == "mezczyzni":
        return pacjenci[pacjenci["plec"] == "M"]
    return pacjenci


def filtruj_wg_kategorii_bmi(pacjenci, wybor):
    """Zwraca podzbiór pacjentów wg wybranej kategorii BMI (lub wszystkich przy 'wszyscy')."""
    if wybor == WARTOSC_WSZYSTKIE or len(pacjenci) == 0:
        return pacjenci
    kategorie = pacjenci.apply(lambda w: kategoria_bmi(w["wiek"], w["bmi"]), axis=1)
    return pacjenci[kategorie == wybor]


def filtruj_pacjentow_dashboardu(dane, plec="wszyscy", bmi=WARTOSC_WSZYSTKIE):
    """Zwraca pacjentów z przekroczoną dawką po zastosowaniu wszystkich filtrów dashboardu."""
    pacjenci = filtruj_przekroczenia(filtruj_bezpieczne(dane))
    pacjenci = filtruj_wg_plci(pacjenci, plec)
    pacjenci = filtruj_wg_kategorii_bmi(pacjenci, bmi)
    return pacjenci


def filtruj_przyczyny(rekordy, czynniki, okolica=WARTOSC_WSZYSTKIE,
                      grupa_wiekowa=WARTOSC_WSZYSTKIE, min_procent=0, pokaz_podejrzane=True):
    """Zwraca rekordy pasujące do filtrów, posortowane malejąco po % przekroczenia.

    czynniki – zbiór zaznaczonych kluczy; pacjent przechodzi, jeśli ma KTÓRYKOLWIEK z nich
    (pacjent bez żadnego czynnika przechodzi, gdy zaznaczono KLUCZ_BRAK_CZYNNIKA).
    Wiersze podejrzane nie mają wiarygodnych danych, więc pozostałe filtry ich nie dotyczą –
    decyduje tylko pokaz_podejrzane. Trafiają na koniec listy.
    """
    wybrane = []
    for rekord in rekordy:
        if rekord["podejrzany"]:
            if pokaz_podejrzane:
                wybrane.append(rekord)
            continue

        aktywne = [klucz for klucz in KLUCZE_CZYNNIKOW if rekord["factors"][klucz]]
        if aktywne:
            pasuje_przyczyna = any(klucz in czynniki for klucz in aktywne)
        else:
            pasuje_przyczyna = KLUCZ_BRAK_CZYNNIKA in czynniki
        if not pasuje_przyczyna:
            continue

        if okolica != WARTOSC_WSZYSTKIE and rekord["okolica"] != okolica:
            continue
        if grupa_wiekowa != WARTOSC_WSZYSTKIE and rekord["grupa_wiekowa"] != grupa_wiekowa:
            continue
        if rekord["procent_przekroczenia"] < min_procent:
            continue

        wybrane.append(rekord)

    # False < True, więc najpierw zwykłe wiersze (malejąco po %), na końcu podejrzane
    wybrane.sort(key=lambda r: (r["podejrzany"], -(r["procent_przekroczenia"] or 0)))
    return wybrane


def filtruj_do_analizy_przyczyn(dane):
    """Pacjenci z przekroczeniem + wiersze do weryfikacji (te mogą nie mieć DLP, więc nie są 'przekroczeniem')."""
    return dane[dane["przekroczenie_dlp"] | dane["podejrzany_wiersz"]]
