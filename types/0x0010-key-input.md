# Typ endpointu `0x0010` · KeyInput

> **Stabilne.** Trzy tryby i zdarzenia przytrzymania rozstrzygnięte.

**Rewizja 1** · klawisz chwilowy

Wejście obsługiwane palcem: klawisz monostabilny, przycisk membranowy, pole dotykowe.
Zamienia naciśnięcia na zdarzenia.

> **Klawisz nie ma stanu.** Nie istnieje pytanie „czy klawisz jest teraz wciśnięty".
> Endpoint tego typu emituje wyłącznie zdarzenia, a jedynym atrybutem stanowym jest licznik
> naciśnięć, i to na potrzeby diagnostyki. Rozróżnienie opisuje
> [`01-model-danych.md`](../01-model-danych.md) §3.

**Łącznik bistabilny** — klasyczny wyłącznik, który zostaje w położeniu — **nie należy
tutaj**. Ma stan, więc używa typu [`Contact`](0x0012-contact.md).

---

## 1. Cechy

**Brak.** Wszystko, czym klawisze się różnią, jest konfiguracją zmienną w czasie pracy,
a nie właściwością sprzętu. Klawisz membranowy i pole dotykowe różnią się czasem drgań
styków, a to atrybut, nie cecha.

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | `PressCount` | `u32` | RO | P | nie | O | — | `0` |

`PressCount` zlicza naciśnięcia przez całe życie urządzenia. Służy do diagnostyki zużycia
mechanicznego: klawisz o deklarowanej trwałości miliona cykli, który przekroczył sześćset
tysięcy, warto mieć na oku. Zapis do pamięci trwałej co 64 naciśnięcia, nie po każdym.

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `DebounceTime` | `u16` | RW | P | nie | M | 5–100 ms | `15` |
| `0x11` | `EventMode` | `enum8` | RW | P | nie | M | §2.3 | `0` — `CLICK` |
| `0x12` | `MultiClickWindow` | `u16` | RW | P | nie | M | 150–800 ms | `350` |
| `0x13` | `MaxClicks` | `u8` | RW | P | nie | M | 2–5 | `3` |
| `0x14` | `HoldEnabled` | `bool` | RW | P | nie | M | — | `1` |
| `0x15` | `HoldThreshold` | `u16` | RW | P | nie | M | 200–3000 ms | `500` |
| `0x16` | `HoldTickInterval` | `u16` | RW | P | nie | M | 50–1000 ms | `200` |
| `0x17` | `Invert` | `bool` | RW | P | nie | O | — | `0` |

### 2.3 `EventMode`

| Wartość | Nazwa | Emituje | Kiedy | Opóźnienie reakcji |
|---|---|---|---|---|
| `0` | **`CLICK`** *(domyślny)* | `Click(1)` | po zwolnieniu | czas trzymania palca, typowo 80–150 ms |
| `1` | `MULTICLICK` | `Click(1…MaxClicks)` | po zwolnieniu i oknie | j.w. + `MultiClickWindow`, czyli 350 ms |
| `2` | `RAW` | `Down`, `Up(czas)` | przy wciśnięciu i zwolnieniu | `DebounceTime` — 15 ms |

Tryb ustawia się osobno dla każdego klawisza. Trzyklawiszowy panel może mieć dwa
klawisze w trybie `CLICK` do świateł i jeden w `MULTICLICK` do scen.

Zdarzenia przytrzymania (`HoldStart`, `HoldTick`, `HoldEnd`) są **niezależne od trybu** —
włącza je `HoldEnabled` i działają we wszystkich trzech.

---

## 3. Komendy

**Brak.** Klawisz niczego nie przyjmuje — jest wyłącznie źródłem zdarzeń.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Tryby |
|---|---|---|---|---|
| `0x01` | `Down` | — | `INFO` | `RAW` |
| `0x02` | `Up` | `duration: u16` [ms] | `INFO` | `RAW` |
| `0x03` | `Click` | `count: u8` | `INFO` | `CLICK`, `MULTICLICK` |
| `0x05` | `HoldStart` | — | `INFO` | wszystkie, gdy `HoldEnabled` |
| `0x06` | `HoldTick` | `elapsed: u16` [ms] | `INFO` | wszystkie, gdy `HoldEnabled` |
| `0x07` | `HoldEnd` | `elapsed: u16` [ms] | `INFO` | wszystkie, gdy `HoldEnabled` |

---

## 5. Zachowanie

### 5.1 Dlaczego `Click` jest domyślne

Automatykę pisze się najłatwiej, gdy klawisz produkuje **jedno zdarzenie**. Reguła
„`Click` → przełącz światło" jest kompletna i nie wymaga rozumienia, czym różni się
naciśnięcie od zwolnienia ani co się dzieje, gdy ktoś przytrzyma.

`Down` i `Up` są potrzebne rzadko — przy sterowaniu wymagającym dokładnego czasu albo
reakcji na samo puszczenie. Dlatego siedzą w trybie `RAW`, po który sięga się świadomie.

