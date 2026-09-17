"""Budowa wykresów matplotlib."""

import matplotlib.pyplot as plt
from constants import PALETA_KOLOROW, ROZMIAR_TYTULU_WYKRESU, GRUBOSC_TYTULU_WYKRESU

def _kolory_cyklicznie(n):
    return [PALETA_KOLOROW[i % len(PALETA_KOLOROW)] for i in range(n)]


def _ustaw_tytul_panelu(ax, tekst):
    ax.set_title(tekst, fontsize=ROZMIAR_TYTULU_WYKRESU, fontweight=GRUBOSC_TYTULU_WYKRESU)

def zbuduj_wykres_liczebnosci(counts, tytul, kolory=None):
    """Buduje pojedynczy wykres słupkowy liczebności z gotowej serii `counts`."""
    kolory = kolory or _kolory_cyklicznie(len(counts))
    counts.plot(kind="bar", ax=ax, color = kolory)
    _ustaw_tytul_panelu(ax, tytul)
    ax.set_xlabel(tytul)
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