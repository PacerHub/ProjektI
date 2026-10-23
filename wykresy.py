#Budowa wykresów matplotlib.
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
import textwrap
from matplotlib.patches import Patch
from stale import (
    PALETA_KOLOROW, ROZMIAR_TYTULU_WYKRESU, GRUBOSC_TYTULU_WYKRESU, ROZMIAR_TYTULU_DASHBOARDU,
    BADANIA_BEZ_DPR, KOLOR_BRAK_DPR,
)
from agregacje import policz_kategorie_onkologiczne, policz_wg_grupy_wiekowej

def _kolory_cyklicznie(n):
    return [PALETA_KOLOROW[i % len(PALETA_KOLOROW)] for i in range(n)]

def zawin_etykiety(etykiety, szerokosc=22):
    #Długie nazwy (np. rodzaje badań) łamane na kilka krótszych linii.
    return [textwrap.fill(str(etykieta), szerokosc) for etykieta in etykiety]

def _ustaw_tytul_panelu(ax, tekst):
    ax.set_title(tekst, fontsize=ROZMIAR_TYTULU_WYKRESU, fontweight=GRUBOSC_TYTULU_WYKRESU)

# ==========================================
# POJEDYNCZE PANELE DASHBOARDU "PACJENCI Z PRZEKROCZONĄ DAWKĄ"
# ==========================================

def narysuj_liczbe_faz(ax, pacjenci):
    #Rysuje słupkowy rozkład liczby faz badania.
    counts = pacjenci["liczba_faz"].value_counts().sort_index()
    etykiety = counts.index.astype(str)

    ax.bar(etykiety, counts.values, color=_kolory_cyklicznie(len(counts)))
    _ustaw_tytul_panelu(ax, "Liczba faz badania")
    ax.set_xlabel("Liczba faz")
    ax.set_ylabel("Liczba pacjentów")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

def narysuj_protokol_onkologiczny(ax, pacjenci):
    #Rysuje kołowy rozkład protokołu onkologicznego (tak/nie/nie dotyczy).
    counts = policz_kategorie_onkologiczne(pacjenci["protokol_onkologiczny_jamy_brzusznej"])

    ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.0f%%",
        colors=_kolory_cyklicznie(len(counts)),
        startangle=90,
    )
    _ustaw_tytul_panelu(ax, "Protokół onkologiczny")


def narysuj_rodzaj_badania(ax, pacjenci):
    #Rysuje poziomy słupkowy rozkład rodzajów badania.
    counts = pacjenci["rodzaj_badania_tk"].value_counts().sort_values()

    ax.barh(counts.index, counts.values, color=_kolory_cyklicznie(len(counts)))
    _ustaw_tytul_panelu(ax, "Rodzaj badania")
    ax.set_xlabel("Liczba pacjentów")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.tick_params(axis="y", labelsize=7)


def narysuj_wiek(ax, pacjenci):
    #Rysuje liczbę pacjentów w grupach wiekowych (te same grupy co w widoku wieku).
    counts = policz_wg_grupy_wiekowej(pacjenci)

    ax.bar(counts.index, counts.values, color=PALETA_KOLOROW[0])
    _ustaw_tytul_panelu(ax, "Wiek pacjentów")
    ax.set_xlabel("Grupa wiekowa")
    ax.set_ylabel("Liczba pacjentów")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)



def zbuduj_dashboard_przekroczenia(pacjenci):
    #Składa figurę 2x2 z czterema panelami dla pacjentów z przekroczoną dawką.
    fig, ((ax_fazy, ax_onko), (ax_badanie, ax_wiek)) = plt.subplots(2, 2, figsize=(11.5, 6.2))
    fig.suptitle(
        "Dashboard – pacjenci z przekroczoną dawką",
        fontsize=ROZMIAR_TYTULU_DASHBOARDU,
        fontweight=GRUBOSC_TYTULU_WYKRESU,
    )

    narysuj_liczbe_faz(ax_fazy, pacjenci)
    narysuj_protokol_onkologiczny(ax_onko, pacjenci)
    narysuj_rodzaj_badania(ax_badanie, pacjenci)
    narysuj_wiek(ax_wiek, pacjenci)

    # Stały układ "tight" z miejscem na tytuł u góry (rect) – przeliczany przy zmianie rozmiaru
    fig.set_layout_engine("tight", rect=(0, 0, 1, 0.94))
    return fig
