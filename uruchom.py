#Tutaj składane są okna z gotowych klocków (`przetwarzanie_danych`, `widoki`) i obsługa
#kliknięć przycisków.

import tkinter as tk
import sys
import ctypes


from stale import RODZAJE_WIDOKOW, WIDOKI_LICZEBNOSCI, SCIEZKA_DANYCH, CZCIONKA, KOLOR_NAGLOWKA, KOLOR_TEKSTU_NAGLOWKA, WIDOKI_LICZBA_PACJENTOW
from przetwarzanie_danych import wczytaj_dane, oznacz_przekroczenia, oznacz_podejrzane_dane
from widoki import (
    pokaz_liczebnosc_wg_kolumny,
    pokaz_liczbe_pacjentow_wg_wieku,
    pokaz_dashboard_przekroczenia,
    pokaz_analize_przyczyn,
    pokaz_pareto_przyczyn,
)
from komponenty import ustaw_czcionke_aplikacji, zbuduj_przycisk_rozwijany

def wlacz_dpi_awareness():
    #Windows: ostre czcionki i wykresy przy skalowaniu ekranu 125%/150%. Musi być PRZED tk.Tk().
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # starsze Windowsy
        except (AttributeError, OSError):
            pass


def obszar_roboczy(okno):
    #Zwraca (x, y, szerokość, wysokość) obszaru ekranu BEZ paska zadań.
    if sys.platform == "win32":
        from ctypes import wintypes
        prostokat = wintypes.RECT()
        SPI_GETWORKAREA = 0x0030
        if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(prostokat), 0):
            return (prostokat.left, prostokat.top,
                    prostokat.right - prostokat.left, prostokat.bottom - prostokat.top)
    # Inne systemy albo niepowodzenie – cały ekran
    return 0, 0, okno.winfo_screenwidth(), okno.winfo_screenheight()

def zbuduj_okno():
    #Tworzenie i konfiguracja głównego okna aplikacji
    wlacz_dpi_awareness()  # musi być wywołane przed tk.Tk()

    okno = tk.Tk()
    ustaw_czcionke_aplikacji(okno, rozmiar=11, rozmiar_przyciskow=10,
                             rozmiar_tabeli=10)
    okno.title("Analiza dawek TK")

    x0, y0, szer_ob, wys_ob = obszar_roboczy(okno)

    szer = min(1400, szer_ob - 20)   # preferowana szerokość, ale nie większa niż obszar roboczy
    wys = min(850, wys_ob - 60)      # ~60 px zapasu na belkę tytułową i ramkę okna
    x = x0 + (szer_ob - szer) // 2                  # wyśrodkowanie w poziomie
    y = y0 + max((wys_ob - wys - 40) // 2, 0)       # i w pionie (40 px na belkę tytułową)

    okno.geometry(f"{szer}x{wys}+{x}+{y}")
    okno.minsize(min(1100, szer), min(700, wys))

    return okno


def dodaj_naglowek(okno):
    # Dodanie tytułowego napisu na górze okna
    belka = tk.Frame(okno, bg=KOLOR_NAGLOWKA)
    belka.pack(fill="x")
    tk.Label(belka, text="Analiza danych pacjentów TK",
             font=(CZCIONKA, 15),
             bg=KOLOR_NAGLOWKA, fg=KOLOR_TEKSTU_NAGLOWKA).pack(pady=5)


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
    # Tworzenie paska przycisków przełączających widoki i zwracanie funkcji obsługującej kliknięcia
    panel = tk.Frame(okno)
    panel.pack(pady=10)

    przyciski = {}
    w_menu = {nazwa: etykieta for etykieta, nazwa in WIDOKI_LICZBA_PACJENTOW}

    def obsluz_klikniecie(wybrany):
        for tekst, przycisk in przyciski.items():
            przycisk.config(relief="sunken" if tekst == wybrany else "raised")

        # Przycisk rozwijany: wciśnięty i z opisem wyboru, gdy wybrano widok z jego listy
        if wybrany in w_menu:
            przycisk_menu.config(relief="sunken",
                                 text=f"Liczba pacjentów wg {w_menu[wybrany]} ▾")
        else:
            przycisk_menu.config(relief="raised", text="Liczba pacjentów wg ▾")

        wyczysc_kontener(kontener)
        wybierz_widok(wybrany, dane, kontener)

    przycisk_menu = zbuduj_przycisk_rozwijany(panel, "Liczba pacjentów wg",
                                              WIDOKI_LICZBA_PACJENTOW, obsluz_klikniecie)
    przycisk_menu.pack(side="left", padx=5)

    for tekst in RODZAJE_WIDOKOW:
        if tekst in w_menu:
            continue  # te widoki są w rozwijanej liście
        przycisk = tk.Button(panel, text=tekst, command=lambda t=tekst: obsluz_klikniecie(t))
        przycisk.pack(side="left", padx=5)
        przyciski[tekst] = przycisk

    return obsluz_klikniecie

def main():
#Uruchamia aplikację: wczytuje dane, buduje okno i startuje pętlę zdarzeń
    dane = oznacz_podejrzane_dane(wczytaj_dane(SCIEZKA_DANYCH))
    dane = oznacz_przekroczenia(dane)

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
