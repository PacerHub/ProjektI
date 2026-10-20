"""Komponenty interfejsu wielokrotnego użytku."""

import tkinter as tk
import tkinter.font as tkfont
import matplotlib.pyplot as plt
from stale import (
    CZCIONKA, KOLOR_NAGLOWKOW_TABELI, KOLOR_NAGLOWKOW_TABELI_HOVER, KOLOR_TEKSTU_NAGLOWKOW_TABELI,
    KATEGORIE_BMI, KOLOR_TLA_WNIOSKOW, KOLOR_AKCENTU_WNIOSKOW, KOLOR_TEKSTU_WNIOSKOW,
    KLUCZE_CZYNNIKOW, ETYKIETY_CZYNNIKOW, KLUCZ_BRAK_CZYNNIKA, ETYKIETA_BRAKU_CZYNNIKA,
    WARTOSC_WSZYSTKIE,
)
from tkinter import ttk
from agregacje import policz_aktywne_czynniki


class Tooltip:
#Dymek podpowiedzi pokazywany po dłuższym najechaniu na wybraną kolumnę Treeview.

    def __init__(self, tabela, kolumna_docelowa, pobierz_tekst, opoznienie_ms=400):
        self.tabela = tabela
        self.kolumna_docelowa = kolumna_docelowa
        self.pobierz_tekst = pobierz_tekst
        self.opoznienie_ms = opoznienie_ms
        self.okno = None
        self.zaplanowane_zadanie = None

        tabela.bind("<Motion>", self._zaplanuj, add="+")
        tabela.bind("<Leave>", self._ukryj, add="+")

    def _zaplanuj(self, event):
        self._anuluj_zadanie()
        self._ukryj()

        region = self.tabela.identify_region(event.x, event.y)
        kolumna = self.tabela.identify_column(event.x)
        wiersz_id = self.tabela.identify_row(event.y)

        if region != "cell" or kolumna != self.kolumna_docelowa or not wiersz_id:
            return

        self.zaplanowane_zadanie = self.tabela.after(
            self.opoznienie_ms,
            lambda: self._pokaz(wiersz_id, event.x_root, event.y_root)
        )

    def _pokaz(self, wiersz_id, x_root, y_root):
        tekst = self.pobierz_tekst(wiersz_id)
        self.okno = tk.Toplevel(self.tabela)
        self.okno.wm_overrideredirect(True)
        self.okno.geometry(f"+{x_root + 10}+{y_root + 10}")
        tk.Label(
            self.okno, text=tekst, justify="left", padx=10, pady=8,
            relief="solid", wraplength=350, borderwidth=1,
        ).pack()

    def _ukryj(self, event=None):
        self._anuluj_zadanie()
        if self.okno is not None:
            self.okno.destroy()
            self.okno = None

    def _anuluj_zadanie(self):
        if self.zaplanowane_zadanie is not None:
            self.tabela.after_cancel(self.zaplanowane_zadanie)
            self.zaplanowane_zadanie = None

