import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk


# =========================
# WCZYTANIE DANYCH
# =========================
from constants import EXAM_REGION, PROG_WYSOKIEGO_DLP_FAZY, RODZAJE_WIDOKOW, SCIEZKA_DANYCH, KLASYFIKACJA_OPISY

from data_processing import wczytaj_dane, oznacz_przekroczenia, analizuj_pacjenta
...
dane = oznacz_przekroczenia(wczytaj_dane(SCIEZKA_DANYCH))

# =========================

okno = tk.Tk()

okno.title("Analiza dawek TK")
okno.geometry("1200x800")
okno.minsize(1200, 800)
okno.maxsize(1200, 800)
okno.option_add("*Font", "Cambria 10")

# =========================
# NAPIS
# =========================

napis = tk.Label(
    okno,
    text="Analiza danych pacjentów TK",
    font=("Cambria", 18)
)

napis.pack(pady=30)

# =========================
# PANEL WYBORU
# =========================

panel_wyboru = tk.Frame(okno)
panel_wyboru.pack(pady=10)


# =========================
# MIEJSCE NA WYKRES
# =========================

miejsce_na_wykres = tk.Frame(okno)

miejsce_na_wykres.pack(
    fill="both",
    expand=True
)


# Na początku nie ma jeszcze wykresu
canvas = None

