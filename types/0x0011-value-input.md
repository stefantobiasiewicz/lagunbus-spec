# Typ endpointu `0x0011` · ValueInput

> **Szkic.** Zakres, krok i zachowanie przy przytrzymaniu rozstrzygnięte. Typ czeka na
> pierwsze zbudowane urządzenie.

**Rewizja 1** · wejście z własną wartością

Wejście obsługiwane palcem, które **trzyma liczbę** i pozwala ją zmieniać: para klawiszy
„w górę / w dół", enkoder obrotowy, suwak, kółko.

> **Czym to się różni od [`KeyInput`](0x0010-key-input.md).** Klawisz mówi, że ktoś go
> nacisnął. To wejście mówi, **ile teraz jest** — naciśnięcie jest wyłącznie sposobem
> dojścia do liczby, a nie treścią wiadomości.

Konsekwencja, którą łatwo przeoczyć: **jeden endpoint to jedna wartość, a nie jeden
klawisz.** Para klawiszy podbijających i obniżających jasność jest **jednym** endpointem
`ValueInput`, bo obsługuje jedną liczbę. Rozbicie jej na dwa endpointy opisywałoby sprzęt
zamiast funkcji i zostawiało hubowi sklejanie ich z powrotem.

Ten typ zajmuje numer zarezerwowany wcześniej pod nazwą `Encoder`. Enkoder obrotowy jest
**sprzętem**, a katalog nazywa **funkcje** — dokładnie tę samą funkcję pełni para klawiszy
i suwak. Rezerwacja znika, bo opisywała jedno wykonanie zamiast całej rodziny.

**Jak czytać tabele.** Pełne definicje kolumn są w
[`01-model-danych.md`](../01-model-danych.md) §3.1 i §8; w skrócie:

| Kolumna | Wartość | Znaczy |
|---|---|---|
| **Dostęp** | `RO` · `RW` · `WO` | tylko odczyt · odczyt i zapis · tylko zapis — z magistrali |
| **Trw.** | `P` · `V` | przeżywa zanik zasilania · tylko w RAM |
| **Rap.** | tak · nie | czy węzeł sam wysyła raport przy zmianie |
| **Konf.** | `M` | obowiązkowy — każde urządzenie tego typu **musi** go mieć |
| | `O` | opcjonalny — urządzenie **może** go mieć; jeśli ma, działa tak, jak opisano |
| | `[CECHA]` | obowiązkowy wtedy i tylko wtedy, gdy urządzenie zadeklarowało tę cechę (§1) |
| | `[CECHA, CECHA]` | obowiązkowy, gdy zadeklarowało **którąkolwiek** z wymienionych |
| | `O [CECHA]` | opcjonalny, ale wolno go mieć **tylko** z tą cechą |
| **Zakres** | | dopuszczalne wartości; zapis spoza nich dostaje `INVALID_VALUE` |
| **Domyśl.** | | wartość po resecie fabrycznym |

---

## 1. Cechy

**Brak.** Wszystko, czym te urządzenia się różnią — zakres, wielkość kroku, zawijanie,
obecność przytrzymania — jest konfiguracją zmienną w czasie pracy. Enkoder i para klawiszy
różnią się czasem drgań styków, a to atrybut, nie cecha.

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `Value` | `u16` | RW | P | **tak** | M | promile, `MinValue`–`MaxValue`, §5.1 |
| `0x01` | `ChangeCount` | `u32` | RO | P | nie | O | liczba zmian przez całe życie |

`Value` jest **zapisywalny** — to jedyny sposób, żeby panel nadążył za światłem zgaszonym
z telefonu (§5.5).

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `MinValue` | `u16` | RW | P | nie | M | 0–1000 ‰ | `0` |
| `0x11` | `MaxValue` | `u16` | RW | P | nie | M | 0–1000 ‰ | `1000` |
| `0x12` | `StepSize` | `u16` | RW | P | nie | M | 1–1000 ‰ | `50` |
| `0x13` | `HoldEnabled` | `bool` | RW | P | nie | M | — | `1` |
| `0x14` | `HoldStepSize` | `u16` | RW | P | nie | M | 1–1000 ‰ | `50` |
| `0x15` | `HoldThreshold` | `u16` | RW | P | nie | M | 200–3000 ms | `500` |
| `0x16` | `HoldTickInterval` | `u16` | RW | P | nie | M | 50–1000 ms | `200` |
| `0x17` | `DebounceTime` | `u16` | RW | P | nie | M | 5–100 ms | `15` |
| `0x18` | `Wrap` | `bool` | RW | P | nie | O | — | `0` |

