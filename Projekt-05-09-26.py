import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import ttk


# =========================
# WCZYTANIE DANYCH
# =========================

dane = pd.read_csv("ct_patients_data.csv")

dane["przekroczenie_dlp"] = (
        dane["dlp_zmierzony_na_faze_mGy_cm"]
        > dane["dlp_referencyjny_na_faze_mGy_cm"]
)


dane["przekroczenie_o"] = (
        dane["dlp_zmierzony_na_faze_mGy_cm"]
        - dane["dlp_referencyjny_na_faze_mGy_cm"]
)

# =========================

okno = tk.Tk()

okno.title("Analiza dawek TK")
okno.geometry("1200x800")
okno.minsize(1200, 800)
okno.maxsize(1200, 800)


# =========================
# NAPIS
# =========================

napis = tk.Label(
    okno,
    text="Analiza danych pacjentów TK",
    font=("Arial", 18)
)

napis.pack(pady=30)

# =========================
# PANEL WYBORU
# =========================

panel_wyboru = tk.Frame(okno)
panel_wyboru.pack(pady=10)


rodzaje_wykresow = [
    "Liczba pacjentów wg rodzaju badania",
    "Liczba pacjentów wg wieku",
    "Liczba pacjentów wg płci",
    "Pacjenci z przekroczoną dawką"
]

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
        styl.configure("Treeview.Heading", padding=(5, 15))

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
        # TOOLTIP DLA DLP
        # ==========================================

        tooltip = None

        def pokaz_tooltip(event):

            nonlocal tooltip

            region = tabela.identify_region(
                event.x,
                event.y
            )

            # Jeżeli nie jesteśmy nad nagłówkiem,
            # nic nie robimy
            if region != "heading":

                if tooltip is not None:
                    tooltip.destroy()
                    tooltip = None

                return

            kolumna = tabela.identify_column(event.x)

            # Tooltip tylko dla kolumn DLP
            if kolumna not in ("#6","#7","#9"):

                if tooltip is not None:
                    tooltip.destroy()
                    tooltip = None

                return

            # Jeżeli tooltip już istnieje,
            # nie tworzymy kolejnego
            if tooltip is not None:
                return

            tooltip = tk.Toplevel(tabela)

            tooltip.wm_overrideredirect(True)

            tooltip.geometry(
                f"+{event.x_root + 10}+"
                f"{event.y_root + 10}"
            )

            if kolumna == "#6":
                tresc_tootltipa = ("DPR – Diagnostyczny Poziom Referencyjny.\n"
                "Punkt odniesienia dla typowego pacjenta,\n"
                "nie sztywny limit prawny. Może być\n"
                "przekroczony przy uzasadnieniu klinicznym.")
            elif kolumna == "#7":
                tresc_tootltipa = ("DLP – iloczyn dawka-długość.\n"
                "Rzeczywista wartość zmierzona\n"
                "u pacjenta dla pojedynczej fazy\n"
                "badania — porównywana z DPR.")
            elif kolumna == "#9":
                tresc_tootltipa = ("Suma DLP z wszystkich\n"
                "faz badania (informacyjnie).\n")
            napis = tk.Label(
                tooltip,
                text=tresc_tootltipa,
                justify="left",
                padx=10,
                pady=8,
                relief="solid",
                wraplength=250,
                borderwidth=1
            )

            napis.pack()

        def ukryj_tooltip(event):

            nonlocal tooltip

            if tooltip is not None:
                tooltip.destroy()
                tooltip = None

        tabela.bind(
            "<Motion>",
            pokaz_tooltip
        )

        tabela.bind(
            "<Leave>",
            ukryj_tooltip
        )

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
    # WYKRES
    # ==========================================

    if wybrany_wykres == "Liczba pacjentów wg rodzaju badania":

        liczba_badan = dane[
            "rodzaj_badania_tk"
        ].value_counts()

    elif wybrany_wykres == "Liczba pacjentów wg wieku":

        liczba_badan = dane[
            "wiek"
        ].value_counts().sort_index()

    elif wybrany_wykres == "Liczba pacjentów wg płci":

        liczba_badan = dane[
            "plec"
        ].value_counts().sort_index()

    print("Wybrano:", wybrany_wykres)

    # Tworzymy wykres
    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    liczba_badan.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title(
        wybrany_wykres
    )

    ax.set_xlabel(
        wybrany_wykres
    )

    ax.set_yticks(
        range(
            0,
            liczba_badan.max() + 1
        )
    )

    ax.set_ylabel(
        "Liczba pacjentów"
    )

    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right",
    )

    plt.tight_layout()

    # Umieszczenie wykresu w Tkinterze
    canvas = FigureCanvasTkAgg(
        fig,
        master=miejsce_na_wykres
    )

    canvas.draw()

    canvas.get_tk_widget().pack(
        fill="both",
        expand=True
    )



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
