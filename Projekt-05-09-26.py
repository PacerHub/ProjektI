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
    "Pacjenci z przekroczoną dawką",
    "Analiza przyczyn przekroczeń"
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
# MAPOWANIE BADAŃ NA OKOLICĘ ANATOMICZNĄ
# =========================
EXAM_REGION = {
    "Rutynowe badanie głowy lub mózgu": "głowa",
    "Badanie twarzy i zatok": "głowa",
    "Angio-TK głowy": "głowa",
    "Rutynowe badanie klatki piersiowej": "klatka piersiowa",
    "TK klatki piersiowej, wysoka rozdzielczość": "klatka piersiowa",
    "Angio-TK serca i naczyń klatki piersiowej": "klatka piersiowa",
    "Angio-TK aorty piersiowej": "klatka piersiowa",
    "Rutynowe badanie brzucha lub jamy brzusznej": "jama brzuszna",
    "Badanie wątroby i śledziony": "jama brzuszna",
    "Angio-TK jamy brzusznej i miednicy mniejszej": "jama brzuszna / miednica",
    "Rutynowe badanie miednicy lub narządów miednicy": "miednica",
    "Badanie kości miednicy lub obręczy biodrowej": "miednica",
    "TK kręgosłupa szyjnego": "kręgosłup",
    "TK odcinka piersiowego kręgosłupa": "kręgosłup",
    "TK odcinka lędźwiowo-krzyżowego kręgosłupa": "kręgosłup",
    "TK szyi, tkanki miękkie": "szyja",
    "Angio-TK tętnic szyjnych": "szyja",
}

PROG_WYSOKIEGO_DLP_FAZY = 1.20  # 20% powyżej wartości referencyjnej


def kategoria_liczby_faz(n):
    if n == 1:
        return "1 faza"
    elif n == 2:
        return "2 fazy"
    else:
        return f"więcej faz ({n})"

def kategoria_bmi(wiek, bmi):
    if wiek < 16:
        return "nie dotyczy (pacjent pediatryczny)"
    elif bmi < 18.5:
        return "niedowaga"
    elif bmi < 25:
        return "waga prawidłowa"
    elif bmi < 30:
        return "nadwaga"
    else:
        return "otyłość"


def klasyfikuj_przyczyne(factors):
    label_map = {
        "pediatryczny": "pacjent <16 lat",
        "onkologiczny": "protokół onkologiczny",
        "wielofazowy": "wielofazowe badanie",
        "wysoki_dlp_fazy": "wysokie DLP pojedynczej fazy",
        "nadwaga_otylosc": "nadwaga/otyłość pacjenta",
    }
    active = [name for name, is_active in factors.items() if is_active]

    if len(active) == 0:
        return "przekroczenie wymagające indywidualnej analizy", []
    elif len(active) == 1:
        return label_map[active[0]], [label_map[active[0]]]
    else:
        return "połączenie kilku czynników", [label_map[a] for a in active]