`MinValue` większe od `MaxValue` jest błędem konfiguracji — zapis, który by do tego
doprowadził, kończy się `INVALID_VALUE`
([`../04-interakcje.md`](../04-interakcje.md) §9).

---

## 3. Komendy

**Brak.** `Value` jest zapisywalny, więc hub ustawia go zwykłym zapisem atrybutu. Komenda
`SetValue` byłaby drugą drogą do tego samego skutku, a dwie drogi znaczą dwa miejsca do
utrzymania i dwa zestawy kodów błędów.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Konf. |
|---|---|---|---|---|
| `0x01` | `Changed` | `value: u16` [‰], `delta: i16` [‰] | `INFO` | M |

`value` to wartość **po** zmianie, `delta` — o ile się zmieniła i w którą stronę.

`delta` nie jest powtórzeniem tego, co hub sam by policzył. Pozwala związać to wejście
wprost z komendą `Step` typu [`Output`](0x0020-output.md), bez pamiętania po stronie huba,
ile było poprzednio — a powiązanie, które niczego nie pamięta, przeżywa restart huba.

### 4.1 Dlaczego zdarzenie, skoro jest atrybut

Wejście obsługiwane przez człowieka opisuje **decyzję sterującą**, a nie obserwację —
i dlatego wolno mu użyć wyjątku od podziału na stan i fakt
([`../01-model-danych.md`](../01-model-danych.md) §3), tego samego, po który sięga
[`Thermostat`](0x0040-thermostat.md) §4.1.

Powód jest ten sam, tylko silniejszy: **raport jedzie z priorytetem `0x8`, czyli na końcu
stawki** ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §2). Sygnał, który powstał,
bo ktoś właśnie nacisnął klawisz, nie ma prawa czekać w kolejce za odczytem temperatury.
Zdarzenie jedzie z `0x1` i wyprzedza nawet komendy huba.

Do tego dochodzi drugi powód, którego termostat nie ma: **raport ze zmiany podlega
histerezie i minimalnemu odstępowi** ([`../01-model-danych.md`](../01-model-danych.md) §6).
Oba mechanizmy powstały po to, żeby tłumić szum przetwornika — a zastosowane do palca
zjadłyby pojedyncze kliknięcie albo je opóźniły. Zdarzenie nie podlega żadnemu z nich.

Role są więc rozdzielone i obie potrzebne:

| | Rola |
|---|---|
| `Changed` | **szybka ścieżka** — hub dowiaduje się natychmiast i działa |
| `Value` | **prawda i odtwarzanie** — przeżywa zgubione zdarzenie, wraca cyklicznie |

> **Przy rozbieżności obowiązuje raport.** Zdarzenie może przepaść i nie jest powtarzane
> ([`../04-interakcje.md`](../04-interakcje.md) §7.1); raport przyjdzie znowu najpóźniej po
> `ReportInterval` i to on jest rozstrzygający.

---

## 5. Zachowanie

### 5.1 Wartość jest w promilach

`Value` jest liczbą z zakresu 0–1000 ‰ i **nie ma jednostki**. Węzeł nie wie, czy steruje
jasnością, głośnością, czy prędkością wentylatora — wie tylko, ile wynosi liczba.

Skala jest ta sama co `Level` typu [`Output`](0x0020-output.md), i to jest jej jedyne
uzasadnienie: powiązanie „to wejście steruje tamtym wyjściem" ma być **przepisaniem
liczby**, a nie przeliczaniem. Panel pokazujący użytkownikowi `0–100 %` dzieli przez
dziesięć w chwili wyświetlania ([`../02-typy-danych.md`](../02-typy-danych.md) §3.1);
na magistrali jest promil.

