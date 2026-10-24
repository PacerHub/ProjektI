#Agregacje: zamiana surowych danych na liczby gotowe do wyświetlenia.
import pandas as pd
from stale import (
    ETYKIETY_GRUP_WIEKOWYCH, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW,
    KLUCZ_BRAK_CZYNNIKA, WARTOSC_WSZYSTKIE,
)
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
    #Funkcja ta zlicza wystąpienia każdej klasyfikacji przyczyny przekroczenia, malejąco.

    # Pomija wiersze oznaczone jako podejrzane (`waliduj_dane`) - dla nich
    # klasyfikacja to tekst ostrzegawczy, nie prawdziwa przyczyna, więc
    # nie ma sensu wliczać ich do statystyki.
    klasyfikacje = [w["klasyfikacja"] for w in wyniki if not w.get("podejrzany")]
    return pd.Series(klasyfikacje).value_counts()

def wygeneruj_wnioski_pareto(counts, wyniki=None):
    #Generowanie krótkiego opisu tekstowego najważniejszych obserwacji z rozkładu Pareto.
    suma = counts.sum()
    if suma == 0:
        return "Brak przekroczeń dawki w bieżących danych."

    najczestsza = counts.index[0]
    udzial_najczestszej = counts.iloc[0] / suma * 100

    opis_przyczyny = f"'{najczestsza}'"
    if najczestsza == "połączenie kilku czynników" and wyniki:
        przypadki = [
            w for w in wyniki
            if not w.get("podejrzany") and w["klasyfikacja"] == "połączenie kilku czynników"
        ]
        liczby = {
            klucz: sum(1 for w in przypadki if w["factors"][klucz])
            for klucz in KLUCZE_CZYNNIKOW
        }
        wystepujace = sorted(
            ((klucz, n) for klucz, n in liczby.items() if n > 0),
            key=lambda para: para[1], reverse=True,
        )
        if wystepujace:
            lista = ", ".join(
                f"{etykieta_czynnika(klucz)} – {n} z {len(przypadki)}"
                for klucz, n in wystepujace
            )
            opis_przyczyny += f" (w tym: {lista})"

    skumulowany = counts.cumsum() / suma * 100
    liczba_kategorii_do_80 = int((skumulowany < 80).sum()) + 1
    liczba_kategorii_do_80 = min(liczba_kategorii_do_80, len(counts))

    return (
        f"Najczęstsza przyczyna: {opis_przyczyny} — {counts.iloc[0]} z {suma} przypadków "
        f"({udzial_najczestszej:.0f}%). "
        f"{liczba_kategorii_do_80} z {len(counts)} kategorii odpowiada łącznie za "
        f"{skumulowany.iloc[liczba_kategorii_do_80 - 1]:.0f}% wszystkich przekroczeń."
    )


def etykieta_czynnika(klucz):
    #Etykieta czynnika w jednej linii, z małej litery (skrót DLP zostaje bez zmian).
    etykieta = ETYKIETY_CZYNNIKOW[klucz].replace("\n", " ")
    return etykieta[0].lower() + etykieta[1:]

def wygeneruj_wnioski_analizy(wyniki):
    #Generowanie krótkiego opisu najważniejszych obserwacji z tabeli analizy przyczyn.
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

def wygeneruj_wnioski_brak_dpr(dane):
    """Opis badań bez DPR w przepisach albo None, gdy takich badań nie ma w danych."""
    # Udział liczony względem WSZYSTKICH wykonanych badań – także tych z błędnie
    # wprowadzonymi danymi, bo badanie zostało fizycznie wykonane, a błąd dotyczy zapisu.
    bez_dpr = dane[dane["brak_dpr"]]
    if bez_dpr.empty:
        return None

    udzial = len(bez_dpr) / len(dane) * 100
    poczatek = f"{len(bez_dpr)} z {len(dane)} badań ({udzial:.0f}%)"
    grupy = list(bez_dpr.groupby("rodzaj_badania_tk"))

    if len(grupy) == 1:
        # Jeden rodzaj badania – liczba podana raz, bez powtarzania jej w nawiasie
        badanie, grupa = grupy[0]
        onko = int((grupa["protokol_onkologiczny_jamy_brzusznej"] == True).sum())
        opis = (
            f"{poczatek} to '{badanie}' (w tym {onko} w protokole onkologicznym) – badanie "
            f"wykonywane w praktyce, dla którego przepisy nie określają diagnostycznego "
            f"poziomu referencyjnego (DPR)."
        )
    else:
        # Kilka rodzajów – lista z liczbą badań każdego rodzaju
        lista = "; ".join(
            f"'{badanie}': {len(grupa)} "
            f"(w tym {int((grupa['protokol_onkologiczny_jamy_brzusznej'] == True).sum())} onkologicznych)"
            for badanie, grupa in grupy
        )
        opis = (
            f"{poczatek} to badania wykonywane w praktyce, dla których przepisy nie określają "
            f"diagnostycznego poziomu referencyjnego (DPR): {lista}."
        )

    return opis + " Nie można dla nich ocenić przekroczenia dawki, dlatego nie są uwzględniane w analizie przekroczeń."

def przygotuj_tabele_eksportu(rekordy):
    """Tabela (DataFrame) do eksportu CSV – surowe liczby zamiast tekstów sformatowanych do wyświetlenia."""
    wiersze = []
    for r in rekordy:
        wiersz = {
            "Pacjent": r["patient_id"],
            "Wiek": r["wiek"],
            "Płeć": r["plec"],
            "Rodzaj badania": r["rodzaj_badania"],
            "Okolica anatomiczna": r["okolica"],
            "BMI": r["bmi"],
            "Kategoria BMI": r["kategoria_bmi"],
            "Liczba faz": r["kategoria_faz"],
            "DPR na fazę [mGy·cm]": r["dpr"],
            "DLP zmierzone na fazę [mGy·cm]": r["dlp"],
            "% przekroczenia": r["procent_przekroczenia"],
            "Klasyfikacja przyczyny": r["klasyfikacja"],
            "Aktywne czynniki": r["aktywne_czynniki"],
            "Do weryfikacji": "tak" if r["podejrzany"] else "nie",
        }
        # Kolumny czynników: "tak" albo puste – łatwo filtrować w Excelu
        for klucz in KLUCZE_CZYNNIKOW:
            wiersz[ETYKIETY_CZYNNIKOW[klucz].replace("\n", " ")] = "tak" if r["factors"][klucz] else ""
        wiersze.append(wiersz)

    tabela = pd.DataFrame(wiersze)
    tabela["Wiek"] = tabela["Wiek"].astype("Int64")   # 61 zamiast 61,0 (Int64 dopuszcza puste pola)
    tabela["% przekroczenia"] = tabela["% przekroczenia"].astype(float).round(1)
    return tabela