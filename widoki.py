#Widoki aplikacji: jedna funkcja `pokaz_*` = jeden ekran wybierany przyciskiem.

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
from agregacje import (
    policz_wg_kolumny, policz_wg_grupy_wiekowej, policz_klasyfikacje,
    wygeneruj_wnioski_pareto, wygeneruj_wnioski_analizy, filtruj_przyczyny,
)
from stale import (
    KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW, KLASYFIKACJA_OPISY, CZCIONKA,
    ETYKIETY_GRUP_WIEKOWYCH, KLUCZ_BRAK_CZYNNIKA, WARTOSC_WSZYSTKIE, KOLUMNY_TABELI_PRZYCZYN,
)
from komponenty import (
    zbuduj_tabele, zbuduj_panel_podsumowania, Tooltip, TooltipTabeli, zbuduj_filtr_plci,
    zbuduj_filtr_kategorii_bmi, zbuduj_panel_wnioskow, zbuduj_panel_filtrow,
)
from przetwarzanie_danych import (
    filtruj_przekroczenia, zbuduj_liste_wynikow, filtruj_bezpieczne,
    filtruj_pacjentow_dashboardu, zbuduj_rekordy_przyczyn,
)
from wykresy import (
    zbuduj_dashboard_przekroczenia, zbuduj_wykres_liczebnosci,
    zbuduj_wykres_kolowy_liczebnosci, zbuduj_wykres_pareto,
)

import tkinter as tk


def osadz_wykres(parent, fig):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)  # zwalnia figurę z pamięci pyplot; wykres zostaje w oknie
    return canvas

def pokaz_liczebnosc_wg_kolumny(parent, dane, kolumna, tytul, sortuj_wg_indeksu=False, typ_wykresu="slupkowy", kolory=None):
    counts = policz_wg_kolumny(filtruj_bezpieczne(dane), kolumna, sortuj_wg_indeksu)

    if typ_wykresu == "kolowy":
        fig = zbuduj_wykres_kolowy_liczebnosci(counts, tytul, kolory)
    else:
        fig = zbuduj_wykres_liczebnosci(counts, tytul, kolory)

    return osadz_wykres(parent, fig)

def pokaz_liczbe_pacjentow_wg_wieku(parent, dane):
    counts = policz_wg_grupy_wiekowej(filtruj_bezpieczne(dane))
    fig = zbuduj_wykres_liczebnosci(counts, "Liczba pacjentów wg wieku")
    return osadz_wykres(parent, fig)

def pokaz_pareto_przyczyn(parent, dane):
    #Widok 'Pareto przyczyn przekroczeń' - które przyczyny odpowiadają za większość przypadków.
    pacjenci = filtruj_przekroczenia(filtruj_bezpieczne(dane))
    wyniki = zbuduj_liste_wynikow(pacjenci)
    counts = policz_klasyfikacje(wyniki)
    fig = zbuduj_wykres_pareto(counts)
    # Panel pakowany PRZED wykresem z side="bottom", żeby wykres go nie wypchnął poza okno
    zbuduj_panel_wnioskow(parent, wygeneruj_wnioski_pareto(counts, wyniki),
                          side="bottom", pady=(5, 20))
    return osadz_wykres(parent, fig)

def pokaz_dashboard_przekroczenia(parent, dane):
    wybrana_plec = tk.StringVar(value="wszyscy")
    wybrana_kategoria_bmi = tk.StringVar(value="wszyscy")
    obszar_wykresu = tk.Frame(parent)

    def odswiez(*_):
        for widget in obszar_wykresu.winfo_children():
            widget.destroy()

        pacjenci = filtruj_pacjentow_dashboardu(
            dane, plec=wybrana_plec.get(), bmi=wybrana_kategoria_bmi.get()
        )

        if len(pacjenci) == 0:
            tk.Label(
                obszar_wykresu, text="Brak pacjentów z przekroczoną dawką dla wybranych filtrów.",
                font=(CZCIONKA, 12),
            ).pack(pady=40)
            return

        fig = zbuduj_dashboard_przekroczenia(pacjenci)
        osadz_wykres(obszar_wykresu, fig)

    wybrana_plec.trace_add("write", odswiez)
    wybrana_kategoria_bmi.trace_add("write", odswiez)

    zbuduj_filtr_plci(parent, wybrana_plec)
    zbuduj_filtr_kategorii_bmi(parent, wybrana_kategoria_bmi)
    obszar_wykresu.pack(fill="both", expand=True)

    odswiez()
    return obszar_wykresu