class TooltipTabeli:
    """Dymek z pełną treścią komórki lub nagłówka Treeview – tylko gdy tekst jest ucięty."""

    MARGINES_KOMORKI = 12   # px zapasu na wewnętrzny odstęp komórki
    MARGINES_NAGLOWKA = 16  # nagłówek ma większy padding (5, 10)

    def __init__(self, tabela, pomin_kolumny=(), opoznienie_ms=500):
        self.tabela = tabela
        self.pomin_kolumny = set(pomin_kolumny)   # np. {"#6"} – kolumny z własnym tooltipem
        self.opoznienie_ms = opoznienie_ms
        self.okno = None
        self.zadanie = None
        self.pozycja = None   # (region, wiersz, kolumna) pod kursorem

        # add="+" – dokładamy obsługę, nie kasując bindów innych tooltipów
        tabela.bind("<Motion>", self._ruch, add="+")
        tabela.bind("<Leave>", self._ukryj, add="+")
        tabela.bind("<ButtonPress>", self._ukryj, add="+")
        tabela.bind("<MouseWheel>", self._ukryj, add="+")

    def _nazwa_kolumny(self, kolumna_id):
        # Zamienia '#3' na nazwę kolumny, np. 'bmi'
        kolumny = self.tabela["displaycolumns"]
        if kolumny in ("#all", ("#all",)):
            kolumny = self.tabela["columns"]
        return kolumny[int(kolumna_id[1:]) - 1]

    def _ruch(self, event):
        region = self.tabela.identify_region(event.x, event.y)
        wiersz = self.tabela.identify_row(event.y)
        kolumna = self.tabela.identify_column(event.x)

        pozycja = (region, wiersz, kolumna)
        if pozycja == self.pozycja:
            return  # kursor wciąż nad tą samą komórką – nic nie zmieniamy
        self.pozycja = pozycja
        self._schowaj_okno()

        if region not in ("cell", "heading") or not kolumna or kolumna in self.pomin_kolumny:
            return
        if region == "cell" and not wiersz:
            return

        x, y = event.x_root, event.y_root
        self.zadanie = self.tabela.after(
            self.opoznienie_ms, lambda: self._pokaz(region, wiersz, kolumna, x, y)
        )

    def _tekst_i_czy_uciety(self, region, wiersz, kolumna_id):
        try:
            nazwa = self._nazwa_kolumny(kolumna_id)
        except (IndexError, ValueError):
            return "", False

        styl = ttk.Style(self.tabela)
        if region == "heading":
            tekst = self.tabela.heading(nazwa, "text")
            opis_czcionki = styl.lookup("Treeview.Heading", "font")
            margines = self.MARGINES_NAGLOWKA
        else:
            tekst = str(self.tabela.set(wiersz, nazwa))
            opis_czcionki = styl.lookup("Treeview", "font")
            margines = self.MARGINES_KOMORKI

        if not tekst.strip():
            return "", False

        czcionka = tkfont.Font(font=opis_czcionki) if opis_czcionki else tkfont.nametofont("TkDefaultFont")
        najdluzsza_linia = max(czcionka.measure(linia) for linia in tekst.split("\n"))
        szerokosc = self.tabela.column(nazwa, "width")
        return tekst, najdluzsza_linia + margines > szerokosc

    def _pokaz(self, region, wiersz, kolumna, x_root, y_root):
        self.zadanie = None
        tekst, uciety = self._tekst_i_czy_uciety(region, wiersz, kolumna)
        if not uciety:
            return

        self.okno = tk.Toplevel(self.tabela)
        self.okno.wm_overrideredirect(True)
        self.okno.geometry(f"+{x_root + 12}+{y_root + 12}")
        tk.Label(
            self.okno, text=tekst, justify="left", padx=8, pady=5,
            bg="#ffffe0", relief="solid", borderwidth=1, wraplength=400,
        ).pack()

    def _schowaj_okno(self):
        if self.zadanie is not None:
            self.tabela.after_cancel(self.zadanie)
            self.zadanie = None
        if self.okno is not None:
            self.okno.destroy()
            self.okno = None

    def _ukryj(self, event=None):
        self._schowaj_okno()
        self.pozycja = None   # po powrocie na tę samą komórkę dymek pokaże się znowu

def zbuduj_tabele(parent, kolumny, naglowki, szerokosci, kotwice=None):
    # Tworzenie Treeview ze scrollbarami (pionowym i poziomym) i zwracanie gotowego widgetu
    kotwice = kotwice or {}

    ramka = tk.Frame(parent)
    ramka.pack(fill="both", expand=True)

    tabela = ttk.Treeview(ramka, columns=kolumny, show="headings")
    for klucz in kolumny:
        tabela.heading(klucz, text=naglowki.get(klucz, klucz))
        tabela.column(klucz, width=szerokosci.get(klucz, 100), anchor=kotwice.get(klucz, "center"))

    pasek_pionowy = ttk.Scrollbar(ramka, orient="vertical", command=tabela.yview)
    pasek_poziomy = ttk.Scrollbar(ramka, orient="horizontal", command=tabela.xview)
    tabela.configure(yscrollcommand=pasek_pionowy.set, xscrollcommand=pasek_poziomy.set)

    tabela.grid(row=0, column=0, sticky="nsew")
    pasek_pionowy.grid(row=0, column=1, sticky="ns")
    pasek_poziomy.grid(row=1, column=0, sticky="ew")
    ramka.grid_rowconfigure(0, weight=1)
    ramka.grid_columnconfigure(0, weight=1)

    return tabela

def zbuduj_panel_podsumowania(parent, wyniki, klucze_czynnikow, etykiety_czynnikow):
#Tworzenie poziomego paska 'kart', po jednej na czynnik, z liczbą aktywnych pacjentów
    panel = tk.Frame(parent)
    panel.pack(fill="x", padx=10, pady=(5, 10))

    liczba_wszystkich = len(wyniki)

    for klucz in klucze_czynnikow:
        liczba_aktywnych = policz_aktywne_czynniki(wyniki, klucz)

        karta = tk.Frame(panel, relief="groove", borderwidth=1, padx=10, pady=6)
        karta.pack(side="left", padx=5, fill="x", expand=True)

        tk.Label(
            karta,
            text=f"{liczba_aktywnych}/{liczba_wszystkich}",
            font=(CZCIONKA, 11)
        ).pack()

        tk.Label(
            karta,
            text=etykiety_czynnikow[klucz].replace("\n", " "),
            font=(CZCIONKA, 11),
            wraplength=140,
            justify="center",
        ).pack()
    return panel

