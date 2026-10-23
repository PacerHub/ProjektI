#Stałe konfiguracyjne aplikacji: mapowania, progi, etykiety i teksty opisowe.

SCIEZKA_DANYCH = "ct_patients_data.csv"

# Mapowanie rodzaju badania TK na okolicę anatomiczną
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
    "TK jamy brzusznej i miednicy": "jama brzuszna / miednica",
}

# 20% powyżej wartości referencyjnej DLP na fazę uznajemy za "wysokie"
PROG_WYSOKIEGO_DLP_FAZY = 1.20

# Nazwy widoków wybieranych przyciskami, w kolejności wyświetlania
RODZAJE_WIDOKOW = [
    "Liczba pacjentów wg rodzaju badania",
    "Liczba pacjentów wg wieku",
    "Liczba pacjentów wg płci",
    "Pacjenci z przekroczoną dawką",
    "Analiza przyczyn przekroczeń",
    "Pareto przyczyn przekroczeń",
]
# Etykiety klasyfikacji przyczyny -> opis pokazywany w tooltipie
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

ROZMIAR_TYTULU_WYKRESU = 13
ROZMIAR_TYTULU_DASHBOARDU = 15
GRUBOSC_TYTULU_WYKRESU = "bold"

PALETA_KOLOROW = [
    "#355070",
    "#6D597A",
    "#B56576",
    "#E56B6F",
    "#EAAC8B",
]

CZCIONKA = "Book Antiqua"

WIDOKI_LICZEBNOSCI = {
    "Liczba pacjentów wg rodzaju badania": {
        "kolumna": "rodzaj_badania_tk", "sortuj_wg_indeksu": False, "typ_wykresu": "slupkowy", "kolory": None
    },
    "Liczba pacjentów wg płci": {
        "kolumna": "plec", "sortuj_wg_indeksu": True, "typ_wykresu": "kolowy",
        "kolory": [PALETA_KOLOROW[0], PALETA_KOLOROW[2]],
    },
}
GRANICE_WIEKU = [15, 17, 25, 35, 45, 55, 65, 75]

ETYKIETY_GRUP_WIEKOWYCH = [
    "<16 lat", "16-17", "18-25", "26-35", "36-45", "46-55", "56-65", "66-75", "powyżej 75 lat",
]

KLUCZE_CZYNNIKOW = ["pediatryczny", "onkologiczny", "wielofazowy", "wysoki_dlp_fazy", "nadwaga_otylosc"]

ETYKIETY_CZYNNIKOW = {
    "pediatryczny": "Pacjent\n<16 lat",
    "onkologiczny": "Protokół\nonkologiczny",
    "wielofazowy": "Wielofazowe\nbadanie",
    "wysoki_dlp_fazy": "Wysokie DLP\nfazy",
    "nadwaga_otylosc": "Nadwaga / otyłość",
}

# Granice wartości - używane do wykrywania błędnych/podejrzanych rekordów
ZAKRES_WIEKU = (0, 110)
ZAKRES_BMI = (10, 70)
ZAKRES_LICZBY_FAZ = (1, 6)

KOLOR_NAGLOWKA = "#1f4e79"          # ciemnoniebieski – belka z tytułem aplikacji
KOLOR_TEKSTU_NAGLOWKA = "white"
KOLOR_NAGLOWKOW_TABELI = "#2e75b6"  # niebieski – tytuły kolumn tabeli
KOLOR_NAGLOWKOW_TABELI_HOVER = "#255f94"
KOLOR_TEKSTU_NAGLOWKOW_TABELI = "white"
# Panel wniosków (Pareto, analiza przyczyn)
KOLOR_TLA_WNIOSKOW = "#eaf2fa"      # jasnoniebieskie tło panelu
KOLOR_AKCENTU_WNIOSKOW = "#1f4e79"  # pasek z lewej strony i tytuł "Wnioski"
KOLOR_TEKSTU_WNIOSKOW = "#1a1a1a"


WIDOKI_LICZBA_PACJENTOW = [
    # (tekst w menu, pełna nazwa widoku z RODZAJE_WIDOKOW)
    ("rodzaju badania", "Liczba pacjentów wg rodzaju badania"),
    ("wieku", "Liczba pacjentów wg wieku"),
    ("płci", "Liczba pacjentów wg płci"),
]

KATEGORIE_BMI = ["niedowaga", "waga prawidłowa", "nadwaga", "otyłość I stopnia", "otyłość II stopnia"]
# Widok "Filtr przyczyn przekroczeń"
WARTOSC_WSZYSTKIE = "wszystkie"           # pozycja "bez filtra" w listach rozwijanych
KLUCZ_BRAK_CZYNNIKA = "brak"              # pacjenci bez żadnego znanego czynnika
ETYKIETA_BRAKU_CZYNNIKA = "Brak znanego czynnika"

KOLUMNY_TABELI_PRZYCZYN = [
    # (klucz, nagłówek, szerokość, wyrównanie) – kolejność = kolejność kolumn w tabeli
    ("pacjent", "Pacjent", 70, "center"),
    ("wiek", "Wiek", 50, "center"),
    ("plec", "Płeć", 45, "center"),
    ("okolica", "Okolica anatomiczna", 130, "w"),
    ("bmi", "BMI (kategoria)", 150, "center"),
    ("kategoria_faz", "Liczba faz", 80, "center"),
    ("procent", "% przekroczenia", 105, "center"),
    ("klasyfikacja", "Klasyfikacja przyczyny", 200, "w"),
    ("czynniki", "Aktywne czynniki", 220, "w"),
    ("pediatryczny", "<16 lat", 70, "center"),
    ("onkologiczny", "Onko", 70, "center"),
    ("wielofazowy", "Wielofazowe", 85, "center"),
    ("wysoki_dlp_fazy", "Wysokie DLP", 85, "center"),
    ("nadwaga_otylosc", "Nadwaga/\notyłość", 80, "center"),
]

# Źródło diagnostycznych poziomów referencyjnych (DPR) – wartości referencyjne w pliku CSV
ZRODLO_DPR = (
    "Rozporządzenie Ministra Zdrowia z dnia 6 grudnia 2022 r. w sprawie diagnostycznych "
    "poziomów referencyjnych (Dz.U. 2022 poz. 2626), załącznik nr 1, tabela 3 – wydane "
    "na podstawie art. 33g ust. 3 ustawy z dnia 29 listopada 2000 r. – Prawo atomowe"
)
ZRODLO_DPR_KROTKO = (
    "Rozporządzenie MZ z 6.12.2022 r. w sprawie DPR (Dz.U. 2022 poz. 2626), "
    "wyd. na podst. art. 33g ust. 3 ustawy – Prawo atomowe"
)

# Badania wykonywane w praktyce, dla których rozporządzenie NIE określa DPR.
# Brak DPR nie jest dla nich błędem danych – nie da się tylko ocenić przekroczenia.
BADANIA_BEZ_DPR = ["TK jamy brzusznej i miednicy"]
KOLOR_BRAK_DPR = "#9e9e9e"  # szary – wyróżnienie tych badań na wykresie