def wiersz_tabeli_przyczyn(patient_id, wynik):
#Buduje krotkę wartości do wstawienia w jeden wiersz tabeli przyczyn.
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


def dodaj_tooltip_klasyfikacji(tabela):
    #Podpina tooltip z pełną nazwą i opisem klasyfikacji przyczyny do kolumny 'klasyfikacja'.
    def tekst_dymka(wiersz_id):
        klasyfikacja = tabela.set(wiersz_id, "klasyfikacja")
        opis = KLASYFIKACJA_OPISY.get(klasyfikacja, "Brak dodatkowego opisu dla tej klasyfikacji.")
        return f"{klasyfikacja}\n\n{opis}"

    return Tooltip(tabela, kolumna_docelowa="#6", pobierz_tekst=tekst_dymka)

def wiersz_tabeli_przyczyn(rekord):
    #Krotka wartości jednego wiersza – w kolejności KOLUMNY_TABELI_PRZYCZYN.
    pacjent = f"⚠ {rekord['patient_id']}" if rekord["podejrzany"] else rekord["patient_id"]
    wiek = str(int(rekord["wiek"])) if pd.notna(rekord["wiek"]) else "—"
    plec = rekord["plec"] if pd.notna(rekord["plec"]) else "—"
    bmi = (
        f"{rekord['bmi']} ({rekord['kategoria_bmi']})"
        if rekord["bmi"] is not None else rekord["kategoria_bmi"]
    )
    procent = (
        f"{rekord['procent_przekroczenia']:+.1f}%"
        if rekord["procent_przekroczenia"] is not None else "—"
    )
    return (
        pacjent, wiek, plec, rekord["okolica"], bmi, rekord["kategoria_faz"], procent,
        rekord["klasyfikacja"], rekord["aktywne_czynniki"],
        *("✓" if rekord["factors"][klucz] else "" for klucz in KLUCZE_CZYNNIKOW),
    )


def dodaj_tooltip_klasyfikacji(tabela, kolumna_id):
    #Tooltip z pełną nazwą i opisem klasyfikacji przyczyny w podanej kolumnie (np. '#8').
    def tekst_dymka(wiersz_id):
        klasyfikacja = tabela.set(wiersz_id, "klasyfikacja")
        opis = KLASYFIKACJA_OPISY.get(klasyfikacja, "Brak dodatkowego opisu dla tej klasyfikacji.")
        return f"{klasyfikacja}\n\n{opis}"

    return Tooltip(tabela, kolumna_docelowa=kolumna_id, pobierz_tekst=tekst_dymka)


