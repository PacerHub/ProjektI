# Specyfikacja aplikacji „Analiza dawek TK”


## 1. Cel aplikacji

Aplikacja wspiera analizę dawek promieniowania w badaniach tomografii komputerowej. Dla każdego pacjenta porównuje zmierzoną wartość DLP na fazę z diagnostycznym poziomem referencyjnym (DPR), wykrywa przekroczenia, przypisuje im prawdopodobną przyczynę i prezentuje wyniki w formie wykresów, tabel oraz automatycznych wniosków tekstowych.

**Użytkownik docelowy:** fizyk medyczny, inspektor ochrony radiologicznej, technik elektroradiologii lub student analizujący dane dozymetryczne z pracowni TK.

---

## 2. Dane wejściowe

Plik CSV (domyślnie `ct_patients_data.csv`, ścieżka w `stale.py` → `SCIEZKA_DANYCH`), jeden wiersz = jedno badanie pacjenta.

| Kolumna | Typ | Opis |
|---|---|---|
| `patient_id` | liczba całkowita | identyfikator pacjenta |
| `wiek` | liczba | wiek w latach |
| `plec` | `K` / `M` | płeć |
| `bmi` | liczba | wskaźnik masy ciała |
| `rodzaj_badania_tk` | tekst | nazwa badania, np. „Rutynowe badanie głowy lub mózgu” |
| `protokol_onkologiczny_jamy_brzusznej` | `True` / `False` / puste | dotyczy tylko badań jamy brzusznej |
| `liczba_faz` | liczba całkowita | liczba faz skanowania |
| `ctdiw_referencyjny_mGy`, `ctdiw_zmierzony_mGy` | liczba | CTDIw referencyjny i zmierzony |
| `dlp_referencyjny_na_faze_mGy_cm` | liczba | DPR – referencyjne DLP na fazę |
| `dlp_zmierzony_na_faze_mGy_cm` | liczba | zmierzone DLP na fazę |
| `dlp_zmierzony_lacznie_mGy_cm` | liczba | zmierzone DLP łącznie (wszystkie fazy) |

Rodzaj badania jest mapowany na okolicę anatomiczną (głowa, szyja, klatka piersiowa, jama brzuszna, jama brzuszna / miednica, miednica, kręgosłup) – słownik `EXAM_REGION` w `stale.py`.

### 2.1. Źródło wartości referencyjnych

Wartości `ctdiw_referencyjny_mGy` i `dlp_referencyjny_na_faze_mGy_cm` pochodzą z **Rozporządzenia Ministra Zdrowia z dnia 6 grudnia 2022 r. w sprawie diagnostycznych poziomów referencyjnych** (Dz.U. 2022 poz. 2626, załącznik nr 1, tabela 3), wydanego na podstawie **art. 33g ust. 3 ustawy z dnia 29 listopada 2000 r. – Prawo atomowe**.

- Wartości dotyczą standardowego pacjenta dorosłego (170 cm, 70 kg).
- DLP podawane jest dla jednej fazy badania – dlatego aplikacja porównuje DLP na fazę, a nie DLP łączne.
- Rozporządzenie nie określa DPR dla badań TK u dzieci ani dla łączonego badania jamy brzusznej i miednicy (poza angio-TK).

Pełny opis źródła jest zapisany w stałej `ZRODLO_DPR` (`stale.py`), a jego skrócona wersja (`ZRODLO_DPR_KROTKO`) jest wyświetlana w stopce okna aplikacji.

### 2.2. Badania bez DPR w przepisach

Stała `BADANIA_BEZ_DPR` zawiera badania wykonywane w praktyce, dla których rozporządzenie nie określa wartości referencyjnych – obecnie **„TK jamy brzusznej i miednicy”** (również w protokole onkologicznym). W danych mają puste kolumny z wartościami referencyjnymi. Aplikacja:

- **nie** oznacza ich jako błędnych (brak DPR to luka w przepisach, a nie w danych),
- uwzględnia je w liczebności pacjentów (widać, że takie badania są wykonywane),
- **nie** uwzględnia ich w analizie przekroczeń (nie ma z czym porównać zmierzonej dawki),
- wyróżnia je na wykresie rodzajów badań i opisuje w panelu wniosków.

### 2.3. Pojęcia