`Click` jest **tym samym zdarzeniem we wszystkich trybach, w których występuje**, więc
przejście z `CLICK` na `MULTICLICK` nie unieważnia istniejących reguł: `Click(1)` nadal
przychodzi, tyle że później, a dochodzi możliwość `Click(2)` i `Click(3)`.

### 5.2 `Click` powstaje przy zwolnieniu

Kliknięcie to **naciśnięcie i puszczenie**, więc zdarzenie powstaje dopiero wtedy, gdy
oba się dokonały. Nie da się nazwać kliknięciem czegoś, co jeszcze trwa.

Ma to trzy dobre konsekwencje:

1. **Przytrzymanie nie emituje `Click`.** Krótkie naciśnięcie daje `Click(1)`, długie daje
   `HoldStart` i `HoldEnd` — i nic poza tym. Nie ma dublowania ani zdarzeń, które trzeba
   potem odfiltrować w regułach.
2. **`CLICK` i `MULTICLICK` zachowują się tak samo.** W obu `Click` przychodzi po
   zwolnieniu; tryby różnią się już tylko tym, czy czekamy jeszcze na kolejne naciśnięcie.
3. **`Click` i `Down` przestają być tym samym.** Gdyby `Click` leciał przy wciśnięciu,
   byłby zwykłym `Down` pod inną nazwą, a granica między trybami zrobiłaby się umowna.

Kosztem jest **zmienne opóźnienie**: reakcja przychodzi po tym, jak długo ktoś trzyma
palec, czyli typowo 80–150 ms zamiast 15 ms. Dla oświetlenia jest to niezauważalne,
bo mieści się poniżej progu, przy którym człowiek odbiera reakcję jako opóźnioną.

Gdy potrzebna jest **reakcja najszybsza z możliwych i o stałym czasie** — sterowanie
czymś, co musi ruszyć dokładnie w chwili dotknięcia — służy do tego tryb `RAW`
i reguła na `Down` (§5.5). To jest właśnie powód, dla którego ten tryb istnieje.

### 5.3 Tryb `CLICK` — domyślny

```
zwolniony ──wciśnięcie, po DebounceTime──► wciśnięty      (nic nie emituj)

wciśnięty ──zwolnienie──► zwolniony
                            emituj Click(1)

wciśnięty ──po HoldThreshold──► trzymany                  (tylko gdy HoldEnabled)
                                  emituj HoldStart
                                  potem HoldTick(czas) co HoldTickInterval

trzymany  ──zwolnienie──► zwolniony
                            emituj HoldEnd(czas trzymania)      ← bez Click
```

Naciśnięcie zakończone zwolnieniem przed upływem `HoldThreshold` daje `Click(1)`.
Naciśnięcie dłuższe przechodzi w przytrzymanie i **nie daje `Click` w ogóle**.

Przy `HoldEnabled = 0` nie ma przejścia do stanu trzymanego, więc `Click(1)` powstaje
przy zwolnieniu **niezależnie od czasu trzymania**. Klawisz przytrzymany pięć sekund
wyśle `Click(1)` po pięciu sekundach.

Typowe sterowanie ściemnialnym światłem wygląda więc tak: krótkie naciśnięcie przełącza
(`Click` → `Toggle`), przytrzymanie reguluje jasność (`HoldTick` → `Step`). Dwie reguły,
zero nakładania się.

### 5.4 Tryb `MULTICLICK`

```
zwolniony ──wciśnięcie, po DebounceTime──► wciśnięty     (nic nie emituj)

wciśnięty ──zwolnienie──► oczekiwanie
                            licznik ← licznik + 1
                            uruchom zegar MultiClickWindow

oczekiwanie ──kolejne wciśnięcie──► wciśnięty
                                      zatrzymaj zegar

oczekiwanie ──upływ MultiClickWindow──► zwolniony
                                          emituj Click(licznik)
                                          licznik ← 0

wciśnięty ──po HoldThreshold──► trzymany
                                  licznik ← 0        ← sekwencja anulowana
                                  emituj HoldStart, potem HoldTick
```

Rozpoznanie dwukliku **wymaga odczekania** `MultiClickWindow` po zwolnieniu — inaczej nie
wiadomo, czy kliknięcie było ostatnie. Tej ceny nie da się uniknąć: klawisz w tym trybie
reaguje po 350 ms zamiast po 15 ms.

Po osiągnięciu `MaxClicks` klawisz **nie czeka** na upływ okna — emituje `Click` od razu.
Bez tego pięciokrotne kliknięcie przy `MaxClicks = 3` byłoby nierozpoznawalne, a tak daje
`Click(3)` i zaczyna liczyć od nowa.

Przytrzymanie **anuluje** rozpoczętą sekwencję. Wzorzec „dwuklik i przytrzymaj" nie jest
w tej rewizji obsługiwany; gdyby był potrzebny, `HoldStart` dostanie parametr z liczbą
poprzedzających kliknięć — pole jest na to zarezerwowane.

### 5.5 Tryb `RAW`

