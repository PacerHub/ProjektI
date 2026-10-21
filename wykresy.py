#Budowa wykresów matplotlib.
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
from stale import PALETA_KOLOROW, ROZMIAR_TYTULU_WYKRESU, GRUBOSC_TYTULU_WYKRESU, ROZMIAR_TYTULU_DASHBOARDU
from agregacje import policz_kategorie_onkologiczne

def _kolory_cyklicznie(n):
    return [PALETA_KOLOROW[i % len(PALETA_KOLOROW)] for i in range(n)]


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
    #Rysuje histogram wieku pacjentów z binami wyrównanymi do pełnych lat.
    wiek_min = int(pacjenci["wiek"].min())
    wiek_max = int(pacjenci["wiek"].max())

    ax.hist(pacjenci["wiek"], bins=range(wiek_min - 1, wiek_max + 2),
            color=PALETA_KOLOROW[0], edgecolor="white")
    _ustaw_tytul_panelu(ax, "Wiek pacjentów")
    ax.set_xlabel("Wiek")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylabel("Liczba pacjentów")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))



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

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    return fig
# ==========================================
# PROSTY WYKRES LICZEBNOŚCI (wg badania / wieku / płci)
# ==========================================


def zbuduj_wykres_liczebnosci(counts, tytul, kolory=None):
    fig, ax = plt.subplots(figsize=(10, 6))

    kolory = kolory or _kolory_cyklicznie(len(counts))
    counts.plot(kind="bar", ax=ax, color = kolory)
    _ustaw_tytul_panelu(ax, tytul)
    ax.set_xlabel("")
    ax.set_ylabel("Liczba pacjentów")
    ax.set_yticks(range(0, counts.max() + 1))

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    return fig

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
    ax1.set_xticklabels(counts.index, rotation=30, ha="right")
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