| Pojęcie | Definicja |
|---|---|
| **DLP** (*Dose Length Product*, iloczyn dawki i długości) [mGy·cm] | CTDIvol pomnożony przez długość skanowanego obszaru; opisuje całkowitą ekspozycję w jednej fazie badania |
| **CTDIw** (ważony indeks dawki TK) [mGy] | średnia z pomiarów w fantomie z wagą 1/3 dla środka i 2/3 dla obwodu; dawka na jeden obrót lampy |
| **DPR** (diagnostyczny poziom referencyjny) | poziom dawki dla typowych badań u pacjentów o standardowych wymiarach (170 cm, 70 kg); nie jest limitem dawki – regularne przekraczanie DPR powinno skłonić do przeglądu procedury |

Definicje DLP i DPR są dostępne w aplikacji jako tooltipy na nagłówkach kolumn tabeli analizy przyczyn (punkt 4.5).

---

## 3. Przetwarzanie danych

### 3.1. Walidacja

Po wczytaniu każdy wiersz jest sprawdzany (`oznacz_podejrzane_dane`). Wiersz jest oznaczany jako **podejrzany**, jeśli:

- brakuje wartości w kolumnach: `wiek`, `bmi`, `liczba_faz`, `dlp_referencyjny_na_faze_mGy_cm`, `dlp_zmierzony_na_faze_mGy_cm`,
- wiek jest poza zakresem 0–110 lat,
- BMI jest poza zakresem 10–70,
- liczba faz jest poza zakresem 1–6,
- DPR ≤ 0 lub zmierzone DLP < 0.

Wyjątek: dla badań z listy `BADANIA_BEZ_DPR` brak DPR nie jest powodem podejrzenia (punkt 2.2).

Podejrzane wiersze **nie są usuwane**. Dostają kolumny `podejrzany_wiersz = True` i `powod_podejrzenia` (lista powodów). Wykresy zbiorcze je pomijają, a tabela analizy przyczyn pokazuje je z oznaczeniem ⚠ i żółtym tłem.

### 3.2. Wykrywanie przekroczenia

```
przekroczenie = DLP zmierzone na fazę > DPR na fazę
% przekroczenia = (DLP zmierzone / DPR − 1) × 100
```

### 3.3. Czynniki przekroczenia

Dla każdego pacjenta z przekroczeniem wyznaczanych jest 5 czynników (prawda/fałsz):

| Czynnik | Warunek |
|---|---|
| Pacjent <16 lat | wiek < 16 |
| Protokół onkologiczny | `protokol_onkologiczny_jamy_brzusznej` = True |
| Wielofazowe badanie | liczba faz ≥ 2 |
| Wysokie DLP fazy | DLP zmierzone ≥ 120% DPR (`PROG_WYSOKIEGO_DLP_FAZY = 1.20`) |
| Nadwaga / otyłość | BMI ≥ 25 i pacjent nie jest pediatryczny |

### 3.4. Klasyfikacja przyczyny

| Liczba aktywnych czynników | Klasyfikacja |
|---|---|
| 0 | „przekroczenie wymagające indywidualnej analizy” |
| 1 | nazwa tego czynnika, np. „nadwaga/otyłość pacjenta” |
| 2 lub więcej | „połączenie kilku czynników” |

### 3.5. Kategorie pomocnicze

- **Kategoria BMI** (dorośli): niedowaga < 18,5; waga prawidłowa < 25; nadwaga < 30; otyłość I stopnia < 35; otyłość II stopnia ≥ 35. Dla pacjentów < 16 lat: „nie dotyczy (pacjent pediatryczny)”.
- **Grupy wiekowe:** <16 lat, 16-17, 18-25, 26-35, 36-45, 46-55, 56-65, 66-75, powyżej 75 lat (granice w `GRANICE_WIEKU`).
- **Liczba faz:** „1 faza”, „2 fazy”, „więcej faz (n)”.

---

## 4. Interfejs użytkownika

### 4.1. Okno główne

- Tytuł okna: „Analiza dawek TK”.
- Rozmiar startowy do 1400 × 850 px, dopasowany do obszaru roboczego ekranu (bez paska zadań), okno wyśrodkowane. Minimalny rozmiar 1100 × 700 px, okno można powiększać i maksymalizować.
- Na Windows włączona obsługa skalowania ekranu (ostre czcionki i wykresy przy 125%/150%).

Układ od góry:

1. **Belka tytułowa** – ciemnoniebieski pasek z napisem „Analiza danych pacjentów TK”.
2. **Pasek przycisków** – przełączanie widoków. Aktywny widok ma wciśnięty przycisk.
3. **Obszar widoku** – zawartość wybranego widoku, wymieniana po każdym kliknięciu.
4. **Stopka** – szary napis ze źródłem wartości referencyjnych (`ZRODLO_DPR_KROTKO`), widoczny we wszystkich widokach.

### 4.2. Pasek przycisków

| Przycisk | Działanie |
|---|---|
| **Liczba pacjentów wg ▾** | rozwija menu: *rodzaju badania*, *wieku*, *płci*. Po wyborze przycisk pokazuje bieżący wybór, np. „Liczba pacjentów wg płci ▾” |
| **Pacjenci z przekroczoną dawką** | dashboard 2×2 z filtrami |
| **Analiza przyczyn przekroczeń** | karty, wnioski, filtry i tabela pacjentów |
| **Pareto przyczyn przekroczeń** | wykres Pareto z wnioskami |

Po uruchomieniu otwiera się widok „Liczba pacjentów wg rodzaju badania”.

### 4.3. Widoki liczebności

Dane: wszyscy pacjenci bez wierszy podejrzanych.

- **wg rodzaju badania** – wykres słupkowy, kategorie posortowane malejąco, etykiety osi X obrócone o 45°. Badania z DPR mają kolor niebieski, badania bez DPR w przepisach – szary; legenda w prawym górnym rogu. Pod wykresem panel wniosków, np. „13 z 150 badań (9%) to 'TK jamy brzusznej i miednicy' (w tym 11 w protokole onkologicznym) – badanie wykonywane w praktyce, dla którego przepisy nie określają diagnostycznego poziomu referencyjnego (DPR)…”. Udział liczony jest względem wszystkich wykonanych badań (także tych z błędnie wprowadzonymi danymi), bo badania zostały fizycznie wykonane – błąd dotyczy tylko zapisu danych.
- **wg wieku** – wykres słupkowy z 9 grupami wiekowymi w stałej kolejności (puste grupy pokazane jako 0).
- **wg płci** – wykres kołowy z udziałem procentowym kobiet i mężczyzn.

### 4.4. Pacjenci z przekroczoną dawką (dashboard)

Dane: pacjenci z przekroczeniem, bez wierszy podejrzanych.

**Filtry** (przełączniki radiowe nad wykresami):
- *Płeć:* Wszyscy / Kobiety / Mężczyźni,
- *Kategoria BMI:* Wszyscy / niedowaga / waga prawidłowa / nadwaga / otyłość I stopnia / otyłość II stopnia.

Zmiana filtra natychmiast przebudowuje wszystkie 4 panele. Układ wykresów jest przeliczany przy każdej zmianie rozmiaru okna, a długie etykiety (np. rodzaje badań) są zawijane do kilku linii, żeby nie były ucinane. Jeśli po filtrowaniu nie ma pacjentów, zamiast wykresów pojawia się komunikat „Brak pacjentów z przekroczoną dawką dla wybranych filtrów.”

**Panele:**

| Panel | Wykres |
|---|---|
| Liczba faz badania | słupkowy, oś Y w liczbach całkowitych |
| Protokół onkologiczny | kołowy: tak / nie / nie dotyczy; procenty wewnątrz wycinków (dla wycinków < 8% tylko w legendzie), legenda z boku z liczbą i udziałem %, np. „nie dotyczy – 15 (83%)” |
| Rodzaj badania | poziomy słupkowy |
| Wiek pacjentów | słupkowy wg grup wiekowych |

### 4.5. Analiza przyczyn przekroczeń

Dane: pacjenci z przekroczeniem oraz wiersze podejrzane.

Układ od góry:

1. **Karty czynników** – 5 kart w poziomym pasku, każda z liczbą „aktywni / wszyscy” i nazwą czynnika.
2. **Panel wniosków** – ramka z jasnoniebieskim tłem, paskiem akcentu i tytułem „Wnioski”. Tekst generowany automatycznie: najczęstszy czynnik (liczba i %), okolica z największą liczbą przekroczeń, średni % przekroczenia. Tekst zawija się do szerokości okna.
3. **Panel filtrów:**
   - *Przyczyny* – pola wyboru: 5 czynników + „Brak znanego czynnika”. Pokazywani są pacjenci, u których występuje **którykolwiek** z zaznaczonych czynników. Domyślnie wszystkie zaznaczone.
   - *Okolica* – lista rozwijana: „wszystkie” + okolice występujące w danych.
   - *Grupa wiekowa* – lista rozwijana: „wszystkie” + 9 grup.
   - *Min. % przekroczenia* – pole liczbowe (0–200, krok 5). Puste lub błędne pole traktowane jest jak 0.
   - *Pokaż wiersze do weryfikacji (⚠)* – pole wyboru. Wiersze podejrzane nie podlegają pozostałym filtrom (nie mają wiarygodnych danych).
   - *Wyczyść filtry* – przywraca ustawienia domyślne.
4. **Licznik wyników** – np. „Wyniki: 6 z 15 pacjentów z przekroczeniem (+ 2 ⚠ do weryfikacji)”.
5. **Tabela pacjentów** (Treeview z paskami przewijania) – posortowana malejąco po % przekroczenia, wiersze podejrzane na końcu z żółtym tłem i znakiem ⚠ przy numerze pacjenta.

W wierszach podejrzanych wyświetlane są wszystkie dane, które da się wiarygodnie wyliczyć (okolica, liczba faz, BMI, DPR, DLP, % przekroczenia), a „—” tylko w miejscu brakującej lub błędnej wartości. Kategoria BMI jest podawana tylko przy poprawnym wieku i BMI („poza zakresem” przy BMI spoza 10–70), a % przekroczenia tylko przy DPR > 0 i DLP ≥ 0. Wiersze te nie dostają klasyfikacji przyczyny ani czynników ✓.

| Kolumna | Zawartość |
|---|---|
| Pacjent | `patient_id` (⚠ dla wierszy podejrzanych) |
| Wiek, Płeć | dane pacjenta |
| Okolica anatomiczna | z mapowania rodzaju badania |
| BMI (kategoria) | np. „27.6 (nadwaga)” |
| Liczba faz | „1 faza” / „2 fazy” / „więcej faz (n)” |
| DPR na fazę [mGy·cm] | wartość referencyjna DLP dla jednej fazy |
| DLP zmierzone na fazę [mGy·cm] | zmierzone DLP jednej fazy |
| % przekroczenia | np. „+53.9%” |
| Klasyfikacja przyczyny | wg punktu 3.4; dla wierszy podejrzanych – powód podejrzenia |
| Aktywne czynniki | lista czynników tekstem |
| <16 lat, Onkologiczny, Wielofazowe, Wysokie DLP, Nadwaga/otyłość | ✓ gdy czynnik występuje |

**Tooltipy w tabeli:**
- kolumna *Klasyfikacja przyczyny* – po najechaniu dymek z pełną nazwą klasyfikacji i jej opisem (`KLASYFIKACJA_OPISY`),
- kolumna *Klasyfikacja przyczyny* w wierszach ⚠ – wyjaśnienie, że dane są niepełne lub błędne i nie są uwzględniane w statystykach,
- nagłówki *DPR na fazę* i *DLP zmierzone na fazę* – definicje DPR (ze źródłem) i DLP; nagłówek *Onkologiczny* – pełna nazwa czynnika „Protokół onkologiczny”; nagłówki *% przekroczenia*, *Liczba faz* i *Wysokie DLP* – wzór na % przekroczenia, wyjaśnienie, dlaczego porównywane jest DLP jednej fazy, i próg wysokiego DLP fazy (`OPISY_NAGLOWKOW_PRZYCZYN` w `stale.py`),
- pozostałe komórki i nagłówki – dymek z pełną treścią, **tylko jeśli tekst jest ucięty** (szerokość tekstu mierzona czcionką tabeli).

Dymki pojawiają się obok kursora; gdy nie mieszczą się przy prawej lub dolnej krawędzi ekranu, są wyświetlane na lewo od kursora lub nad nim.

Każda zmiana filtra natychmiast odświeża tabelę i licznik (`trace_add` na zmiennych Tkintera).

### 4.6. Pareto przyczyn przekroczeń

Dane: pacjenci z przekroczeniem, bez wierszy podejrzanych.