def pokaz_analize_przyczyn(parent, dane):
    #Widok 'Analiza przyczyn przekroczeń': karty, wnioski, filtry i tabela pacjentów.
    # Przekroczenia + wiersze podejrzane (te mogą nie mieć DLP, więc nie są "przekroczeniem")
    pacjenci = dane[dane["przekroczenie_dlp"] | dane["podejrzany_wiersz"]]
    rekordy = zbuduj_rekordy_przyczyn(pacjenci)
    liczba_waznych = sum(1 for r in rekordy if not r["podejrzany"])
    okolice = sorted({r["okolica"] for r in rekordy if not r["podejrzany"]})

    # --- Karty czynników i wnioski (w commicie 2 zaczną reagować na filtry) ---
    zbuduj_panel_podsumowania(parent, rekordy, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW)
    zbuduj_panel_wnioskow(parent, wygeneruj_wnioski_analizy(rekordy))

    # --- Filtry ---
    zmienne = {
        "czynniki": {
            klucz: tk.BooleanVar(value=True)
            for klucz in [*KLUCZE_CZYNNIKOW, KLUCZ_BRAK_CZYNNIKA]
        },
        "okolica": tk.StringVar(value=WARTOSC_WSZYSTKIE),
        "grupa_wiekowa": tk.StringVar(value=WARTOSC_WSZYSTKIE),
        "min_procent": tk.StringVar(value="0"),
        "podejrzane": tk.BooleanVar(value=True),
    }

    def wyczysc():
        for zmienna in zmienne["czynniki"].values():
            zmienna.set(True)
        zmienne["okolica"].set(WARTOSC_WSZYSTKIE)
        zmienne["grupa_wiekowa"].set(WARTOSC_WSZYSTKIE)
        zmienne["min_procent"].set("0")
        zmienne["podejrzane"].set(True)

    zbuduj_panel_filtrow(parent, zmienne, okolice, ETYKIETY_GRUP_WIEKOWYCH, wyczysc)

    licznik = tk.Label(parent, anchor="w", font=(CZCIONKA, 11, "bold"))
    licznik.pack(fill="x", padx=20, pady=(8, 4))

    # --- Tabela ---
    kolumny = tuple(k for k, _, _, _ in KOLUMNY_TABELI_PRZYCZYN)
    naglowki = {k: n for k, n, _, _ in KOLUMNY_TABELI_PRZYCZYN}
    szerokosci = {k: s for k, _, s, _ in KOLUMNY_TABELI_PRZYCZYN}
    kotwice = {k: a for k, _, _, a in KOLUMNY_TABELI_PRZYCZYN}

    tabela = zbuduj_tabele(parent, kolumny, naglowki, szerokosci, kotwice)
    tabela.tag_configure("podejrzany", background="#fff3cd")

    # Numer kolumny liczony z listy – nie trzeba go poprawiać po zmianie kolejności kolumn
    kolumna_klasyfikacji = f"#{kolumny.index('klasyfikacja') + 1}"
    dodaj_tooltip_klasyfikacji(tabela, kolumna_klasyfikacji)
    tabela.tooltip = TooltipTabeli(tabela, pomin_kolumny={kolumna_klasyfikacji})

    def odswiez(*_):
        try:
            min_procent = float(zmienne["min_procent"].get().replace(",", "."))
        except ValueError:
            min_procent = 0  # np. puste pole w trakcie wpisywania

        wybrane = filtruj_przyczyny(
            rekordy,
            czynniki={k for k, z in zmienne["czynniki"].items() if z.get()},
            okolica=zmienne["okolica"].get(),
            grupa_wiekowa=zmienne["grupa_wiekowa"].get(),
            min_procent=min_procent,
            pokaz_podejrzane=zmienne["podejrzane"].get(),
        )

        tabela.delete(*tabela.get_children())
        for rekord in wybrane:
            tagi = ("podejrzany",) if rekord["podejrzany"] else ()
            tabela.insert("", "end", values=wiersz_tabeli_przyczyn(rekord), tags=tagi)

        pokazane = sum(1 for r in wybrane if not r["podejrzany"])
        podejrzane = len(wybrane) - pokazane
        tekst = f"Wyniki: {pokazane} z {liczba_waznych} pacjentów z przekroczeniem"
        if podejrzane:
            tekst += f"  (+ {podejrzane} ⚠ do weryfikacji)"
        licznik.config(text=tekst)

    # Każda zmiana dowolnego filtra odświeża tabelę
    for zmienna in [*zmienne["czynniki"].values(), zmienne["okolica"], zmienne["grupa_wiekowa"],
                    zmienne["min_procent"], zmienne["podejrzane"]]:
        zmienna.trace_add("write", odswiez)

    odswiez()
    return tabela