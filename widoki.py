# Widoki aplikacji: jedna funkcja `pokaz_*` = jeden ekran wybierany przyciskiem.
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.layout_engine import TightLayoutEngine
from typing import Any

from agregacje import (
    policz_wg_kolumny, policz_wg_grupy_wiekowej, policz_klasyfikacje,
    wygeneruj_wnioski_pareto, wygeneruj_wnioski_analizy, wygeneruj_wnioski_brak_dpr, przygotuj_tabele_eksportu
)
from komponenty import (
    zbuduj_tabele, zbuduj_panel_podsumowania, Tooltip, TooltipTabeli, zbuduj_filtr_plci,
    zbuduj_filtr_kategorii_bmi, zbuduj_panel_wnioskow, zbuduj_panel_filtrow,
)
from przetwarzanie_danych import (
    filtruj_przekroczenia, filtruj_bezpieczne,
    filtruj_pacjentow_dashboardu, zbuduj_rekordy_przyczyn, filtruj_przyczyny, filtruj_do_analizy_przyczyn
)
from stale import (
    KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW, KLASYFIKACJA_OPISY, CZCIONKA,
    ETYKIETY_GRUP_WIEKOWYCH, KLUCZ_BRAK_CZYNNIKA, WARTOSC_WSZYSTKIE, KOLUMNY_TABELI_PRZYCZYN,
    OPIS_DANYCH_DO_WERYFIKACJI, OPISY_NAGLOWKOW_PRZYCZYN, KOLOR_TLA_PRZYP_DO_WERYFIKACJI)
from wykresy import (
    zbuduj_dashboard_przekroczenia, zbuduj_wykres_liczebnosci,
    zbuduj_wykres_kolowy_liczebnosci, zbuduj_wykres_pareto, kolory_rodzajow_badan
)


def osadz_wykres(parent, fig):
    # Układ "tight" przeliczany przy każdym rysowaniu – także po zmianie rozmiaru wykresu
    # w oknie. Jednorazowe plt.tight_layout() nie wystarcza, bo liczy miejsce na etykiety
    # tylko dla pierwotnego rozmiaru figury.
    if not isinstance(fig.get_layout_engine(), TightLayoutEngine):
        fig.set_layout_engine("tight")

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)  # zwalnia figurę z pamięci pyplot; wykres zostaje w oknie
    return canvas


def pokaz_liczebnosc_wg_kolumny(parent, dane, kolumna, tytul, sortuj_wg_indeksu=False,
                                typ_wykresu="slupkowy", kolory=None):
    counts = policz_wg_kolumny(filtruj_bezpieczne(dane), kolumna, sortuj_wg_indeksu)
    legenda = None

    # Rodzaj badania: wyróżnienie badań, dla których przepisy nie określają DPR
    if kolumna == "rodzaj_badania_tk":
        kolory, legenda = kolory_rodzajow_badan(counts.index)
        wnioski = wygeneruj_wnioski_brak_dpr(dane)
        if wnioski:
            # Panel pakowany PRZED wykresem z side="bottom", żeby wykres go nie wypchnął
            zbuduj_panel_wnioskow(parent, wnioski, side="bottom", pady=(5, 20))

    if typ_wykresu == "kolowy":
        fig = zbuduj_wykres_kolowy_liczebnosci(counts, tytul, kolory)
    else:
        fig = zbuduj_wykres_liczebnosci(counts, tytul, kolory, legenda)

    return osadz_wykres(parent, fig)


def pokaz_liczbe_pacjentow_wg_wieku(parent, dane):
    counts = policz_wg_grupy_wiekowej(filtruj_bezpieczne(dane))
    fig = zbuduj_wykres_liczebnosci(counts, "Liczba pacjentów wg wieku")
    return osadz_wykres(parent, fig)


def pokaz_pareto_przyczyn(parent, dane):
    # Widok 'Pareto przyczyn przekroczeń' - które przyczyny odpowiadają za większość przypadków.
    pacjenci = filtruj_przekroczenia(filtruj_bezpieczne(dane))
    wyniki = zbuduj_rekordy_przyczyn(pacjenci)
    counts = policz_klasyfikacje(wyniki)
    fig = zbuduj_wykres_pareto(counts)
    # Panel pakowany PRZED wykresem z side="bottom", żeby wykres go nie wypchnął poza okno
    zbuduj_panel_wnioskow(parent, wygeneruj_wnioski_pareto(counts, wyniki),
                          side="bottom", pady=(5, 20))
    return osadz_wykres(parent, fig)


def pokaz_dashboard_przekroczenia(parent, dane):
    wybrana_plec = tk.StringVar(value=WARTOSC_WSZYSTKIE)
    wybrana_kategoria_bmi = tk.StringVar(value=WARTOSC_WSZYSTKIE)
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