```
zwolniony ──wciśnięcie, po DebounceTime──► wciśnięty
                                             emituj Down

wciśnięty ──zwolnienie──► zwolniony
                            emituj Up(czas trzymania)

wciśnięty ──po HoldThreshold──► trzymany
                                  emituj HoldStart, potem HoldTick

trzymany  ──zwolnienie──► zwolniony
                            emituj HoldEnd(czas trzymania)
```

**Zwolnienie emituje dokładnie jedno zdarzenie**: `Up` albo `HoldEnd`, nigdy oba. Dzięki
temu reguła na `Up` nie odpala się po przytrzymaniu, a obie niosą czas trzymania.

Tryb `RAW` ma dwie właściwości, których nie ma żaden inny:

- **`Down` przychodzi po `DebounceTime`**, czyli po 15 ms i zawsze po tym samym czasie.
  To jedyna droga do reakcji szybszej niż czas trzymania palca.
- **Widać samo zwolnienie.** `Up` niesie czas trzymania i pozwala reagować na puszczenie,
  czego `Click` nie umożliwia.

Ceną jest dwukrotnie większy ruch na magistrali — dwa zdarzenia na naciśnięcie zamiast
jednego. Przy pojedynczym klawiszu bez znaczenia, przy panelu z ośmioma warto wiedzieć.

### 5.6 Przytrzymanie

`HoldTick` powtarza się co `HoldTickInterval`, niosąc łączny czas trzymania. To jest
mechanizm ściemniania: reguła `HoldTick → Step(+50‰)` daje płynną regulację, a `Step`
nasyca się na `MinLevel`, więc przytrzymanie nigdy nie zgasi lampy
([`Output`](0x0020-output.md) §5.2).

`HoldEnabled = 0` wyłącza całą trójkę zdarzeń we wszystkich trybach.

Przy `HoldTickInterval = 200 ms` przytrzymanie przez pięć sekund to 25 ramek. Klawisz
trzymany bardzo długo generuje ruch bez końca, więc **po 60 sekundach trzymania węzeł
przestaje wysyłać `HoldTick`** i czeka na zwolnienie. Zablokowany mechanicznie klawisz —
zaklinowany, zalany, przyciśnięty meblem — nie ma prawa zająć magistrali.

### 5.7 Drgania styków i inwersja

`DebounceTime` liczy się od **pierwszej** zmiany poziomu; kolejne zmiany w tym oknie są
ignorowane. Zdarzenie powstaje na końcu okna, jeśli poziom się utrzymał.

`Invert = 1` dla klawiszy zwierających do zasilania zamiast do masy. Dotyczy wyłącznie
odczytu wejścia — zdarzenia zawsze opisują **palec na klawiszu**, nie poziom elektryczny.

### 5.8 Zdarzenia zgubione

Zdarzenia są rozgłaszane raz i nie mają wartości bieżącej. Odbiorca, który był offline
w chwili naciśnięcia, nie ma jak się o nim dowiedzieć — nie istnieje mechanizm
nadrobienia zaległości.

Dlatego zdarzenia mają na magistrali wyższy priorytet niż raporty stanu, a odbiorca,
który wykryje dziurę w liczniku zdarzeń, **loguje ubytek, ale wykonuje zdarzenie
bieżące**. Odtwarzanie przeszłości jest zabronione: zapalenie światła pół minuty po
naciśnięciu jest gorsze niż niezapalenie go wcale.

---

## 6. Konfiguracje typowe

| Zastosowanie | `EventMode` | `Hold` | Uwagi |
|---|---|---|---|
| Klawisz oświetlenia | `CLICK` | `1` | `Click` przełącza, przytrzymanie ściemnia |
| Klawisz sceny | `MULTICLICK` | `0` | `Click(1)`, `Click(2)`, `Click(3)` |
| Klawisz „wychodzę z domu" | `MULTICLICK` | `1` | dwuklik gasi wszystko, przytrzymanie uzbraja |
| Dzwonek do drzwi | `CLICK` | `0` | jedno zdarzenie na naciśnięcie |
| Pole dotykowe | `CLICK` | `1` | `DebounceTime` = 30 ms |
| Sterowanie bramą „trzymaj aby jechać" | `RAW` | `0` | brama jedzie między `Down` a `Up` |
| Klawisz wymagający natychmiastowej reakcji | `RAW` | `0` | reguła na `Down`, stałe 15 ms |

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia klawisz na zewnątrz, **nie należy do tej specyfikacji**.
Warto natomiast zapisać jedno zalecenie, bo wynika z charakteru zdarzeń, a nie z wyboru
adaptera:

> **`HoldTick` nie powinien opuszczać huba.**

Przy domyślnych ustawieniach to pięć zdarzeń na sekundę na każdy trzymany klawisz.
Systemy nadrzędne zwykle zapisują każde zdarzenie w historii, więc kilkusekundowe
ściemnianie zaśmieciłoby bazę setkami wpisów, z których żaden nikogo nie interesuje.

Znaczenie ma **wynik** ściemniania, czyli poziom raportowany przez typ
[`Output`](0x0020-output.md), a nie przebieg dochodzenia do niego. `HoldStart` i `HoldEnd`
warto przekazać — to są fakty o intencji użytkownika.
