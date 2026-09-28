# Przykłady na magistrali

> **Nienormatywne.** Ten dokument nic nie ustala — pokazuje, jak reguły z rozdziałów
> `01`–`05` wyglądają w ramkach. Gdy coś tu przeczy specyfikacji, błąd jest tutaj.

Wszystkie identyfikatory i ładunki są policzone z [`05-mapowanie-can.md`](05-mapowanie-can.md);
pola wielobajtowe są little-endian ([`02-typy-danych.md`](02-typy-danych.md) §1).

---

## Instalacja, o której mowa

```
HUB  0x7FE
 │
 ├─ magistrala 1 — parter
 │   └─ 0x012   Panel dwuklawiszowy z podświetleniem, salon
 │              ep4  KeyInput                 ch1    klawisz lewy
 │              ep5  KeyInput                 ch2    klawisz prawy
 │              ep6  Output  INDICATOR        ch1    podświetlenie lewego
 │              ep7  Output  INDICATOR        ch2    podświetlenie prawego
 │
 └─ magistrala 2 — rozdzielnica
     ├─ 0x020   Przekaźnik 4× z pomiarem prądu
     │          ep4…ep7    Output  LIGHT          ch1…ch4
     │          ep8…ep11   Sense   CURRENT        ch1…ch4
     │          ep12       Sense   TEMPERATURE    ch0    w rozdzielnicy
     │
     └─ 0x021   Ściemniacz 2×
                ep4  Output [LEVEL] LIGHT     ch1    salon, lampa nad stołem
                ep5  Output [LEVEL] LIGHT     ch2    salon, kinkiety
```

Każdy węzeł ma ponadto `ep0 Device`, `ep1 Diagnostics` i `ep2 Groups`; węzły z wyjściami
mają też `ep3 Scenes` ([`01-model-danych.md`](01-model-danych.md) §1.2).

### Grupy

| Nr | Nazwa u operatora | Endpointy |
|---|---|---|
| `1` | wszystkie światła | `0x020` ep4–ep7, `0x021` ep4–ep5 |
| `5` | salon | `0x020` ep4, `0x021` ep4, `0x021` ep5 |
| `9` | podświetlenia paneli | `0x012` ep6, ep7 |

Nazwy mieszkają w bazie huba — węzeł zna wyłącznie numery
([`02-typy-danych.md`](02-typy-danych.md) §2.2).

### Sceny

| Para | Znaczenie |
|---|---|
| `(5, 1)` | wieczór w salonie: lampa 30 %, kinkiety 10 %, przekaźnik załączony |
| `(1, 1)` | wszystko zgaszone |

---

## Jak czytać identyfikator

Identyfikator ma 29 bitów i cztery pola ([`05-mapowanie-can.md`](05-mapowanie-can.md) §1):

```
   ID 0x08014301
      │
      ├── RODZAJ    0x4    KOMENDA_GRUPOWA
      ├── ADRES     0x005  numer grupy — bo rodzaj jest grupowy
      ├── ENDPOINT  3      Scenes
      └── ELEMENT   0x01   Recall
```

To samo pole `ADRES` niesie raz adres węzła, raz numer grupy, a raz adres nadawcy —
rozstrzyga o tym `RODZAJ`, i tylko on.

---

## 1. Konfiguracja: dodanie wyjścia do grupy

Operator tworzy grupę „salon". Hub wpisuje przynależność do każdego węzła osobno —
komendą adresowaną, bo chce potwierdzenia.

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → `0x020` ep2 | `0x06080200` | 4 | `01 04 05 00` |
| `0x020` → hub | `0x0E080200` | 1 | `01` |

```
ładunek żądania
  [0] 01        nagłówek: Tid = 1, pole wyniku puste
  [1] 04        endpoint docelowy — 4
  [2] 05 00     numer grupy 5, little-endian

ładunek odpowiedzi
  [0] 01        wynik OK (0), Tid = 1
```

Endpoint docelowy jedzie **w ładunku**, bo pole `ENDPOINT` identyfikatora wskazuje `2` —
czyli typ [`Groups`](types/0x0004-groups.md), który komendę wykonuje.

---

## 2. Konfiguracja: zapamiętanie sceny

Operator ustawia światła tak, jak mają wyglądać wieczorem, i utrwala stan. `Store` idzie
**adresowo do każdego węzła**, bo jego niepowodzenia nie widać w żadnym raporcie
([`types/0x0003-scenes.md`](types/0x0003-scenes.md) §6.3).

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → `0x020` ep3 | `0x06080300` | 4 | `02 05 00 01` |
| `0x020` → hub | `0x0E080300` | 1 | `02` |