# ==========================================
# PROSTY WYKRES LICZEBNOŚCI (wg badania / wieku / płci)
# ==========================================


def zbuduj_wykres_liczebnosci(counts, tytul, kolory=None, legenda=None):
    #legenda – opcjonalna lista par (kolor, opis) pokazana w prawym górnym rogu.
    fig, ax = plt.subplots(figsize=(10, 6))

    kolory = kolory or _kolory_cyklicznie(len(counts))
    counts.plot(kind="bar", ax=ax, color=kolory)
    _ustaw_tytul_panelu(ax, tytul)
    ax.set_xlabel("")
    ax.set_ylabel("Liczba pacjentów")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    if legenda:
        ax.legend(handles=[Patch(color=kolor, label=opis) for kolor, opis in legenda],
                  loc="upper right")

    ax.set_xticklabels(zawin_etykiety(counts.index), rotation=45, ha="right",
                       rotation_mode="anchor", fontsize=9)
    plt.tight_layout()
    return fig


def kolory_rodzajow_badan(nazwy_badan):
    #Badania z DPR – niebieskie, badania bez DPR w przepisach – szare; zwraca (kolory, legenda).
    kolory = [KOLOR_BRAK_DPR if nazwa in BADANIA_BEZ_DPR else PALETA_KOLOROW[0]
              for nazwa in nazwy_badan]
    legenda = [(PALETA_KOLOROW[0], "badanie z DPR w przepisach"),
               (KOLOR_BRAK_DPR, "brak DPR w przepisach")]
    return kolory, legenda

def zbuduj_wykres_kolowy_liczebnosci(counts, tytul, kolory=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    kolory = kolory or _kolory_cyklicznie(len(counts))
    ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%", colors=kolory, startangle=90)
    _ustaw_tytul_panelu(ax, tytul)
    ax.axis("equal")
    plt.tight_layout()
    return fig

def zbuduj_wykres_pareto(counts, tytul="Pareto przyczyn przekroczeń"):
    #Słupki liczebności klasyfikacji + linia skumulowanego procentu (zasada Pareto)."""
    skumulowany_procent = counts.cumsum() / counts.sum() * 100

    fig, ax1 = plt.subplots(figsize=(11, 6.5))
    kolory = _kolory_cyklicznie(len(counts))

    pozycje = range(len(counts))
    ax1.bar(pozycje, counts.values, color=kolory)
    ax1.set_xticks(pozycje)
    ax1.set_xticklabels(zawin_etykiety(counts.index), rotation=30, ha="right",
                        rotation_mode="anchor")
    ax1.set_ylabel("Liczba pacjentów")
    ax1.set_ylim(0, counts.max() * 1.2)

    for x, y in zip(pozycje, counts.values):
        ax1.text(x, y, str(y), ha="center", va="bottom", fontsize=9)

    ax2 = ax1.twinx()
    ax2.plot(pozycje, skumulowany_procent.values, color="#333333", marker="o", linewidth=1.5)
    ax2.set_ylabel("Skumulowany %")
    ax2.set_ylim(0, 110)

    # linia pomocnicza na 80% - klasyczny próg zasady Pareto (80/20)
    ax2.axhline(80, color="#B56576", linestyle="--", linewidth=1)
    ax2.text(len(counts) - 1, 83, "80%", color="#B56576", ha="right", fontsize=9)

    _ustaw_tytul_panelu(ax1, tytul)
    plt.tight_layout()
    return fig