- **Słupki** – liczba pacjentów w każdej klasyfikacji przyczyny, malejąco, z liczbą nad słupkiem.
- **Linia** – skumulowany % (prawa oś, 0–110%).
- **Przerywana linia 80%** – próg zasady Pareto.
- **Panel wniosków** pod wykresem – najczęstsza przyczyna z liczbą i udziałem %. Gdy jest to „połączenie kilku czynników”, w nawiasie podawane są składowe czynniki z liczbami, np. „nadwaga / otyłość – 6 z 6, wysokie DLP fazy – 4 z 6”. Dodatkowo: ile kategorii odpowiada łącznie za ≥ 80% przekroczeń.

---

## 5. Wyniki dla danych przykładowych

Dla `ct_patients_data.csv` (150 pacjentów):

| Wynik | Wartość |
|---|---|
| Wiersze poprawne / podejrzane | 142 / 8 |
| Badania bez DPR w przepisach | 13 × „TK jamy brzusznej i miednicy” (9% badań), w tym 11 w protokole onkologicznym |
| Pacjenci z przekroczeniem DLP (bez podejrzanych) | 18 |
| Najczęstsza klasyfikacja | połączenie kilku czynników – 7 z 18 (39%) |
| Najczęstszy czynnik | nadwaga / otyłość – 12 z 18 (67%) |
| Okolica z największą liczbą przekroczeń | kręgosłup (28%) |
| Średnie przekroczenie | 13,9% |
| Kategorie odpowiadające za ≥ 80% przekroczeń | 3 z 6 (83%) |

Wiersze podejrzane (każdy łamie inną regułę z punktu 3.1):

| Pacjent | Powód podejrzenia |
|---|---|
| 104 | brak wartości w 'bmi' |
| 112 | wiek poza zakresem (0, 110) |
| 119 | BMI poza zakresem (10, 70) |
| 127 | liczba faz poza zakresem (1, 6) |
| 133 | DPR <= 0 |
| 138 | DLP ujemne |
| 144 | brak wartości w 'wiek'; BMI poza zakresem (10, 70) |
| 149 | brak wartości w 'dlp_zmierzony_na_faze_mGy_cm' |

Wykresy zbiorcze i wnioski o przekroczeniach liczone są tylko z 142 poprawnych wierszy (wyjątek: udział badań bez DPR liczony jest względem wszystkich 150 wykonanych badań). Tabela analizy przyczyn pokazuje 18 pacjentów z przekroczeniem i dodatkowo 8 wierszy z ⚠ na końcu.

---

## 6. Architektura

| Moduł | Odpowiedzialność | Zależy od Tkintera |
|---|---|---|
| `stale.py` | konfiguracja: ścieżka danych, progi, etykiety, kolory, definicje kolumn | nie |
| `przetwarzanie_danych.py` | wczytanie CSV, walidacja, analiza pacjenta, filtry płci/BMI | nie |
| `agregacje.py` | zliczenia, filtrowanie przyczyn, generowanie wniosków | nie |
| `wykresy.py` | budowa figur matplotlib | nie |
| `komponenty.py` | elementy GUI: tabela, karty, panel wniosków, panele filtrów, tooltipy, przycisk rozwijany, ustawienia czcionek | tak |
| `widoki.py` | składanie ekranów z komponentów i wykresów; widok analizy przyczyn jako klasa `WidokAnalizyPrzyczyn` (stan filtrów w atrybutach, `odswiez` i `wyczysc` jako metody) | tak |
| `uruchom.py` | okno główne, nagłówek, pasek przycisków, przełączanie widoków, `main()` | tak |

Logika obliczeń jest oddzielona od interfejsu, dzięki czemu można ją testować bez uruchamiania okna.

---

## 7. Ograniczenia

- Dane wczytywane są raz przy starcie; zmiana pliku CSV wymaga ponownego uruchomienia aplikacji.
- Brak eksportu wyników (CSV/PNG) i sortowania tabeli kliknięciem w nagłówek.
- Przyczyny przekroczeń są wskazywane regułowo (punkt 3.3) – to wskazówka do analizy, a nie ocena kliniczna.
- Dla badań spoza rozporządzenia (`BADANIA_BEZ_DPR`) nie da się ocenić przekroczenia dawki – aplikacja tylko pokazuje ich liczbę i udział.
- Wyśrodkowanie w obszarze roboczym i obsługa skalowania ekranu działają tylko na Windows.