def ustaw_czcionke_aplikacji(root, rozmiar=10, rozmiar_przyciskow=9, rozmiar_tabeli=10):
    # Wszystkie wbudowane czcionki Tk – przyciski, etykiety, tabele, nagłówki, menu, pola tekstowe
    for nazwa in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont",
                  "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        tkfont.nametofont(nazwa, root=root).configure(family=CZCIONKA, size=rozmiar)

    # Wykresy matplotlib korzystają z własnych ustawień
    plt.rcParams["font.family"] = CZCIONKA
    plt.rcParams["font.size"] = 11

    # Mniejsza czcionka na przyciskach
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TButton", font=(CZCIONKA, rozmiar_przyciskow))  # ttk.Button
    root.option_add("*Button.font", f"{{{CZCIONKA}}} {rozmiar_przyciskow}")  # tk.Button
    root.option_add("*Menubutton.font", f"{{{CZCIONKA}}} {rozmiar_przyciskow}") #przycisk do listy

    # Mniejsza czcionka w tabelach
    style.configure("Treeview", font=(CZCIONKA, rozmiar_tabeli),
                    rowheight=int(rozmiar_tabeli * 2.4))

    style.configure("Treeview.Heading", font=(CZCIONKA, rozmiar_tabeli),
                    padding=(5, 10),
                    background=KOLOR_NAGLOWKOW_TABELI,
                    foreground=KOLOR_TEKSTU_NAGLOWKOW_TABELI)
    style.map("Treeview.Heading",
              background=[("active", KOLOR_NAGLOWKOW_TABELI_HOVER)])

def zbuduj_przycisk_rozwijany(rodzic, tekst, opcje, po_wyborze):
    """Przycisk, który po kliknięciu rozwija listę widoków."""
    przycisk = tk.Menubutton(rodzic, text=f"{tekst} ▾", relief="raised",
                             borderwidth=2, padx=8, pady=4, direction="below")
    menu = tk.Menu(przycisk, tearoff=False)
    for etykieta, nazwa_widoku in opcje:
        menu.add_command(label=etykieta,
                         command=lambda n=nazwa_widoku: po_wyborze(n))
    przycisk["menu"] = menu
    return przycisk

def zbuduj_panel_wnioskow(parent, tekst, side="top", pady=(5, 10)):
    """Wyróżniony panel z automatycznie wygenerowanymi wnioskami.

    Ramka z jasnym tłem, kolorowym paskiem po lewej, tytułem 'Wnioski'
    i tekstem, który zawija się do aktualnej szerokości okna.
    """
    panel = tk.Frame(parent, bg=KOLOR_TLA_WNIOSKOW,
                     highlightbackground=KOLOR_AKCENTU_WNIOSKOW, highlightthickness=1)
    panel.pack(side=side, fill="x", padx=20, pady=pady)

    # Pionowy pasek akcentu po lewej stronie
    tk.Frame(panel, bg=KOLOR_AKCENTU_WNIOSKOW, width=6).pack(side="left", fill="y")

    tresc = tk.Frame(panel, bg=KOLOR_TLA_WNIOSKOW)
    tresc.pack(side="left", fill="both", expand=True, padx=12, pady=8)

    tk.Label(tresc, text="Wnioski", font=(CZCIONKA, 12, "bold"),
             bg=KOLOR_TLA_WNIOSKOW, fg=KOLOR_AKCENTU_WNIOSKOW,
             anchor="w").pack(fill="x")

    etykieta = tk.Label(tresc, text=tekst, font=(CZCIONKA, 11),
                        bg=KOLOR_TLA_WNIOSKOW, fg=KOLOR_TEKSTU_WNIOSKOW,
                        justify="left", anchor="w")
    etykieta.pack(fill="x", pady=(2, 0))

    # Zawijanie tekstu do bieżącej szerokości panelu (także po zmianie rozmiaru okna)
    tresc.bind("<Configure>", lambda e: etykieta.config(wraplength=max(e.width - 10, 200)))

    return panel


