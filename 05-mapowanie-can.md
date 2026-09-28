# 05 · Mapowanie na CAN 2.0B

> **Szkic.** Układ identyfikatora i ramka przyłączania są ustalone. Układy ładunków dla
> poszczególnych rodzajów są opisane częściowo i będą uzupełniane wraz z katalogiem typów endpointów.

Warstwa aplikacyjna opisana w rozdziałach `01`–`04` jest niezależna od medium. Ten rozdział
mówi, jak przełożyć ją na CAN 2.0B: identyfikator rozszerzony 29-bitowy, ładunek 8 bajtów.

---

## 1. Układ identyfikatora

```
 28 27 26 25 │ 24 23 22 21 20 19 18 17 16 15 14 │ 13 12 11 10 9 8 │ 7 6 5 4 3 2 1 0
 ┌─────────┐ │ ┌───────────────────────────────┐ │ ┌─────────────┐ │ ┌─────────────┐
 │ RODZAJ  │ │ │            ADRES              │ │ │  ENDPOINT   │ │ │   ELEMENT   │
 │   (4)   │ │ │            (11)               │ │ │     (6)     │ │ │     (8)     │
 └─────────┘ │ └───────────────────────────────┘ │ └─────────────┘ │ └─────────────┘
```

| Pole | Bity | Znaczenie |
|---|---|---|
| `RODZAJ` | 4 | rodzaj wiadomości; **wyznacza priorytet** (§2) |
| `ADRES` | 11 | jeden adres węzła — nadawca albo odbiorca, zależnie od rodzaju |
| `ENDPOINT` | 6 | `0`–`63` |
| `ELEMENT` | 8 | atrybut, komenda albo zdarzenie — rozstrzyga rodzaj |

Razem **29 bitów, bez ani jednego wolnego**.

`ADRES` jest pojedynczy, bo druga strona zawsze wynika z rodzaju
([`04-interakcje.md`](04-interakcje.md) §1). Wpisanie obu wymagałoby 37 bitów.

### 1.1 Dlaczego `Tid` nie jest w identyfikatorze

Identyfikator transakcji siedzi w **pierwszym bajcie ładunku**, nie w ramce. Powód jest
prosty: `Tid` służy wyłącznie do skojarzenia odpowiedzi z żądaniem i **nikt nie filtruje
po nim sprzętowo**. Trzymanie go w identyfikatorze zabierałoby trzy bity polu, w którym
robią realną różnicę.

W odpowiedzi `Tid` mieści się w bajcie, który i tak tam jest — dzieli go z kodem wyniku,
więc odpowiedzi nie urosły ani o bajt. Rosną tylko komendy i zapisy, o jeden bajt.

### 1.2 Skąd 11 bitów

Osiem bitów dawałoby 253 węzły. Wystarczyłoby dla domu jednorodzinnego, gdzie realny
szacunek to około stu urządzeń — ale nie zostawiałoby miejsca na **numerowanie blokami**
(§2.2), a przy większej instalacji sufit stawałby się realny.

Jedenaście bitów to 2045 węzłów przy koszcie jednego bajtu ładunku w wiadomościach
transakcyjnych. Model danych pozostał nietknięty: endpoint nadal ma 64 wartości, element
256.

---

## 2. Rodzaje wiadomości i priorytet

W CAN wygrywa arbitraż ramka o **niższym identyfikatorze**. `RODZAJ` siedzi na
najstarszych bitach, więc numeracja rodzajów **jest** hierarchią priorytetów — nie trzeba
osobnego pola.

