"""Punkt wejścia aplikacji: budowa okna Tkinter i przełączanie widoków przyciskami."""

import tkinter as tk

from constants import RODZAJE_WIDOKOW, SCIEZKA_DANYCH
from data_processing import wczytaj_dane, oznacz_przekroczenia
from views import pokaz_liczebnosc_wg_kolumny, pokaz_tabele_przekroczenia, pokaz_analize_przyczyn


def zbuduj_okno():
    okno = tk.Tk()
    okno.title("Analiza dawek TK")
    okno.geometry("1200x800")
    okno.minsize(1200, 800)
    okno.maxsize(1200, 800)
    okno.option_add("*Font", "Cambria 10")
    return okno


def dodaj_naglowek(okno):
    tk.Label(okno, text="Analiza danych pacjentów TK", font=("Cambria", 18)).pack(pady=30)


def wyczysc_kontener(kontener):
    for widget in kontener.winfo_children():
        widget.destroy()


def wybierz_widok(wybrany, dane, kontener):
    if wybrany in WIDOKI_LICZEBNOSCI:
        ustawienia = WIDOKI_LICZEBNOSCI[wybrany]
        pokaz_liczebnosc_wg_kolumny(
            kontener,
            dane,
            ustawienia["kolumna"],
            wybrany,
            ustawienia["sortuj_wg_indeksu"],
            ustawienia["typ_wykresu"],
            ustawienia["kolory"])
    elif wybrany == "Liczba pacjentów wg wieku":
        pokaz_liczebnosc_wg_kolumny(kontener, dane, "wiek", wybrany, sortuj_wg_indeksu=True)
    elif wybrany == "Pacjenci z przekroczoną dawką":
        pokaz_dashboard_przekroczenia(kontener, dane)
    elif wybrany == "Analiza przyczyn przekroczeń":
        pokaz_analize_przyczyn(kontener, dane)


def dodaj_panel_przyciskow(okno, dane, kontener):
    panel = tk.Frame(okno)
    panel.pack(pady=10)
    przyciski = {}

    def obsluz_klikniecie(wybrany):
        for tekst, przycisk in przyciski.items():
            przycisk.config(relief="sunken" if tekst == wybrany else "raised")
        wyczysc_kontener(kontener)
        wybierz_widok(wybrany, dane, kontener)

    for tekst in RODZAJE_WIDOKOW:
        przycisk = tk.Button(panel, text=tekst, command=lambda t=tekst: obsluz_klikniecie(t))
        przycisk.pack(side="left", padx=5)
        przyciski[tekst] = przycisk

    return obsluz_klikniecie


def main():
    dane = oznacz_przekroczenia(wczytaj_dane(SCIEZKA_DANYCH))
    okno = zbuduj_okno()
    dodaj_naglowek(okno)

    kontener = tk.Frame(okno)
    obsluz_klikniecie = dodaj_panel_przyciskow(okno, dane, kontener)
    kontener.pack_propagate(False)
    kontener.pack(fill="both", expand=True)

    obsluz_klikniecie(RODZAJE_WIDOKOW[0])
    okno.mainloop()


if __name__ == "__main__":
    main()