Co ten typ **świadomie pomija**: nastawy wyrażone w jednostkach fizycznych. Ścienne
pokrętło zadające 21,5 °C nie jest `ValueInput` — wartość ma tam jednostkę i skalę,
a te w tej rewizji nie istnieją.

### 5.2 Krok, nasycenie i zawijanie

Pojedyncze kliknięcie zmienia `Value` o `StepSize`, przytrzymanie — o `HoldStepSize`
na takt.

Przy `Wrap = 0` wartość **nasyca się** na `MinValue` i `MaxValue`: dalsze naciskanie nic
nie zmienia i **nie emituje zdarzeń**, bo nie ma czego ogłaszać. Jest to zachowanie
domyślne, bo odpowiada temu, czego człowiek się spodziewa po suwaku.

Przy `Wrap = 1` wartość przeskakuje z `MaxValue` na `MinValue` i odwrotnie. Zawijanie ma
sens dla enkodera bez ograniczników — dla pary klawiszy jest pułapką, bo przytrzymanie
przy maksimum nagle gasi światło.

Krok, który wyprowadziłby wartość poza zakres, **dochodzi do granicy**, a nie jest
odrzucany: z `990` przy `StepSize = 50` robi się `1000`, nie `990`.

### 5.3 Przytrzymanie

```
spoczynek ──wciśnięcie klawisza, po DebounceTime──► wciśnięty
                                                      Value ← Value ± StepSize
                                                      emituj Changed

wciśnięty ──po HoldThreshold──► trzymany              (tylko gdy HoldEnabled)
                                  co HoldTickInterval:
                                    Value ← Value ± HoldStepSize
                                    emituj Changed

trzymany  ──zwolnienie──► spoczynek                   (nic nie emituj)
wciśnięty ──zwolnienie──► spoczynek                   (nic nie emituj)
```

**Krok następuje przy wciśnięciu, nie przy zwolnieniu** — i to jest różnica wobec
[`KeyInput`](0x0010-key-input.md) §5.2, która wymaga uzasadnienia, bo tam rozstrzygnięto
odwrotnie.

Powód jest w tym, że tutaj zdarzenie niesie **wartość bezwzględną**. Klawisz musi czekać
na zwolnienie, żeby wiedzieć, czy naciśnięcie było kliknięciem, czy początkiem
przytrzymania — a od tego zależy, które zdarzenie wysłać. Tutaj takiego rozstrzygnięcia
nie ma: pierwszy krok jest ten sam bez względu na to, co stanie się dalej. Czekanie
kosztowałoby więc opóźnienie, nie kupując niczego.

Przy `HoldEnabled = 0` przytrzymanie daje **dokładnie jeden krok**, choćby trwało pięć
sekund.

Przytrzymanie przy `Wrap = 1` trwałoby bez końca, więc obowiązuje ten sam bezpiecznik co
w [`KeyInput`](0x0010-key-input.md) §5.6: **po 60 sekundach trzymania węzeł przestaje
wysyłać zdarzenia** i czeka na zwolnienie. Zaklinowany klawisz nie ma prawa zająć
magistrali.

### 5.4 Zgubione zdarzenie samo się naprawia

Jest to własność, której nie ma wzorzec „`KeyInput` → `Output.Step`", i najmocniejszy
powód, żeby ten typ istniał osobno.

`Changed` niesie **wartość bezwzględną**. Zgubienie jednego zdarzenia znaczy, że jeden
krok nie doszedł — ale następne zdarzenie przynosi liczbę aktualną i obraz się zrasta.
Przy `Step`, który jest względny, ubytki się **kumulują**: po kilku zgubionych ramkach
poziom wyjścia i wskazanie panelu rozjeżdżają się na trwałe i nic ich nie sprowadza
z powrotem.

Dlatego powiązanie oparte na `value` jest odporniejsze niż oparte na `delta`, choć oba
są dopuszczalne (§4).

### 5.5 Zapis z huba nie jest działaniem człowieka

> **Zapis `Value` przez hub zmienia wartość, ale `Changed` nie powstaje.**

