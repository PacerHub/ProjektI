"""Punkt wejścia aplikacji: budowa okna Tkinter i przełączanie widoków przyciskami.

Ten moduł nie liczy i nie rysuje niczego sam – jedyną jego odpowiedzialnością
jest złożenie okna z gotowych klocków (`data_processing`, `views`) i obsługa
kliknięć przycisków.
"""

import tkinter as tk

from constants import RODZAJE_WIDOKOW, WIDOKI_LICZEBNOSCI, SCIEZKA_DANYCH
from data_processing import wczytaj_dane, oznacz_przekroczenia, oznacz_podejrzane_dane
from views import (
    pokaz_liczebnosc_wg_kolumny,
    pokaz_liczbe_pacjentow_wg_wieku,
    pokaz_dashboard_przekroczenia,
    pokaz_analize_przyczyn,
    pokaz_pareto_przyczyn,
)



def main():
    dane = wczytaj_dane(SCIEZKA_DANYCH)
    dane = oznacz_podejrzane_dane(dane)
    dane = oznacz_przekroczenia(dane)


def zbuduj_okno():
    """Tworzy i konfiguruje główne okno aplikacji."""
    okno = tk.Tk()
    okno.title("Analiza dawek TK")
    okno.geometry("1400x800")
    okno.minsize(1400, 800)
    okno.maxsize(1400, 800)
    okno.option_add("*Font", "Cambria 10")
    return okno


def dodaj_naglowek(okno):
    """Dodaje tytułowy napis na górze okna."""
    tk.Label(okno, text="Analiza danych pacjentów TK", font=("Cambria", 18)).pack(pady=30)


def wyczysc_kontener(kontener):
    """Usuwa wszystkie widgety z kontenera przed narysowaniem nowego widoku."""
    for widget in kontener.winfo_children():
        widget.destroy()

def wybierz_widok(wybrany, dane, kontener):
    """Deleguje rysowanie do właściwej funkcji widoku na podstawie nazwy przycisku."""
    if wybrany in WIDOKI_LICZEBNOSCI:
        ustawienia = WIDOKI_LICZEBNOSCI[wybrany]
        pokaz_liczebnosc_wg_kolumny(
            kontener,
            dane,
            ustawienia["kolumna"],
            wybrany,
            ustawienia["sortuj_wg_indeksu"],
            ustawienia["typ_wykresu"],
            ustawienia["kolory"],
                    )
    elif wybrany == "Liczba pacjentów wg wieku":
        pokaz_liczbe_pacjentow_wg_wieku(kontener, dane)
    elif wybrany == "Pacjenci z przekroczoną dawką":
        pokaz_dashboard_przekroczenia(kontener, dane)
    elif wybrany == "Analiza przyczyn przekroczeń":
        pokaz_analize_przyczyn(kontener, dane)
    elif wybrany == "Pareto przyczyn przekroczeń":
        pokaz_pareto_przyczyn(kontener, dane)


def dodaj_panel_przyciskow(okno, dane, kontener):
    """Tworzy pasek przycisków przełączających widoki i zwraca funkcję obsługującą kliknięcia."""
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
    """Uruchamia aplikację: wczytuje dane, buduje okno i startuje pętlę zdarzeń."""
    dane = oznacz_przekroczenia(wczytaj_dane(SCIEZKA_DANYCH))

    okno = zbuduj_okno()
    dodaj_naglowek(okno)

    # Kontener na wykres/tabelę tworzymy już teraz (potrzebny do domknięcia
    # obsluz_klikniecie), ale PAKUJEMY go dopiero PO panelu przycisków —
    # inaczej kontener (fill+expand) zabrałby całą przestrzeń i przyciski
    # nie miałyby się gdzie zmieścić.
    kontener = tk.Frame(okno)

    obsluz_klikniecie = dodaj_panel_przyciskow(okno, dane, kontener)

    # pack_propagate(False): kontener ma trzymać rozmiar przydzielony przez
    # pack (fill/expand), a NIE dopasowywać się do rozmiaru swojej zawartości
    # (np. dużego wykresu). Dzięki temu żaden wykres nie rozepchnie okna.
    kontener.pack_propagate(False)
    kontener.pack(fill="both", expand=True)

    obsluz_klikniecie(RODZAJE_WIDOKOW[0])

    okno.mainloop()


if __name__ == "__main__":
    main()