```
  [0] 02        Tid = 2
  [1] 05 00     grupa 5
  [3] 01        scena 1
```

Węzeł `0x020` zapamiętuje stan **tylko tych swoich wyjść, które należą do grupy 5** —
czyli ep4. Kanały 2–4 zostają nietknięte. To samo powtarza się dla `0x021`.

---

## 3. Wieczór: naciśnięcie klawisza

Mieszkaniec naciska lewy klawisz. Panel emituje zdarzenie — **nie wie, co się z nim
stanie**, i nie wskazuje odbiorcy ([`04-interakcje.md`](04-interakcje.md) §6).

| | ID | DLC | Ładunek |
|---|---|---|---|
| `0x012` ep4 → magistrala | `0x02048403` | 2 | `2C 01` |

```
  [0] 2C        licznik kolejny zdarzenia — 44
  [1] 01        count = 1, czyli pojedyncze kliknięcie
```

`ADRES` w tej ramce to **nadawca**. Licznik pozwala hubowi zauważyć, że zgubił zdarzenie;
dziura znaczy „coś przepadło — zaloguj, ale wykonaj bieżące"
([`01-model-danych.md`](01-model-danych.md) §3.3).

---

## 4. Wieczór: hub przywołuje scenę

Hub dopasowuje powiązanie i nadaje **jedną** komendę grupową. Ramka trafia na magistralę 2,
bo tam siedzą odbiorcy — granica magistral jest niewidoczna dla mieszkańca
([`03-adresacja.md`](03-adresacja.md) §4).

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → grupa `5` | `0x08014301` | 3 | `01 D0 07` |

```
  [0] 01        scena 1
  [1] D0 07     transition = 2000 ms, little-endian

  bez nagłówka — komenda grupowa nie ma Tid ani odpowiedzi
  numer grupy nie jest w ładunku — jedzie w polu ADRES identyfikatora
```

**Pole `ENDPOINT` wynosi `3`, nie zero.** Gdyby było zerem, znaczyłoby „rozdziel do
endpointów należących do grupy" i trafiłoby w wyjścia, dla których element `0x01` znaczy
`On`, a nie `Recall` ([`04-interakcje.md`](04-interakcje.md) §5.2).

Skutek widać w raportach, które przychodzą same:

| | ID | DLC | Ładunek |
|---|---|---|---|
| `0x020` ep4 → raport `OnOff` | `0x10080400` | 1 | `01` |
| `0x021` ep4 → raport `Level` | `0x10084401` | 2 | `2C 01` |
| `0x021` ep5 → raport `Level` | `0x10084501` | 2 | `64 00` |

`2C 01` to `0x012C` = 300 promili, czyli 30 %; `64 00` to 100 promili, czyli 10 %
([`02-typy-danych.md`](02-typy-danych.md) §3.1).

Trzy raporty, bo do grupy 5 należą trzy wyjścia. Przychodzą **osobno i bez potwierdzenia** —
komenda grupowa żadnego nie miała ([`04-interakcje.md`](04-interakcje.md) §5.1).

---

## 5. Wyjście z domu: zgaś wszystko

Tu scena nie jest potrzebna — „zgaś" nie ma argumentów i mieści się w samej komendzie.

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → grupa `1` | `0x08004000` | 0 | — |

```
  ENDPOINT = 0   rozdziel: wykonuje KAŻDY endpoint węzła należący do grupy 1
  ELEMENT  = 0   Off

  ładunek pusty — Off nie ma argumentów
```

Jedna ramka gasi sześć wyjść w dwóch węzłach **w tej samej milisekundzie**. Sześć komend
adresowanych dałoby kaskadę rozciągniętą na kilkanaście milisekund — widoczną
([`03-adresacja.md`](03-adresacja.md) §3.1).

---

## 6. Sterowanie pojedyncze: gdy zależy nam na pewności

Przełączenie jednego obwodu idzie komendą adresowaną, bo ta ma odpowiedź.

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → `0x020` ep4 | `0x06080402` | 1 | `03` |
| `0x020` → hub | `0x0E080402` | 1 | `03` |
| `0x020` ep4 → raport | `0x10080400` | 1 | `00` |