| `RODZAJ` | Nazwa | Kierunek | `ADRES` to | Transakcyjna |
|---|---|---|---|---|
| `0x0` | `ALARM` | węzeł → | nadawca | nie |
| `0x1` | `ZDARZENIE` | węzeł → | nadawca | nie |
| `0x2` | **rezerwa wysoka** | | | *(§2.3)* |
| `0x3` | `KOMENDA` | hub → węzeł | odbiorca | **tak** |
| `0x4` | `KOMENDA_GRUPOWA` | hub → grupa | numer grupy | nie |
| `0x5` | `ZAPIS` | hub → węzeł | odbiorca | **tak** |
| `0x6` | `ODCZYT` | hub → węzeł | odbiorca | **tak** |
| `0x7` | `ODPOWIEDŹ` | węzeł → hub | nadawca | **tak** |
| `0x8` | `RAPORT` | węzeł → | nadawca | nie |
| `0x9` | `ODPOWIEDŹ_DŁUGA` | węzeł → hub | nadawca | *(§6)* |
| `0xA` | `ZAPIS_DŁUGI` | hub → węzeł | odbiorca | *(§6)* |
| `0xB` | `ZAPYTANIE` | węzeł → hub | nadawca | **tak** |
| `0xC` | `ODPOWIEDŹ_HUBA` | hub → węzeł | odbiorca | **tak** |
| `0xD`–`0xE` | rezerwa niska | | | |
| `0xF` | `PRZYŁĄCZANIE` | obustronnie | *(patrz §4)* | nie |

Wiadomości transakcyjne niosą `Tid` w pierwszym bajcie ładunku (§5.1); pozostałe nie mają
tego bajtu wcale.

`ALARM` przenosi raporty z wejść alarmowych i zgłoszenia awarii węzła. Jest to jedyny
sposób, by nadać im pierwszeństwo — priorytet w CAN wynika wyłącznie z identyfikatora,
więc musi być zakodowany w jego górnych bitach.

Rozstrzyga to dwa zobowiązania zaciągnięte wcześniej: pierwszeństwo zdarzeń przed
raportami ([`04-interakcje.md`](04-interakcje.md) §7.2) i podwyższony priorytet wejść
alarmowych ([`types/0x0012-contact.md`](types/0x0012-contact.md) §5.4).

### 2.1 W obrębie rodzaju wygrywa niższy adres

Węzeł `0x001` zawsze wyprzedzi `0x7FD`. Przy obciążeniu rzędu kilku procent nie ma to
znaczenia, ale przy wysyceniu magistrali węzły o wysokich adresach byłyby głodzone.

### 2.2 Skutek: numerowanie blokami

Skoro kolejność arbitrażu wynika wprost z adresu, **sam sposób numerowania staje się
mechanizmem priorytetu** — bez jednego dodatkowego pola w ramce. Przy adresie
ośmiobitowym na taki podział nie było miejsca; to najbardziej praktyczny skutek
rozszerzenia adresu do jedenastu bitów.

Podział puli adresowej na bloki jest normatywny i znajduje się
w [`03-adresacja.md`](03-adresacja.md) §2.3.

### 2.3 Dlaczego `0x2` jest pusty

Numeracja rodzajów **jest** drabinką priorytetów, więc miejsce w niej to zasób — i to taki,
którego po zamrożeniu kontraktu nie da się już powiększyć. Przesunięcie istniejącej wartości
łamie zgodność w każdej implementacji naraz.

Wolne wartości `0xD`–`0xE` leżą **poniżej `RAPORTU`** i nadają się wyłącznie do rzeczy
niepilnych. Gdyby zabrakło tylko ich, każda przyszła wiadomość wymagająca **wysokiego**
priorytetu byłaby nie do dołożenia.

Dlatego `0x2` zostaje pusty **z zapasem na sterowanie, którego jeszcze nie ma**. Wiadomo
już, co się o nie upomni: regulator zadający wartość ciągłą — położenie zaworu, prędkość
wentylatora — nie ma czego wysłać jako zdarzenia, a jego raport siedziałby na `0x8`, za
wszystkimi komendami ([`types/0x0040-thermostat.md`](types/0x0040-thermostat.md) §4.1).

Rezerwa kosztuje jedną wartość z szesnastu i nic poza tym. Jej brak kosztowałby kiedyś
przenumerowanie całej drabinki.
---

## 3. Filtrowanie sprzętowe

Układ pól jest dobrany tak, by kontroler CAN odsiewał ruch bez budzenia procesora.

Typowy węzeł przepuszcza:

| Maska | Po co |
|---|---|
| `RODZAJ ∈ {KOMENDA, ZAPIS, ODCZYT}` **i** `ADRES = własny` | wszystko skierowane do mnie |
| `RODZAJ = KOMENDA_GRUPOWA` **i** `ADRES ∈ własne grupy` | po jednym filtrze na grupę (§3.1) |
| `RODZAJ = PRZYŁĄCZANIE` **i** `ShortId = własny` | tylko własny przydział |