def wiersz_tabeli_przyczyn(rekord):
    # Krotka wartości jednego wiersza – w kolejności KOLUMNY_TABELI_PRZYCZYN.
    pacjent = f"⚠ {rekord['patient_id']}" if rekord["podejrzany"] else rekord["patient_id"]
    wiek = str(int(rekord["wiek"])) if pd.notna(rekord["wiek"]) else "—"
    plec = rekord["plec"] if pd.notna(rekord["plec"]) else "—"
    bmi = (
        f"{rekord['bmi']} ({rekord['kategoria_bmi']})"
        if rekord["bmi"] is not None else rekord["kategoria_bmi"]
    )
    dpr = f"{rekord['dpr']:.0f}" if pd.notna(rekord["dpr"]) else "—"
    dlp = f"{rekord['dlp']:.1f}" if pd.notna(rekord["dlp"]) else "—"
    procent = (
        f"{rekord['procent_przekroczenia']:+.1f}%"
        if rekord["procent_przekroczenia"] is not None else "—"
    )
    return (
        pacjent, wiek, plec, rekord["okolica"], bmi, rekord["kategoria_faz"], dpr, dlp, procent,
        rekord["klasyfikacja"], rekord["aktywne_czynniki"],
        *("✓" if rekord["factors"][klucz] else "" for klucz in KLUCZE_CZYNNIKOW),
    )


def dodaj_tooltip_klasyfikacji(tabela, kolumna_id):
    # Tooltip z pełną nazwą i opisem klasyfikacji przyczyny w podanej kolumnie (np. '#8').
    def tekst_dymka(wiersz_id):
        klasyfikacja = tabela.set(wiersz_id, "klasyfikacja")
        if "podejrzany" in tabela.item(wiersz_id, "tags"):
            opis = OPIS_DANYCH_DO_WERYFIKACJI  # wiersz ⚠ – błędne lub niepełne dane
        else:
            opis = KLASYFIKACJA_OPISY.get(klasyfikacja, "Brak dodatkowego opisu dla tej klasyfikacji.")
        return f"{klasyfikacja}\n\n{opis}"

    return Tooltip(tabela, kolumna_docelowa=kolumna_id, pobierz_tekst=tekst_dymka)


# ---------- Funkcje pomocnicze widoku analizy przyczyn (bez Tkintera) ----------

def rozpakuj_kolumny(definicje):
    # Zamienia listę (klucz, nagłówek, szerokość, wyrównanie) na argumenty zbuduj_tabele.
    kolumny = tuple(k for k, _, _, _ in definicje)
    naglowki = {k: n for k, n, _, _ in definicje}
    szerokosci = {k: s for k, _, s, _ in definicje}
    kotwice = {k: a for k, _, _, a in definicje}
    return kolumny, naglowki, szerokosci, kotwice


def parsuj_procent(tekst):
    # Tekst ze Spinboxa -> liczba; puste lub błędne pole traktujemy jak 0.
    try:
        return float(tekst.replace(",", "."))
    except ValueError:
        return 0.0


def tekst_licznika(wybrane, liczba_waznych):
    # Opis liczby wyników nad tabelą przyczyn.
    pokazane = sum(1 for r in wybrane if not r["podejrzany"])
    podejrzane = len(wybrane) - pokazane
    tekst = f"Wyniki: {pokazane} z {liczba_waznych} pacjentów z przekroczeniem"
    if podejrzane:
        tekst += f"  (+ {podejrzane} ⚠ do weryfikacji)"
    return tekst


# ---------- Widok 'Analiza przyczyn przekroczeń' ----------

