"""Komponenty interfejsu wielokrotnego użytku."""

import tkinter as tk
from tkinter import ttk
from agregacje import policz_aktywne_czynniki

class Tooltip:
    """Dymek podpowiedzi pokazywany po dłuższym najechaniu na wybraną kolumnę Treeview."""

    def __init__(self, tabela, kolumna_docelowa, pobierz_tekst, opoznienie_ms=400):
        self.tabela = tabela
        self.kolumna_docelowa = kolumna_docelowa
        self.pobierz_tekst = pobierz_tekst
        self.opoznienie_ms = opoznienie_ms
        self.okno = None
        self.zaplanowane_zadanie = None

        tabela.bind("<Motion>", self._zaplanuj)
        tabela.bind("<Leave>", self._ukryj)

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


def zbuduj_tabele(parent, kolumny, naglowki, szerokosci, kotwice=None):
    """Tworzy Treeview ze scrollbarami (pionowym i poziomym) i zwraca gotowy widget."""
    kotwice = kotwice or {}

    styl = ttk.Style()
    styl.theme_use("clam")
    styl.configure("Treeview.Heading", padding=(5, 10), font=("Cambria", 9, "bold"))
    styl.configure("Treeview", font=("Cambria", 10), rowheight=25)

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
    """Tworzy poziomy pasek 'kart', po jednej na czynnik, z liczbą aktywnych pacjentów."""
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
            font=("Cambria", 15, "bold"),
        ).pack()

        tk.Label(
            karta,
            text=etykiety_czynnikow[klucz].replace("\n", " "),
            font=("Cambria", 9),
            wraplength=140,
            justify="center",
        ).pack()

    return panel