Węzeł nie musi widzieć raportów ani zdarzeń innych urządzeń — konsumuje je wyłącznie hub.
Filtry węzła są przez to bardzo wąskie, a procesor budzi się niemal wyłącznie do ruchu
skierowanego do niego.

Hub przepuszcza wszystko.

### 3.1 Filtrowanie grup ma granicę

Filtr na grupę wymaga jednego banku filtrów na każdą grupę, do której węzeł należy.
**Kontrolery mają ich kilkanaście, nie setki** — bxCAN w STM32F1 czternaście na dwa
interfejsy — więc reguła „po jednym filtrze na grupę" działa do kilkunastu grup i nie dalej.

Węzeł, który należy do większej ich liczby, **przyjmuje wszystkie ramki rodzaju
`KOMENDA_GRUPOWA` i odsiewa je programowo**. Jest to dopuszczalne i nie zmienia niczego
w formacie ramki; kosztuje tylko tym, że procesor budzi się do każdej komendy grupowej
w instalacji, także takiej, która go nie dotyczy.

Przy obciążeniu magistrali poniżej procenta (§6) jest to bez znaczenia. Warto natomiast
wiedzieć, że **granica istnieje i przebiega po stronie sprzętu, a nie specyfikacji** —
projektant węzła, któremu zależy na filtrowaniu sprzętowym, trzyma liczbę grup
w kilkunastu ([`types/0x0004-groups.md`](types/0x0004-groups.md) §5.3).

---

## 4. Ramka przyłączania

`PRZYŁĄCZANIE` ma **własny układ identyfikatora**, bo nie ma czym wypełnić pola adresu —
węzeł go jeszcze nie zna ([`03-adresacja.md`](03-adresacja.md) §5.2).

```
 28 27 26 25 │ 24 │ 23 22 21 20 19 18 17 16 15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 0
 ┌─────────┐ │ ┌┐ │ ┌───────────────────────────────────────────────────────────┐
 │  0xF    │ │ │K│ │ │                   ShortId [23:0]                          │
 └─────────┘ │ └┘ │ └───────────────────────────────────────────────────────────┘

 K = 0   PRZYDZIAŁ    hub → węzeł
 K = 1   ZGŁOSZENIE   węzeł → hub
```

Ładunek:

```
ZGŁOSZENIE   [0..3] ShortId (32 b)   [4] NodeClass         [5..7] rezerwa
PRZYDZIAŁ    [0..3] ShortId (32 b)   [4..5] adres (u16)    [6..7] rezerwa
```

### 4.1 `NodeClass` — jedyna rzecz, którą węzeł mówi o sobie przed enumeracją

| Wartość | Nazwa | Blok adresowy | Kto tu należy |
|---|---|---|---|
| `0` | `UNSPECIFIED` | rezerwa `0x400`–`0x7FD` | węzeł, który klasy nie deklaruje |
| `1` | `CONTROL` | `0x001`–`0x0FF` | ruch, na który ktoś musi zareagować |
| `2` | `SENSOR` | `0x100`–`0x3FF` | pomiary raportowane cyklicznie |
| `3`–`255` | — | — | rezerwa, nadawaj `0` |

Blok adresowy jest **jedynym mechanizmem priorytetu** poza rodzajem wiadomości
([`03-adresacja.md`](03-adresacja.md) §2.3), a adres nadany przy przyłączaniu zostaje
z węzłem na całe życie. Hub musi więc wybrać blok w chwili, w której nie może odczytać
z węzła niczego — do odczytu potrzebny jest adres, a adresu jeszcze nie ma.

`NodeClass` rozcina to jajko i kurę **jedną liczbą, której nikt nie musi tłumaczyć**.
Nie jest to numer modelu wymagający tablicy po stronie huba: węzeł obcego autora, o którym
hub nie wie nic, trafia do właściwego bloku tak samo jak własny.

> **`NodeClass` nie jest atrybutem i nie da się go odczytać.** Żyje wyłącznie w tej jednej
> ramce, a jego rola kończy się w chwili, gdy hub odczyta deskryptor.

