#Tutaj składane są okna z gotowych klocków (`przetwarzanie_danych`, `widoki`) i obsługa
#kliknięć przycisków.

import tkinter as tk


from stałe import RODZAJE_WIDOKOW, WIDOKI_LICZEBNOSCI, SCIEZKA_DANYCH
from przetwarzanie_danych import wczytaj_dane, oznacz_przekroczenia, oznacz_podejrzane_dane
from widoki import (
    pokaz_liczebnosc_wg_kolumny,
    pokaz_liczbe_pacjentow_wg_wieku,
    pokaz_dashboard_przekroczenia,
    pokaz_analize_przyczyn,
    pokaz_pareto_przyczyn,
)
from komponenty import ustaw_czcionke_aplikacji


def main():
    dane = wczytaj_dane(SCIEZKA_DANYCH)
    dane = oznacz_podejrzane_dane(dane)
    dane = oznacz_przekroczenia(dane)


def zbuduj_okno():
#Tworzenie i konfiguracja głównego okna aplikacji
    okno = tk.Tk()
    ustaw_czcionke_aplikacji(okno)
    okno.title("Analiza dawek TK")
    okno.geometry("1400x800")
    szer_ekranu = okno.winfo_screenwidth()
    wys_ekranu = okno.winfo_screenheight()

    szer = min(1400, szer_ekranu)        # preferowana szerokość, ale nie większa niż ekran
    wys = min(900, wys_ekranu - 80)      # ~80 px zapasu na pasek zadań i belkę tytułową
    x = (szer_ekranu - szer) // 2        # wyśrodkowanie w poziomie

    okno.geometry(f"{szer}x{wys}+{x}+0")
    okno.minsize(1400, 800)
    okno.maxsize(1400, 800)
    okno.option_add("*Font", "Book Antiqua")
    return okno


def dodaj_naglowek(okno):
#Dodanie tytułowego napisu na górze okna
    tk.Label(okno, text="Analiza danych pacjentów TK", font=("Book Antiqua", 18)).pack(pady=5)


def wyczysc_kontener(kontener):
#Usuwanie wszystkich widgetów z kontenera przed narysowaniem nowego widoku.
    for widget in kontener.winfo_children():
        widget.destroy()

def wybierz_widok(wybrany, dane, kontener):
#Deleguje rysowanie do właściwej funkcji widoku na podstawie nazwy przycisku
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
#Tworzenie paska przycisków przełączających widoki i zwracanie funkcji obsługującej kliknięcia
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
#Uruchamia aplikację: wczytuje dane, buduje okno i startuje pętlę zdarzeń
    dane = oznacz_przekroczenia(wczytaj_dane(SCIEZKA_DANYCH))

    okno = zbuduj_okno()
    dodaj_naglowek(okno)


    kontener = tk.Frame(okno)

    obsluz_klikniecie = dodaj_panel_przyciskow(okno, dane, kontener)

# kontener ma za zadanie trzymać przydzielony rozmiar
    kontener.pack_propagate(False)
    kontener.pack(fill="both", expand=True)

    obsluz_klikniecie(RODZAJE_WIDOKOW[0])

    okno.mainloop()


if __name__ == "__main__":
    main()