Bez tej reguły zrobiłaby się pętla: hub pisze, węzeł ogłasza zmianę, powiązanie każe
hubowi napisać znowu. Reguła „skutek powiązania nie wyzwala kolejnego powiązania"
([`../07-hub.md`](../07-hub.md)) broni przed tym po stronie huba — ta broni po stronie
węzła, czyli także wtedy, gdy zapis przyszedł skądinąd.

Zapis **jest** natomiast raportowany zwyczajnie, przy najbliższym raporcie cyklicznym —
bo to jest zmiana stanu i nowi słuchacze mają ją zobaczyć.

Typowe użycie: ktoś ściemnia światło z telefonu, hub zapisuje ten sam poziom do panelu,
i następne naciśnięcie klawisza rusza **z miejsca, w którym światło naprawdę jest**,
a nie z liczby sprzed godziny.

### 5.6 Trwałość i restart

`Value` przeżywa restart węzła. Zapis do pamięci nieulotnej następuje jednak **dopiero
po ustaniu zmian** — pięć sekund bez ruchu — a nie po każdym kroku. Bez tego jedno
przytrzymanie trwające cztery sekundy kosztowałoby dwadzieścia cykli kasowania.

Po `FactoryReset` wartość wynosi `MinValue`.

Węzeł, który stracił zasilanie w trakcie regulacji, wstaje z wartością sprzed ostatniego
zrzutu. Rozbieżność kasuje pierwszy zapis z huba albo pierwsze naciśnięcie.

### 5.7 Koszt na magistrali

| Sytuacja | Ramki |
|---|---|
| jedno kliknięcie | 1 zdarzenie |
| przytrzymanie 4 s przy ustawieniach domyślnych | 20 zdarzeń, pełny przejazd zakresu |
| raport cykliczny | 1 ramka na `ReportInterval`, domyślnie 300 s |

Raport ze zmiany dokłada się do zdarzeń i **nie jest tłumiony** — ogranicza go wyłącznie
`ReportMinGap`, dla tego typu domyślnie **1000 ms**. Przytrzymanie kosztuje więc pięć
zdarzeń i jeden raport na sekundę, a nie dziesięć wiadomości.

---

## 6. Konfiguracje typowe

| Urządzenie | `Step` | `HoldStep` | `Wrap` | Uwagi |
|---|---|---|---|---|
| Para klawiszy „jaśniej / ciemniej" | 50 ‰ | 50 ‰ | `0` | pełny przejazd w 4 s |
| Enkoder obrotowy | 20 ‰ | — | `0` | `HoldEnabled = 0`, krok na impuls |
| Enkoder bez ograniczników, wybór barwy | 20 ‰ | — | `1` | zawijanie ma tu sens |
| Regulacja głośności | 25 ‰ | 25 ‰ | `0` | `MinValue = 0` — cisza osiągalna |
| Ściemniacz z minimum technicznym | 50 ‰ | 50 ‰ | `0` | `MinValue = 100` — świetlówka nie gaśnie |
| **Ścienne pokrętło zadające °C** | — | — | — | **nie tym typem** — §5.1 |

Klawisze `ValueInput` mogą jednocześnie służyć do czegoś innego: węzeł deklaruje wtedy
dodatkowo endpointy [`KeyInput`](0x0010-key-input.md) na **tym samym kanale**
([`../01-model-danych.md`](../01-model-danych.md) §5), i dwuklik zaczyna wywoływać scenę,
nie ruszając wartości. Ceną są dwa zdarzenia na naciśnięcie zamiast jednego.

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia ten typ na zewnątrz, **nie należy do tej specyfikacji**.
Jedno zalecenie wynika jednak z charakteru samej wartości:

> **`Value` jest intencją, a nie stanem odbiornika.**

Panel pokazuje to, co ustawił człowiek. Czy światło naprawdę świeci z taką jasnością, mówi
wyłącznie atrybut `Level` sterowanego wyjścia ([`Output`](0x0020-output.md) §5.1). Systemy
nadrzędne, które połączą jedno z drugim w jeden suwak, dostaną obiekt kłamiący za każdym
razem, gdy wyjście odmówi wykonania — a odmawia zawsze wtedy, gdy najbardziej interesuje
to użytkownika.