Jest to celowe. Klasa jest **wskazówką do rozruchu**, a nie prawdą o urządzeniu — prawdą
są typy endpointów. Gdyby klasa istniała jako atrybut, powstałby drugi opis tego samego,
mający jak rozjechać się z pierwszym ([`01-model-danych.md`](01-model-danych.md) §3).

Wskazówka bywa więc niedokładna i nic się nie psuje. Hub, który po enumeracji stwierdzi, że
węzeł zadeklarował `SENSOR`, a ma endpointy `Output`, przesuwa go zapisem `Device.Address`
([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §4) — tą samą drogą, którą
przechodzi każdy węzeł klasy `UNSPECIFIED`.

**Węzeł mieszany deklaruje klasę najostrzejszego ruchu, jaki generuje.** Panel z klawiszami
i termometrem jest `CONTROL`: zdarzenie z klawisza nie może czekać za raportem temperatury,
a odwrotna pomyłka jest niegroźna.

### 4.2 Dlaczego `ShortId` jest w identyfikatorze

Arbitraż CAN jest bezkolizyjny **tylko wtedy, gdy identyfikatory się różnią**. Dwa węzły
nadające ten sam identyfikator z różną treścią oba wygrywają arbitraż, wchodzą w pole
danych i zderzają się na pierwszym różniącym się bicie — po czym oba powtarzają i zderzają
się znowu.

Umieszczenie `ShortId` w identyfikatorze sprawia, że każdy zgłaszający się węzeł nadaje
inny identyfikator. Arbitraż ustawia je w kolejkę sprzętowo, bez udziału oprogramowania.

Przy 24 bitach prawdopodobieństwo kolizji wśród czterdziestu węzłów wynosi około
**1 do 21 000**, czyli 0,005%. Gdyby jednak zaszła, ratuje losowa zwłoka przy kolejnej
próbie ([`03-adresacja.md`](03-adresacja.md) §5.6).

Adres w `PRZYDZIALE` zajmuje dwa bajty, bo ma jedenaście bitów (§1.2); pięć najstarszych
jest zawsze zerowych.

### 4.3 Dlaczego pełny `ShortId` jest też w ładunku

Nadmiarowość jest celowa. Identyfikator służy do rozstrzygania arbitrażu i do filtrowania
sprzętowego, a ładunek — do jednoznacznego potwierdzenia tożsamości. **Hub porównuje pełne
32 bity**, zanim przydzieli adres.

### 4.4 Dlaczego przydział ma `K = 0`

Niższy identyfikator wygrywa, więc odpowiedź huba wyprzedza kolejne zgłoszenia. Przydziały
przeciskają się przez tłum zgłaszających się urządzeń i odblokowują je po kolei, zamiast
czekać na koniec fali.

Węzeł filtruje przydział **sprzętowo**, po własnym `ShortId` w identyfikatorze. Przy
czterdziestu urządzeniach zgłaszających się naraz procesor każdego z nich widzi jedną
ramkę zamiast osiemdziesięciu.

---

## 5. Ładunki

> Uzupełniane wraz z katalogiem typów endpointów.

### 5.1 Bajt nagłówkowy wiadomości transakcyjnych

`KOMENDA`, `ZAPIS`, `ODCZYT` i `ODPOWIEDŹ` mają w bajcie `[0]`:

```
 bit  7  6  5  4  3 │  2  1  0
     ┌─────────────┐│┌────────┐
     │   WYNIK     │││  Tid   │      WYNIK tylko w ODPOWIEDZI;
     │    (5)      │││  (3)   │      w pozostałych: rezerwa, nadawaj 0
     └─────────────┘│└────────┘
```

Pięć bitów na wynik daje 32 wartości; kodów jest dziś trzynaście
([`04-interakcje.md`](04-interakcje.md) §9).

### 5.2 Układy

| Rodzaj | Ładunek |
|---|---|
| `ODCZYT` | `[0]` nagłówek |
| `ODPOWIEDŹ` | `[0]` nagłówek z wynikiem, `[1..]` wartość (gdy `OK`) |
| `ZAPIS` | `[0]` nagłówek, `[1..]` wartość atrybutu |
| `KOMENDA` | `[0]` nagłówek, `[1..]` argumenty |
| `KOMENDA_GRUPOWA` | `[0..]` argumenty — **bez nagłówka**, nie ma `Tid` |
| `RAPORT`, `ALARM` | `[0..]` wartość atrybutu |
| `ZDARZENIE` | `[0]` licznik kolejny, `[1..]` parametry |
| `ODPOWIEDŹ_DŁUGA`, `ZAPIS_DŁUGI` | `[0]` `LAST` + `Tid`, `[1]` numer segmentu, `[2..7]` dane (§6.3) |
| `ZAPYTANIE` | `[0]` nagłówek z `Tid` |
| `ODPOWIEDŹ_HUBA` | `[0]` nagłówek z wynikiem, `[1..]` wartość (gdy `OK`) |

### 5.3 Zapytanie i odpowiedź huba

Zapytanie to **jedyna transakcja, którą zaczyna węzeł**
([`04-interakcje.md`](04-interakcje.md) §8), i jedyne miejsce, w którym odpowiedź płynie
od huba do węzła. Stąd dwa rodzaje zamiast jednego: pole `ADRES` pełni w nich odwrotne
role, a rozstrzyga o tym wyłącznie `RODZAJ`.

```
ZAPYTANIE        ADRES = nadawca   [0] nagłówek z Tid
ODPOWIEDŹ_HUBA   ADRES = odbiorca  [0] nagłówek z wynikiem i Tid, [1..] wartość
```

Pola `ENDPOINT` i `ELEMENT` mówią, o który atrybut chodzi — tak jak w każdej innej ramce.

**Priorytet jest najniższy z ruchu roboczego**, niżej nawet niż segmenty. Wynika stąd
sytuacja warta odnotowania: długie przesyłanie wartości może opóźnić zapytanie o tyle, że
minie sto milisekund i węzeł powtórzy. Nie jest to problem — najdłuższe przesyłanie trwa
około 154 ms, a budżet trzech prób to 300 ms, więc druga próba przechodzi.

Długość wartości wynika z typu atrybutu ([`02-typy-danych.md`](02-typy-danych.md) §2),
a nie z pola w ramce. Odbiorca zna typ atrybutu, bo zna typ endpointu.

Najciaśniejszy przypadek to dziś odpowiedź na `GetMembership` typu `Groups`: nagłówek,
licznik i trzy numery grup — **8 z 8 bajtów, bez ani jednego wolnego**. To ona wyznacza,
że jedna odpowiedź niesie trzy grupy, a nie cztery
([`types/0x0004-groups.md`](types/0x0004-groups.md) §3.1).

Zaraz za nią jest komenda `SetColor` typu `Output`: nagłówek, cztery składowe barwy i czas
przejścia — **7 z 8**. Najdłuższy raport to stan tego samego typu z cechą `COLOR_RGB`:
6 bajtów, bez nagłówka.

Warto sprawdzać ten rachunek po każdym nowym typie. Ładunek jest jedynym zasobem w tej
specyfikacji, którego nie da się powiększyć.

---

## 6. Wartości dłuższe niż ramka

Niektóre wartości nie mieszczą się w ośmiu bajtach: `Uid` ma do szesnastu, nazwa modelu do
dwustu pięćdziesięciu pięciu, lista przynależności do grup — do pięciuset. Przesyła się je
wtedy **w segmentach**.

> **Segmentowanie nie jest osobną interakcją.** Jest **sposobem przeniesienia wartości**,
> która nie mieści się w ramce ([`04-interakcje.md`](04-interakcje.md)) — odczyt pozostaje
> odczytem, a zapis zapisem.
> Dlatego rodzaje ramek nazywają się `ODPOWIEDŹ_DŁUGA` i `ZAPIS_DŁUGI`, a nie jakkolwiek
> inaczej: są długimi odmianami tego, co już istnieje.

### 6.1 Dwa rodzaje, po jednym na kierunek

| `RODZAJ` | Nazwa | Kierunek | `ADRES` to |
|---|---|---|---|
| `0x9` | `ODPOWIEDŹ_DŁUGA` | węzeł → hub | nadawca |
| `0xA` | `ZAPIS_DŁUGI` | hub → węzeł | odbiorca |

Oba siedzą **poniżej `RAPORTU`**, czyli na końcu ruchu roboczego. Jest to zamierzone:
segmenty przenoszą dane, które i tak czekają na człowieka albo na enumerację, i nie mają
prawa opóźnić ani zdarzenia, ani komendy, ani raportu stanu.

### 6.2 Dlaczego osobne rodzaje, a nie ciąg dalszy `ODPOWIEDZI`

Skoro odczyt długiej wartości jest **jednym odczytem**, a segmenty są po prostu jego
odpowiedzią, nasuwa się pytanie, po co im własne rodzaje. Ciąg dalszy dałoby się oznaczyć
w polu `WYNIK`, które ma 32 wartości, a używamy trzynastu — i wyszłoby tyle samo danych na
segment, bo numer segmentu zająłby bajt `[1]` tak czy owak.

Powodem jest **priorytet**, i tylko on:

| Rodzaj | `RODZAJ` |
|---|---|
| `ODPOWIEDŹ` | `0x7` |
| `RAPORT` | `0x8` |
| `ODPOWIEDŹ_DŁUGA` | `0x9` |

`ODPOWIEDŹ` wyprzedza `RAPORT`. Gdyby segmenty były odpowiedziami, odczyt pełnej wartości —
256 ramek po około 0,6 ms — **zagłodziłby wszystkie raporty w instalacji na jakieś
150 milisekund**, bo każdy segment wygrywałby arbitraż z każdym raportem stanu. Przy
trzysegmentowym `Uid` nikt by tego nie zauważył; przy liście przynależności do grup już tak.

Dane masowe muszą stać **za** raportami, a priorytet w CAN wynika wyłącznie z identyfikatora
(§2). `RODZAJ` jest więc jedynym miejscem, w którym da się to zapisać.

Pola `ENDPOINT` i `ELEMENT` niosą to samo co w zwykłej ramce — **czego dotyczy wartość**.
Ramka jest przez to samoopisująca się i nie trzeba powtarzać tego w ładunku. Działa to
zarówno dla atrybutu, jak i dla odpowiedzi na komendę, bo `ELEMENT` identyfikuje jedno
i drugie.

### 6.3 Ładunek segmentu

```
 [0]   bit 7      LAST — ostatni segment wartości
       bity 6…3   rezerwa, nadawaj 0
       bity 2…0   Tid

 [1]   numer segmentu, 0…255

 [2…7] dane — 6 bajtów na segment
```

Pojemność jednej wartości to **256 × 6 = 1536 bajtów**. Bajt `[0]` ma celowo ten sam kształt co
nagłówek transakcyjny (§5.1): trzy najmłodsze bity to `Tid`, a `LAST` zajmuje jeden bit
z pola, które tam jest rezerwą.

### 6.4 Po co `Tid` w segmencie

Kolejność jest darmowa: **CAN nie przestawia ramek o tym samym identyfikatorze**, a wszystkie
segmenty jednej wartości mają identyczny identyfikator. Numer segmentu służy więc wyłącznie
do wykrycia ubytku, nie do układania.

`Tid` robi co innego — **wiąże segmenty z transakcją, która je wywołała**. Bez niego nie dałoby
się dokończyć zapisu: węzeł, który odebrał ostatni segment, musi odpowiedzieć, a odpowiedź bez
`Tid` nie ma jak zostać skojarzona z żądaniem ([`04-interakcje.md`](04-interakcje.md) §2).

Przy odczycie `Tid` jest mniej konieczny, ale zostaje — jeden układ ładunku w obu kierunkach
jest wart jednego bajtu na segment.

### 6.5 Segment zerowy zaczyna od nowa

Powtórzenie żądania używa **tego samego `Tid`** ([`04-interakcje.md`](04-interakcje.md) §2.1),
więc `Tid` nie odróżnia drugiej próby od pierwszej. Rozstrzyga to inna reguła:

> **Segment o numerze `0` unieważnia wszystko, co odebrano wcześniej dla tej wartości.**

Ponieważ kolejność jest gwarantowana, spóźnione segmenty porzuconej próby przychodzą **przed**
segmentem zerowym nowej i zostają wyrzucone razem z nią. Nie ma sposobu, żeby dwie próby
zostały sklejone w jedną wartość.

### 6.6 Błędy i porzucenie

| Sytuacja | Co robi odbiorca |
|---|---|
| dziura w numeracji segmentów | porzuca wartość w całości |
| brak kolejnego segmentu przez **100 ms** | porzuca wartość w całości |
| długość danych przeczy prefiksowi długości wartości | porzuca i zgłasza `INVALID_VALUE` |

**Nie ma retransmisji częściowej.** Nadawca powtarza całe żądanie, a nie brakujący segment.
Przy szesnastu bajtach `Uid` i trzech segmentach oszczędność byłaby żadna, a mechanizm
wznawiania — kolejnym stanem do utrzymania po obu stronach.

Zapis porzucony w połowie **nie zmienia niczego**: węzeł odrzuca kawałki i nie rusza atrybutu,
zgodnie z zasadą, że zapis jest niepodzielny ([`04-interakcje.md`](04-interakcje.md) §4).

### 6.7 Jedna wartość naraz

Węzeł składa **najwyżej jedną wartość w każdą stronę naraz**. Żądanie, które wymagałoby drugiej,
kończy się `BUSY` — jedynym kodem, po którym warto powtórzyć
([`04-interakcje.md`](04-interakcje.md) §9).

Pozwala to trzymać w węźle jeden bufor zamiast tablicy i jest spójne z regułą, że węzeł musi
obsłużyć co najmniej jedno żądanie naraz, a nie więcej
([`04-interakcje.md`](04-interakcje.md) §10).

### 6.8 Kierunek do węzła nie ma dziś użytkownika

`ZAPIS_DŁUGI` jest zdefiniowany, ale **żaden atrybut w tej wersji specyfikacji nie jest
zarazem długi i zapisywalny**: `Uid`, `VendorName` i `ModelName` są `RO`, a nazwy nadawane
przez człowieka nie mieszkają w węźle.

Jest to zdefiniowane mimo to, bo pierwszy użytkownik jest już widoczny — komenda definiująca
scenę wartościami wprost ([`types/0x0003-scenes.md`](types/0x0003-scenes.md) §6.8) — a układ
ładunku wspólny dla obu kierunków nie kosztuje nic poza jednym akapitem tutaj. Dokładanie go
później oznaczałoby drugi format do zaimplementowania w każdym węźle.

### 6.9 Czego segmenty nie obsłużą

**Aktualizacji firmware.** Tysiąc pięćset bajtów to nie jest obraz programu, a wymagania są
zupełnie inne: wznawianie po zerwaniu, weryfikacja sumy kontrolnej, tryb awaryjny na wypadek
przerwanej aktualizacji. Gdyby kiedyś doszła, potrzebuje **własnego mechanizmu** — i lepiej,
żeby go dostała, niż żeby ktoś próbował rozciągnąć ten do rozmiaru, na który nie był
projektowany.

---

## 7. Budżet pasma

Ramka rozszerzona z ośmioma bajtami danych to około **150 bitów** po wypełnieniu bitami
uzupełniającymi. Przy 250 kbit/s daje to **0,6 ms na ramkę**, czyli około 1600 ramek
na sekundę.

Szacunek ruchu ustalonego dla magistrali z czterdziestoma węzłami:

| Źródło | Częstość | Ramek/s |
|---|---|---|
| czujniki, odświeżanie cykliczne | 20 × co 60 s | 0,3 |
| aktuatory, odświeżanie cykliczne | 15 × co 300 s | 0,05 |
| zdarzenia klawiszy | seriami, kilkaset dziennie | ~0,01 średnio |

Obciążenie ustalone **znacznie poniżej 1%**. Nawet szczyt — wszystkie klawisze naciśnięte
naraz, wszystkie czujniki raportujące jednocześnie — nie zbliża się do wysycenia.

Wynika stąd, że **prędkość magistrali nie jest ograniczeniem tego projektu**. Wybór 250
kbit/s zamiast 500 kbit/s można podjąć wyłącznie ze względu na długość kabla i odporność
na zakłócenia, bez oglądania się na przepustowość.
