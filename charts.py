"""Budowa wykresów matplotlib."""

import matplotlib.pyplot as plt


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