def zbuduj_filtr_plci(parent, zmienna):
    """Pasek radiobuttonów do filtrowania danych wg płci: wszyscy / kobiety / mężczyźni."""
    panel = tk.Frame(parent)
    panel.pack(fill="x", pady=(0, 10))

    tk.Label(panel, text="Płeć:", font=(CZCIONKA, 10, "bold")).pack(side="left", padx=(10, 5))

    opcje = [("Wszyscy", "wszyscy"), ("Kobiety", "kobiety"), ("Mężczyźni", "mezczyzni")]
    for tekst, wartosc in opcje:
        tk.Radiobutton(
            panel, text=tekst, variable=zmienna, value=wartosc, font=(CZCIONKA, 10),
        ).pack(side="left", padx=5)

    return panel


def zbuduj_filtr_kategorii_bmi(parent, zmienna):
    """Pasek radiobuttonów do filtrowania danych wg kategorii BMI."""
    panel = tk.Frame(parent)
    panel.pack(fill="x", pady=(0, 10))

    tk.Label(panel, text="Kategoria BMI:", font=(CZCIONKA, 10, "bold")).pack(side="left", padx=(10, 5))

    tk.Radiobutton(
        panel, text="Wszyscy", variable=zmienna, value="wszyscy", font=(CZCIONKA, 10),
    ).pack(side="left", padx=5)

    for kategoria in KATEGORIE_BMI:
        tk.Radiobutton(
            panel, text=kategoria, variable=zmienna, value=kategoria, font=(CZCIONKA, 10),
        ).pack(side="left", padx=5)

    return panel
def zbuduj_panel_filtrow(parent, zmienne, okolice, grupy_wiekowe, po_wyczyszczeniu):
    """Panel filtrów widoku 'Filtr przyczyn przekroczeń'.

    zmienne – słownik zmiennych Tk: 'czynniki' (słownik klucz -> BooleanVar), 'okolica',
    'grupa_wiekowa', 'min_procent' (StringVar) i 'podejrzane' (BooleanVar).
    Odświeżanie tabeli podpina widok przez trace_add – tutaj budujemy tylko kontrolki.
    """
    panel = tk.Frame(parent)
    panel.pack(fill="x", padx=20, pady=(5, 5))

    # --- Wiersz 1: pola wyboru przyczyn ---
    ramka_przyczyn = tk.LabelFrame(
        panel, text="Przyczyny – pokaż pacjentów z którąkolwiek zaznaczoną",
        font=(CZCIONKA, 10, "bold"), padx=8, pady=4,
    )
    ramka_przyczyn.pack(fill="x")

    etykiety = {klucz: ETYKIETY_CZYNNIKOW[klucz].replace("\n", " ") for klucz in KLUCZE_CZYNNIKOW}
    etykiety[KLUCZ_BRAK_CZYNNIKA] = ETYKIETA_BRAKU_CZYNNIKA

    for klucz, zmienna in zmienne["czynniki"].items():
        tk.Checkbutton(ramka_przyczyn, text=etykiety[klucz], variable=zmienna).pack(side="left", padx=6)

    # --- Wiersz 2: okolica, grupa wiekowa, min. %, podejrzane, wyczyść ---
    wiersz = tk.Frame(panel)
    wiersz.pack(fill="x", pady=(8, 0))

    tk.Label(wiersz, text="Okolica:", font=(CZCIONKA, 10, "bold")).pack(side="left")
    ttk.Combobox(
        wiersz, textvariable=zmienne["okolica"], values=[WARTOSC_WSZYSTKIE, *okolice],
        state="readonly", width=24,
    ).pack(side="left", padx=(5, 20))

    tk.Label(wiersz, text="Grupa wiekowa:", font=(CZCIONKA, 10, "bold")).pack(side="left")
    ttk.Combobox(
        wiersz, textvariable=zmienne["grupa_wiekowa"], values=[WARTOSC_WSZYSTKIE, *grupy_wiekowe],
        state="readonly", width=14,
    ).pack(side="left", padx=(5, 20))

    tk.Label(wiersz, text="Min. % przekroczenia:", font=(CZCIONKA, 10, "bold")).pack(side="left")
    tk.Spinbox(
        wiersz, from_=0, to=200, increment=5, textvariable=zmienne["min_procent"], width=6,
    ).pack(side="left", padx=(5, 20))

    tk.Checkbutton(
        wiersz, text="Pokaż wiersze do weryfikacji (⚠)", variable=zmienne["podejrzane"],
    ).pack(side="left")

    tk.Button(wiersz, text="Wyczyść filtry", command=po_wyczyszczeniu).pack(side="right")

    return panel