def analizuj_pacjenta(wiersz):
    wiek = wiersz["wiek"]
    jest_pediatryczny = bool(wiek < 16)

    rodzaj_badania = wiersz["rodzaj_badania_tk"]
    okolica = EXAM_REGION.get(rodzaj_badania, "nieznana")

    liczba_faz = int(wiersz["liczba_faz"])
    jest_wielofazowy = liczba_faz >= 2

    protokol_onko_raw = wiersz["protokol_onkologiczny_jamy_brzusznej"]
    jest_onkologiczny = bool(protokol_onko_raw is True or protokol_onko_raw == True)

    dlp_ref = float(wiersz["dlp_referencyjny_na_faze_mGy_cm"])
    dlp_faza = float(wiersz["dlp_zmierzony_na_faze_mGy_cm"])
    ratio_na_faze = dlp_faza / dlp_ref
    procent_przekroczenia = round((ratio_na_faze - 1) * 100, 3)


    wysokie_dlp_pojedynczej_fazy = ratio_na_faze >= PROG_WYSOKIEGO_DLP_FAZY

    bmi = float(wiersz["bmi"])
    kat_bmi = kategoria_bmi(wiek, bmi)
    ma_nadwage_lub_otylosc = bool((not jest_pediatryczny) and bmi >= 25)

    factors = {
        "pediatryczny": jest_pediatryczny,
        "onkologiczny": jest_onkologiczny,
        "wielofazowy": jest_wielofazowy,
        "wysoki_dlp_fazy": wysokie_dlp_pojedynczej_fazy,
        "nadwaga_otylosc": ma_nadwage_lub_otylosc,
    }
    klasyfikacja, aktywne_czynniki = klasyfikuj_przyczyne(factors)

    return {
        "okolica": okolica,
        "kategoria_faz": kategoria_liczby_faz(liczba_faz),
        "bmi": round(bmi, 1),
        "kategoria_bmi": kat_bmi,
        "procent_przekroczenia": procent_przekroczenia,
        "klasyfikacja": klasyfikacja,
        "aktywne_czynniki": ", ".join(aktywne_czynniki) if aktywne_czynniki else "brak",
    }
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
        # TOOLTIP DLA DPR i DLP
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
                tresc_tooltipa = ("DPR – Diagnostyczny Poziom Referencyjny.\n"
                "Punkt odniesienia dla typowego pacjenta,\n"
                "nie sztywny limit prawny. Może być\n"
                "przekroczony przy uzasadnieniu klinicznym.")
            elif kolumna == "#7":
                tresc_tooltipa = ("DLP – iloczyn dawka-długość.\n"
                "Rzeczywista wartość zmierzona\n"
                "u pacjenta dla pojedynczej fazy\n"
                "badania — porównywana z DPR.")
            elif kolumna == "#9":
                tresc_tooltipa = ("Suma DLP z wszystkich\n"
                "faz badania (informacyjnie).")
            napis = tk.Label(
                tooltip,
                text=tresc_tooltipa,
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

        KLASYFIKACJA_OPISY = {
            "pacjent <16 lat": (
                "Główną przyczyną przekroczenia jest wiek\n"
                "pacjenta (<16 lat) - wymaga odrębnego\n"
                "podejścia i referencji pediatrycznych."
            ),
            "protokół onkologiczny": (
                "Przekroczenie wynika z charakteru\n"
                "protokołu onkologicznego (wielofazowe\n"
                "skanowanie: natywna/tętnicza/żylna)."
            ),
            "wielofazowe badanie": (
                "Przekroczenie wiąże się z liczbą\n"
                "wykonanych faz (2 lub więcej) -\n"
                "sumaryczna dawka pacjenta rośnie."
            ),
            "wysokie DLP pojedynczej fazy": (
                "Nawet pojedyncza faza ma dawkę\n"
                "wyraźnie (≥20%) powyżej DPR -\n"
                "warto zweryfikować parametry ekspozycji."
            ),
            "nadwaga/otyłość pacjenta": (
                "Podwyższona dawka może wynikać\n"
                "z wyższego BMI pacjenta (aparat\n"
                "zwiększa ekspozycję dla jakości obrazu)."
            ),
            "połączenie kilku czynników": (
                "Kilka czynników nakłada się jednocześnie -\n"
                "zobacz kolumnę 'Aktywne czynniki',\n"
                "żeby zobaczyć które dokładnie."
            ),
            "przekroczenie wymagające indywidualnej analizy": (
                "Żaden ze znanych czynników (wiek, protokół,\n"
                "liczba faz, wysokie DLP, BMI) nie tłumaczy\n"
                "tego przekroczenia - może to być zwykły\n"
                "szum pomiarowy/losowy, błąd protokołu\n"
                "lub coś, co wymaga ręcznej weryfikacji."
            ),
        }

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