# =========================
# FUNKCJA POKAZUJĄCA WYKRES
# =========================
def pokaz_wykres(wybrany_wykres):
    for tekst, przycisk in przyciski.items():
        przycisk.config(relief="sunken" if tekst == wybrany_wykres else "raised")

    # Usuwamy poprzedni wykres lub tabelę
    for widget in miejsce_na_wykres.winfo_children():
        widget.destroy()

    global canvas
    canvas = None

   # ==========================================
    # PACJENCI Z PRZEKROCZONĄ DAWKĄ
    # ==========================================

    if wybrany_wykres == "Pacjenci z przekroczoną dawką":

        pacjenci_przekroczenie = dane[
            dane["przekroczenie_dlp"] == True
        ]

        # Ramka przeznaczona tylko na tabelę
        ramka_tabeli = tk.Frame(miejsce_na_wykres)

        ramka_tabeli.pack(
            fill="both",
            expand=True
        )

        # ==========================================
        # TABELA
        # ==========================================
        styl = ttk.Style()
        styl.theme_use("clam")
        styl.configure("Treeview.Heading", padding=(5, 15), font=("Cambria", 10, "bold"))
        styl.configure("Treeview", font=("Cambria", 10), rowheight=25)

        tabela = ttk.Treeview(
            ramka_tabeli,
            columns=(
                "patient_id",
                "wiek",
                "badanie",
                "fazy",
                "onkologiczny",
                "dlp_referencyjny",
                "dlp_zmierzony",
                "przekroczenie",
                "dlp_lacznie",
            ),
            show="headings"
        )

        # Nagłówki
        tabela.heading(
            "patient_id",
            text="Pacjent"
        )

        tabela.heading(
            "wiek",
            text="Wiek"
        )

        tabela.heading(
            "badanie",
            text="Rodzaj badania"
        )

        tabela.heading(
            "fazy",
            text="Liczba faz"
        )

        tabela.heading(
            "onkologiczny",
            text="Protokół onkologiczny"
        )

        tabela.heading(
            "dlp_referencyjny",
            text="DPR na fazę"
        )

        tabela.heading(
            "dlp_zmierzony",
            text="DLP zmierzone na fazę"
        )

        tabela.heading(
            "przekroczenie",
            text="Przekroczenie"
        )

        tabela.heading(
            "dlp_lacznie",
            text=("DLP całego badania \n (informacyjnie)")
        )


        # ==========================================
        # SZEROKOŚĆ KOLUMN
        # ==========================================

        tabela.column(
            "patient_id",
            width=80,
            anchor="center"
        )

        tabela.column(
            "wiek",
            width=60,
            anchor="center"
        )

        tabela.column(
            "badanie",
            width=220,
            anchor="w"
        )

        tabela.column(
            "fazy",
            width=80,
            anchor="center"
        )

        tabela.column(
            "onkologiczny",
            width=160,
            anchor="center"
        )

        tabela.column(
            "dlp_referencyjny",
            width=150,
            anchor="center"
        )

        tabela.column(
            "dlp_zmierzony",
            width=150,
            anchor="center"
        )

        tabela.column(
            "przekroczenie",
            width=120,
            anchor="center"
        )

        tabela.column(
            "dlp_lacznie",
            width=120,
            anchor="center"
        )

        # ==========================================
        # PASEK PIONOWY
        # ==========================================

        pasek_pionowy = ttk.Scrollbar(
            ramka_tabeli,
            orient="vertical",
            command=tabela.yview
        )

        # ==========================================
        # PASEK POZIOMY
        # ==========================================

        pasek_poziomy = ttk.Scrollbar(
            ramka_tabeli,
            orient="horizontal",
            command=tabela.xview
        )

        tabela.configure(
            yscrollcommand=pasek_pionowy.set,
            xscrollcommand=pasek_poziomy.set
        )

        # ==========================================
        # UMIESZCZENIE TABELI
        # ==========================================

        tabela.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        pasek_pionowy.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        pasek_poziomy.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        ramka_tabeli.grid_rowconfigure(
            0,
            weight=1
        )

        ramka_tabeli.grid_columnconfigure(
            0,
            weight=1
        )

        # ==========================================
        # TOOLTIP DLA DPR i DLP
        # ==========================================

        KOLUMNY_OPISY_NAGLOWKOW = {
            "#6": (
                "DPR – Diagnostyczny Poziom Referencyjny.\n"
                "Punkt odniesienia dla typowego pacjenta,\n"
                "nie sztywny limit prawny. Może być\n"
                "przekroczony przy uzasadnieniu klinicznym."
            ),
            "#7": (
                "DLP – iloczyn dawka-długość.\n"
                "Rzeczywista wartość zmierzona\n"
                "u pacjenta dla pojedynczej fazy\n"
                "badania — porównywana z DPR."
            ),
            "#9": (
                "Suma DLP z wszystkich\n"
                "faz badania (informacyjnie)."
            ),
        }

        tooltip = None
        tooltip_job = None

        def zaplanuj_tooltip(event):
            nonlocal tooltip_job

            if tooltip_job is not None:
                tabela.after_cancel(tooltip_job)
                tooltip_job = None

            ukryj_tooltip()

            region = tabela.identify_region(event.x, event.y)
            kolumna = tabela.identify_column(event.x)

            if region == "heading" and kolumna in KOLUMNY_OPISY_NAGLOWKOW:
                tooltip_job = tabela.after(
                    400,
                    lambda: pokaz_tooltip(KOLUMNY_OPISY_NAGLOWKOW[kolumna], event.x_root, event.y_root)
                )
                return

            if region == "cell" and kolumna == "#3":
                wiersz_id = tabela.identify_row(event.y)
                if not wiersz_id:
                    return
                pelny_tekst = tabela.set(wiersz_id, "badanie")
                tooltip_job = tabela.after(
                    400,
                    lambda: pokaz_tooltip(pelny_tekst, event.x_root, event.y_root)
                )
                return

        def pokaz_tooltip(tresc, x_root, y_root):
            nonlocal tooltip

            tooltip = tk.Toplevel(tabela)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{x_root + 10}+{y_root + 10}")

            tk.Label(
                tooltip,
                text=tresc,
                justify="left",
                padx=10,
                pady=8,
                relief="solid",
                wraplength=300,
                borderwidth=1
            ).pack()

        def ukryj_tooltip(event=None):
            nonlocal tooltip, tooltip_job

            if tooltip_job is not None:
                tabela.after_cancel(tooltip_job)
                tooltip_job = None

            if tooltip is not None:
                tooltip.destroy()
                tooltip = None

        tabela.bind("<Motion>", zaplanuj_tooltip)
        tabela.bind("<Leave>", ukryj_tooltip)

        # ==========================================
        # WSTAWIENIE DANYCH DO TABELI
        # ==========================================

        for _, wiersz in pacjenci_przekroczenie.iterrows():

            onkologiczny = wiersz[
                "protokol_onkologiczny_jamy_brzusznej"
            ]

            if pd.isna(onkologiczny):
                onkologiczny = "nie dotyczy"
            elif onkologiczny:
                onkologiczny = "tak"
            else:
                onkologiczny = "nie"

            tabela.insert(
                "",
                "end",
                values=(
                    wiersz["patient_id"],
                    wiersz["wiek"],
                    wiersz["rodzaj_badania_tk"],
                    wiersz["liczba_faz"],
                    onkologiczny,
                    round(
                        wiersz["dlp_referencyjny_na_faze_mGy_cm"],
                        1
                    ),
                    round(
                        wiersz[
                            "dlp_zmierzony_na_faze_mGy_cm"
                        ],
                        1
                    ),
                    round(
                        wiersz["przekroczenie_o"],
                        1
                    ),
                    round(
                        wiersz["dlp_zmierzony_lacznie_mGy_cm"],
                        1
                    )
                )
            )

        return

        # ==========================================
        # ANALIZA PRZYCZYN PRZEKROCZEŃ
        # ==========================================

    if wybrany_wykres == "Analiza przyczyn przekroczeń":

        pacjenci_przekroczenie = dane[dane["przekroczenie_dlp"] == True]

        ramka_tabeli = tk.Frame(miejsce_na_wykres)
        ramka_tabeli.pack(fill="both", expand=True)

        tabela_analizy = ttk.Treeview(
            ramka_tabeli,
            columns=(
                "patient_id",
                "okolica",
                "bmi",
                "kategoria_faz",
                "procent",
                "klasyfikacja",
                "czynniki",
            ),
            show="headings"
        )

        tabela_analizy.heading("patient_id", text="Pacjent")
        tabela_analizy.heading("okolica", text="Okolica anatomiczna")
        tabela_analizy.heading("bmi", text="BMI (kategoria)")
        tabela_analizy.heading("kategoria_faz", text="Liczba faz")
        tabela_analizy.heading("procent", text="% przekroczenia")
        tabela_analizy.heading("klasyfikacja", text="Klasyfikacja przyczyny")
        tabela_analizy.heading("czynniki", text="Aktywne czynniki")

        tabela_analizy.column("patient_id", width=70, anchor="center")
        tabela_analizy.column("okolica", width=150, anchor="w")
        tabela_analizy.column("bmi", width=160, anchor="center")
        tabela_analizy.column("kategoria_faz", width=90, anchor="center")
        tabela_analizy.column("procent", width=110, anchor="center")
        tabela_analizy.column("klasyfikacja", width=230, anchor="w")
        tabela_analizy.column("czynniki", width=280, anchor="w")

        pasek_pionowy2 = ttk.Scrollbar(ramka_tabeli, orient="vertical", command=tabela_analizy.yview)
        pasek_poziomy2 = ttk.Scrollbar(ramka_tabeli, orient="horizontal", command=tabela_analizy.xview)
        tabela_analizy.configure(
            yscrollcommand=pasek_pionowy2.set,
            xscrollcommand=pasek_poziomy2.set
        )

        tabela_analizy.grid(row=0, column=0, sticky="nsew")
        pasek_pionowy2.grid(row=0, column=1, sticky="ns")
        pasek_poziomy2.grid(row=1, column=0, sticky="ew")
        ramka_tabeli.grid_rowconfigure(0, weight=1)
        ramka_tabeli.grid_columnconfigure(0, weight=1)


        tooltip_analiza = None
        tooltip_job = None

        def zaplanuj_tooltip(event):
            nonlocal tooltip_job

            if tooltip_job is not None:
                tabela_analizy.after_cancel(tooltip_job)
                tooltip_job = None

            ukryj_tooltip_analiza()

            region = tabela_analizy.identify_region(event.x, event.y)
            if region != "cell":
                return

            kolumna = tabela_analizy.identify_column(event.x)
            wiersz_id = tabela_analizy.identify_row(event.y)

            if kolumna not in ("#6", "#7") or not wiersz_id:
                return

            tooltip_job = tabela_analizy.after(
                400,
                lambda: pokaz_tooltip_analiza(wiersz_id, kolumna, event.x_root, event.y_root)
            )

        def pokaz_tooltip_analiza(wiersz_id, kolumna, x_root, y_root):
            nonlocal tooltip_analiza

            if kolumna == "#7":
                pelny_tekst = tabela_analizy.set(wiersz_id, "czynniki")
            else:  # "#6" - klasyfikacja
                wartosc_klasyfikacji = tabela_analizy.set(wiersz_id, "klasyfikacja")
                pelny_tekst = KLASYFIKACJA_OPISY.get(
                    wartosc_klasyfikacji,
                    "Brak dodatkowego opisu dla tej klasyfikacji."
                )

            tooltip_analiza = tk.Toplevel(tabela_analizy)
            tooltip_analiza.wm_overrideredirect(True)
            tooltip_analiza.geometry(f"+{x_root + 10}+{y_root + 10}")

            tk.Label(
                tooltip_analiza,
                text=pelny_tekst,
                justify="left",
                padx=10,
                pady=8,
                relief="solid",
                wraplength=350,
                borderwidth=1
            ).pack()

        def ukryj_tooltip_analiza(event=None):
            nonlocal tooltip_analiza, tooltip_job

            if tooltip_job is not None:
                tabela_analizy.after_cancel(tooltip_job)
                tooltip_job = None

            if tooltip_analiza is not None:
                tooltip_analiza.destroy()
                tooltip_analiza = None

        tabela_analizy.bind("<Motion>", zaplanuj_tooltip)
        tabela_analizy.bind("<Leave>", ukryj_tooltip_analiza)

        tabela_analizy.bind("<Motion>", zaplanuj_tooltip)
        tabela_analizy.bind("<Leave>", ukryj_tooltip_analiza)

        for _, wiersz in pacjenci_przekroczenie.iterrows():

            tabela_analizy.bind("<Motion>", zaplanuj_tooltip)
            tabela_analizy.bind("<Leave>", ukryj_tooltip_analiza)

        for _, wiersz in pacjenci_przekroczenie.iterrows():
            wynik = analizuj_pacjenta(wiersz)
            tabela_analizy.insert(
                "",
                "end",
                values=(
                    wiersz["patient_id"],
                    wynik["okolica"],
                    f"{wynik['bmi']} ({wynik['kategoria_bmi']})",
                    wynik["kategoria_faz"],
                    f"{wynik['procent_przekroczenia']:+.3f}%",
                    wynik["klasyfikacja"],
                    wynik["aktywne_czynniki"],
                )
            )

        return
    # ==========================================
    # WYKRES
    # ==========================================
    from aggregations import policz_wg_kolumny
    ...
    liczba_badan = policz_wg_kolumny(dane, kolumna, sortuj_wg_indeksu)


# =========================
# PRZYCISKI
# =========================
przyciski = {}

for tekst in rodzaje_wykresow:
    przycisk = tk.Button(
        panel_wyboru,
        text=tekst,
        command=lambda t=tekst: pokaz_wykres(t)
    )
    przycisk.pack(side="left", padx=5)
    przyciski[tekst] = przycisk
pokaz_wykres(rodzaje_wykresow[0])


#przycisk.pack(side="left", padx=5)


# =========================
# URUCHOMIENIE PROGRAMU
# =================

okno.mainloop()