Trzy ramki, dwa różne znaczenia. **Odpowiedź** mówi „przyjąłem i wykonałem"; **raport**
mówi, jaki był fizyczny skutek. Odpowiedź `OK`, po której nie przychodzi spodziewany
raport, oznacza przekaźnik, który polecenie przyjął i się nie przełączył — jedyny sposób
wykrycia zaciętego styku ([`types/0x0020-output.md`](types/0x0020-output.md) §5.4).

---

## 7. Ruch, którego nikt nie zamawiał

Czujnik prądu raportuje cyklicznie i przy zmianie.

| | ID | DLC | Ładunek |
|---|---|---|---|
| `0x020` ep8 → raport `Value` | `0x10080800` | 4 | `A4 01 00 00` |

`A4 01 00 00` to `420` przy skali 0,001 A, czyli **0,420 A**. Typ `i32`, bo instalacja
z fotowoltaiką oddaje prąd do sieci ([`02-typy-danych.md`](02-typy-danych.md) §3).

---

## 8. Rozpoznanie urządzenia: odczyt `Uid` w segmentach

Hub dodaje węzeł `0x020` do instalacji i musi poznać jego tożsamość. `Uid` to `blob`
o długości dwunastu bajtów — z dwubajtowym prefiksem długości daje czternaście, więc nie
mieści się w ramce ([`05-mapowanie-can.md`](05-mapowanie-can.md) §6).

| | ID | DLC | Ładunek |
|---|---|---|---|
| hub → `0x020` ep0, odczyt `Uid` | `0x0C080000` | 1 | `04` |
| `0x020` → hub, odpowiedź | `0x0E080000` | 1 | `5C` |
| segment 0 | `0x12080000` | 8 | `04 00 0C 00 33 00 27 00` |
| segment 1 | `0x12080000` | 8 | `04 01 12 51 34 33 31 32` |
| segment 2 | `0x12080000` | 4 | `84 02 37 30` |

```
odpowiedź
  [0] 5C        wynik 0x0B = SEGMENTED, Tid = 4
                „przyjąłem, wartość nie mieści się, nadchodzi segmentami"

segment
  [0] 04        LAST = 0, Tid = 4
  [1] 00        numer segmentu
  [2..7]        0C 00 — prefiks długości, 12 bajtów
                33 00 27 00 — pierwsze cztery bajty Uid

segment ostatni
  [0] 84        LAST = 1 (bit 7), Tid = 4
  [1] 02        numer segmentu
  [2..3]        37 30 — ostatnie dwa bajty
```

Trzy segmenty mają **identyczny identyfikator** — i to jest właśnie powód, dla którego
kolejność nie wymaga pilnowania: CAN nie przestawia ramek o tym samym ID. Numer segmentu
służy wyłącznie do wykrycia ubytku.

Odpowiedź `SEGMENTED` **nie jest błędem**, tylko zapowiedzią
([`04-interakcje.md`](04-interakcje.md) §9). Gdyby `Uid` miał cztery bajty, przyjechałby
w tej samej odpowiedzi i żaden segment by nie powstał.

---

## 9. Co się dzieje, gdy wszystko nadaje naraz

Arbitraż CAN wygrywa ramka o **niższym identyfikatorze**, a `RODZAJ` siedzi na najstarszych
bitach — numeracja rodzajów **jest** hierarchią priorytetów
([`05-mapowanie-can.md`](05-mapowanie-can.md) §2).

| Kolejność | ID | Ramka |
|---|---|---|
| 1 | `0x02048403` | zdarzenie klawisza `0x012` |
| 2 | `0x06080402` | komenda do `0x020` |
| 3 | `0x08004000` | komenda grupowa, grupa 1 |
| 4 | `0x10080800` | raport prądu `0x020` ep8 |
| 5 | `0x10540400` | raport temperatury `0x150` |

Dwie rzeczy widać z tej tabeli wprost:

**Zdarzenie wyprzedza wszystko.** Raport spóźniony o sekundę nadal niesie prawdę, zdarzenie
spóźnione o sekundę już nie ([`04-interakcje.md`](04-interakcje.md) §7.2).

**Wśród raportów wygrywa niższy adres**, dlatego czujniki siedzą w bloku `0x100`–`0x3FF`,
a urządzenia wymagające reakcji — w `0x001`–`0x0FF`
([`03-adresacja.md`](03-adresacja.md) §2.3). Przekaźnik `0x020` wyprzedza czujnik `0x150`
bez żadnego dodatkowego pola w ramce.
