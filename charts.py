"""Budowa wykresów matplotlib."""

import matplotlib.pyplot as plt
from constants import PALETA_KOLOROW, ROZMIAR_TYTULU_WYKRESU, GRUBOSC_TYTULU_WYKRESU


def zbuduj_wykres_liczebnosci(counts, tytul, kolory=None):
    """Buduje pojedynczy wykres słupkowy liczebności z gotowej serii `counts`."""
    fig, ax = plt.subplots(figsize=(10, 6))
    counts.plot(kind="bar", ax=ax)
    ax.set_title(tytul)
    ax.set_xlabel(tytul)
    ax.set_ylabel("Liczba pacjentów")
    ax.set_yticks(range(0, counts.max() + 1))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.tight_layout()
    return fig

def _kolory_cyklicznie(n):
    return [PALETA_KOLOROW[i % len(PALETA_KOLOROW)] for i in range(n)]


def _ustaw_tytul_panelu(ax, tekst):
    ax.set_title(tekst, fontsize=ROZMIAR_TYTULU_WYKRESU, fontweight=GRUBOSC_TYTULU_WYKRESU)