class WidokAnalizyPrzyczyn:
    """Widok 'Analiza przyczyn przekroczeń': karty, wnioski, filtry i tabela pacjentów."""

    def __init__(self, parent, dane):
        self.parent = parent

        pacjenci = filtruj_do_analizy_przyczyn(dane)
        self.rekordy = zbuduj_rekordy_przyczyn(pacjenci)
        self.liczba_waznych = sum(1 for r in self.rekordy if not r["podejrzany"])
        okolice = sorted({r["okolica"] for r in self.rekordy if not r["podejrzany"]})

        # Karty czynników i wnioski
        zbuduj_panel_podsumowania(parent, self.rekordy, KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW)
        zbuduj_panel_wnioskow(parent, wygeneruj_wnioski_analizy(self.rekordy))

        # Filtry
        self.zmienne = self._utworz_zmienne()
        zbuduj_panel_filtrow(parent, self.zmienne, okolice, ETYKIETY_GRUP_WIEKOWYCH, self.wyczysc)

        # Pasek: licznik wyników (po lewej) + eksport (po prawej)
        pasek = tk.Frame(parent)
        pasek.pack(fill="x", padx=20, pady=(8, 4))
        self.licznik = tk.Label(pasek, anchor="w", font=(CZCIONKA, 11, "bold"))
        self.licznik.pack(side="left")
        tk.Button(pasek, text="Eksportuj tabelę do CSV",
                  command=self.eksportuj_csv).pack(side="right")
        self.wybrane = []  # wiersze aktualnie widoczne w tabeli – uzupełnia odswiez()

        # Tabela
        self.tabela = self._zbuduj_tabele()

        # Każda zmiana dowolnego filtra odświeża tabelę
        for zmienna in self._wszystkie_zmienne():
            zmienna.trace_add("write", self.odswiez)

        self.odswiez()

    # ---------- stan filtrów ----------

    @staticmethod
    def _utworz_zmienne() -> dict[str, Any]:
        return {
            "czynniki": {
                klucz: tk.BooleanVar(value=True)
                for klucz in [*KLUCZE_CZYNNIKOW, KLUCZ_BRAK_CZYNNIKA]
            },
            "okolica": tk.StringVar(value=WARTOSC_WSZYSTKIE),
            "grupa_wiekowa": tk.StringVar(value=WARTOSC_WSZYSTKIE),
            "min_procent": tk.StringVar(value="0"),
            "podejrzane": tk.BooleanVar(value=True),
        }

    def _wszystkie_zmienne(self):
        z = self.zmienne
        return [*z["czynniki"].values(), z["okolica"], z["grupa_wiekowa"],
                z["min_procent"], z["podejrzane"]]

    def _aktualne_filtry(self):
        # Odczytuje zmienne Tk i zwraca argumenty dla filtruj_przyczyny.
        z = self.zmienne
        return {
            "czynniki": {k for k, zmienna in z["czynniki"].items() if zmienna.get()},
            "okolica": z["okolica"].get(),
            "grupa_wiekowa": z["grupa_wiekowa"].get(),
            "min_procent": parsuj_procent(z["min_procent"].get()),
            "pokaz_podejrzane": z["podejrzane"].get(),
        }

    def wyczysc(self):
        for zmienna in self.zmienne["czynniki"].values():
            zmienna.set(True)
        self.zmienne["okolica"].set(WARTOSC_WSZYSTKIE)
        self.zmienne["grupa_wiekowa"].set(WARTOSC_WSZYSTKIE)
        self.zmienne["min_procent"].set("0")
        self.zmienne["podejrzane"].set(True)

    # ---------- tabela ----------

    def _zbuduj_tabele(self):
        kolumny, naglowki, szerokosci, kotwice = rozpakuj_kolumny(KOLUMNY_TABELI_PRZYCZYN)
        tabela = zbuduj_tabele(self.parent, kolumny, naglowki, szerokosci, kotwice)
        tabela.tag_configure("podejrzany", background=KOLOR_TLA_PRZYP_DO_WERYFIKACJI)

        # Numer kolumny liczony z listy – nie trzeba go poprawiać po zmianie kolejności kolumn
        kolumna_klasyfikacji = f"#{kolumny.index('klasyfikacja') + 1}"
        dodaj_tooltip_klasyfikacji(tabela, kolumna_klasyfikacji)
        tabela.tooltip = TooltipTabeli(tabela, pomin_kolumny={kolumna_klasyfikacji},
                                       opisy_naglowkow=OPISY_NAGLOWKOW_PRZYCZYN)
        return tabela

    def _wypelnij_tabele(self, wybrane):
        self.tabela.delete(*self.tabela.get_children())
        for rekord in wybrane:
            tagi = ("podejrzany",) if rekord["podejrzany"] else ()
            self.tabela.insert("", "end", values=wiersz_tabeli_przyczyn(rekord), tags=tagi)

    # ---------- odświeżanie ----------

    def odswiez(self, *_):
        # *_ – trace_add przekazuje 3 argumenty (nazwa zmiennej, indeks, tryb), których nie używamy
        self.wybrane = filtruj_przyczyny(self.rekordy, **self._aktualne_filtry())
        self._wypelnij_tabele(self.wybrane)
        self.licznik.config(text=tekst_licznika(self.wybrane, self.liczba_waznych))

    def eksportuj_csv(self):
        # Zapisuje wiersze widoczne w tabeli (po filtrach) do pliku CSV dla polskiego Excela.
        if not self.wybrane:
            messagebox.showinfo("Eksport", "Brak wierszy do eksportu – zmień ustawienia filtrów.",
                                parent=self.parent)
            return

        sciezka = filedialog.asksaveasfilename(
            parent=self.parent,
            title="Zapisz tabelę jako CSV",
            defaultextension=".csv",
            filetypes=[("Plik CSV", "*.csv"), ("Wszystkie pliki", "*.*")],
            initialfile=f"analiza_przyczyn_{date.today():%Y-%m-%d}.csv",
        )
        if not sciezka:
            return  # użytkownik kliknął "Anuluj"

        try:
            przygotuj_tabele_eksportu(self.wybrane).to_csv(
                sciezka, sep=";", decimal=",", index=False, encoding="utf-8-sig",
            )
        except PermissionError:
            messagebox.showerror(
                "Eksport",
                "Nie można zapisać pliku – może jest otwarty w Excelu?\n"
                "Zamknij go i spróbuj ponownie.",
                parent=self.parent,
            )
            return

        messagebox.showinfo("Eksport", f"Zapisano {len(self.wybrane)} wierszy do pliku:\n{sciezka}",
                            parent=self.parent)


def pokaz_analize_przyczyn(parent, dane):
    return WidokAnalizyPrzyczyn(parent, dane)
