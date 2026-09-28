# Typ endpointu `0x0013` · ToggleInput

> **Szkic.** Podział względem `Contact` i `KeyInput` rozstrzygnięty. Typ czeka na pierwsze
> zbudowane urządzenie.

**Rewizja 1** · wejście dwustanowe, którego stan tworzy węzeł

Klawisz chwilowy, którym przełącza się stan **zapamiętany w węźle** — zwykle z diodą
pokazującą ten stan wprost na ścianie. Panel z trzema takimi klawiszami to trzy endpointy
`ToggleInput`, po jednym na klawisz.

> **Czym to się różni od [`Contact`](0x0012-contact.md).** Kontakt **odczytuje** stan ze
> świata: położenie łącznika, otwarte drzwi, wodę na podłodze. Tutaj stan nie istnieje
> nigdzie poza węzłem — powstaje z kliknięć i węzeł jest jego jedynym źródłem.

Dla wyłącznika naściennego rozgraniczenie jest praktyczne i warto je mieć pod ręką:

| Sprzęt na ścianie | Typ | Skąd bierze się stan |
|---|---|---|
| łącznik bistabilny — zostaje w położeniu | [`Contact`](0x0012-contact.md), `Purpose = SWITCH` | z mechaniki |
| klawisz chwilowy z diodą stanu | **`ToggleInput`** | z węzła |
| klawisz chwilowy bez stanu | [`KeyInput`](0x0010-key-input.md) | nie ma stanu |

---

## 1. Cechy

| Bit | Cecha | Dokłada |
|---|---|---|
| — | *(zawsze)* | `State`, `ChangeCount`, `DebounceTime`, zdarzenie `Changed` |
| 0 | `INDICATOR` | `IndicatorMode` |
| 1–15 | — | zarezerwowane, nadawaj `0` |

Obecność diody jest **właściwością sprzętu**, a nie ustawieniem — klawisza bez diody nie da
się przekonfigurować tak, żeby ją miał. Dlatego jest cechą, a `IndicatorMode`, który mówi
tylko, jak ta dioda ma się zachować, jest atrybutem.

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `State` | `bool` | RW | P | **tak** | M | `1` = włączony, §5.1 |
| `0x01` | `ChangeCount` | `u32` | RO | P | nie | O | liczba przełączeń przez całe życie |

`State` jest **zapisywalny** — to jedyny sposób, żeby dioda na ścianie nadążyła za
światłem zgaszonym skądinąd (§5.4).

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `DebounceTime` | `u16` | RW | P | nie | M | 5–100 ms | `15` |
| `0x11` | `IndicatorMode` | `enum8` | RW | P | nie | `[INDICATOR]` | §2.3 | `1` — `FOLLOW` |

### 2.3 `IndicatorMode`

| Wartość | Nazwa | Dioda świeci |
|---|---|---|
| `0` | `OFF` | nigdy |
| `1` | **`FOLLOW`** *(domyślny)* | gdy `State = 1` |
| `2` | `LOCATOR` | gdy `State = 0` |
| `3` | `ALWAYS` | zawsze |

`LOCATOR` odpowiada za najstarsze zastosowanie podświetlanego klawisza: świeci wtedy, gdy
w pomieszczeniu jest ciemno, bo światło jest zgaszone, i gaśnie, gdy przestaje być
potrzebny. `ALWAYS` to podświetlana ramka, która orientuje w korytarzu i nic nie znaczy.

---

## 3. Komendy

**Brak.** `State` jest zapisywalny, więc hub ustawia go zwykłym zapisem atrybutu.

Komenda `Toggle` — przełącz, cokolwiek jest teraz — byłaby tu kusząca i jest niepotrzebna:
hub zna stan każdego takiego wejścia, bo dostaje go zdarzeniem i raportem. Przełączanie
w ciemno ma sens tam, gdzie nadawca stanu nie zna; tutaj zna go zawsze.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Konf. |
|---|---|---|---|---|
| `0x01` | `Changed` | `state: bool` | `INFO` | M |

Emitowane przy każdym przełączeniu **wywołanym przez człowieka**. Zapis z huba zdarzenia
nie tworzy (§5.4).

### 4.1 Dlaczego zdarzenie, skoro jest atrybut

Uzasadnienie jest to samo co w [`ValueInput`](0x0011-value-input.md) §4.1 i wynika z tego,
że oba typy opisują **decyzję sterującą**, a nie obserwację
([`../01-model-danych.md`](../01-model-danych.md) §3): raport jedzie z priorytetem `0x8`
i podlega `ReportMinGap`, a naciśnięcie klawisza nie ma prawa ani czekać w kolejce, ani
zostać stłumione.

Tu widać to szczególnie wyraźnie na tle [`Contact`](0x0012-contact.md), który zdarzeń
**nie ma** i mieć nie powinien:

| | `Contact.State` | `ToggleInput.State` |
|---|---|---|
| Czym jest zmiana | obserwacją świata | **decyzją człowieka** |
| Czy ktoś musi zareagować | nie — stan sam w sobie jest treścią | **tak — światło ma się zapalić** |
| Co znaczy opóźnienie o sekundę | nic | klawisz sprawia wrażenie zepsutego |

> **Przy rozbieżności obowiązuje raport.** Tak samo jak w
> [`Thermostat`](0x0040-thermostat.md) §4.1: zdarzenie może przepaść i nie jest powtarzane,
> a raport wraca cyklicznie i to on rozstrzyga.

---

## 5. Zachowanie

### 5.1 Stan powstaje w węźle

Kliknięcie zmienia `State` na przeciwny. To całe zachowanie i **nie bierze w nim udziału
nikt poza węzłem** — ani hub, ani powiązanie, ani system nadrzędny.

```
State = 0 ──kliknięcie, po DebounceTime──► State = 1
                                             emituj Changed(1)
                                             dioda zgodnie z IndicatorMode

State = 1 ──kliknięcie, po DebounceTime──► State = 0
                                             emituj Changed(0)
                                             dioda zgodnie z IndicatorMode
```

Przytrzymania nie ma. Klawisz trzymany pięć sekund przełącza **raz** — przy wciśnięciu.
Wzorce wymagające przytrzymania obsługuje [`KeyInput`](0x0010-key-input.md); węzeł, który
potrzebuje obu, deklaruje oba endpointy na tym samym kanale
([`../01-model-danych.md`](../01-model-danych.md) §5).

### 5.2 Dlaczego nie `KeyInput` plus `Output` z podświetleniem

Ten sam panel da się opisać jako klawisz i osobne wyjście sterujące diodą — i jest to
rozwiązanie **gorsze o jedną istotną rzecz**: stan mieszka wtedy w hubie.

| | `KeyInput` + `Output INDICATOR` | `ToggleInput` |
|---|---|---|
| Gdzie jest stan | w hubie | w węźle |
| Kto zapala diodę | hub, powiązaniem zwrotnym | węzeł, sam |
| Ramki na jedno kliknięcie | 2 — zdarzenie w górę, komenda w dół | 1 |
| Panel przy nieczynnym hubie | martwy | **działa i pokazuje stan** |
| Powiązań do skonfigurowania na trzy klawisze | 6 | 3 |

Ostatnie dwa wiersze są powodem, dla którego ten typ istnieje. Panel, którego dioda zależy
od huba, przestaje cokolwiek pokazywać w chwili, gdy hub się restartuje — a dokładnie
wtedy człowiek najbardziej potrzebuje wiedzieć, w jakim stanie jest instalacja.

Wariant z `Output INDICATOR` zostaje sensowny tam, gdzie dioda ma pokazywać coś **innego
niż stan własnego klawisza** — na przykład otwarcie bramy sterowanej z drugiego końca domu.

### 5.3 Dioda nie wymaga huba

> **`IndicatorMode` opisuje związek diody z `State` wewnątrz węzła.** Hub nie bierze w nim
> udziału i nie da się go tym związkiem obciążyć.

Jest to najtańsze możliwe rozwiązanie: zero ramek, zero powiązań, zero opóźnienia.
Dioda zmienia się w tej samej milisekundzie co stan, więc klawisz odpowiada natychmiast
nawet wtedy, gdy magistrala jest zajęta.

### 5.4 Zapis z huba przestawia stan, ale nie tworzy zdarzenia

> **Zapis `State` przez hub zmienia stan i diodę, a `Changed` nie powstaje.**

Reguła jest identyczna jak w [`ValueInput`](0x0011-value-input.md) §5.5 i broni przed tą
samą pętlą: hub pisze, węzeł ogłasza, powiązanie każe hubowi napisać znowu.

Typowe użycie jest jednak inne i warto je nazwać wprost. Światło zgaszone z telefonu albo
sceną zostawia klawisz w położeniu „włączony", a dioda świeci nad zgaszoną lampą. Hub
gasi tę rozbieżność jednym zapisem — i dopiero wtedy panel na ścianie znowu mówi prawdę.

**Węzeł nie wymaga tego zapisu do działania.** Bez niego przełącznik jest niezsynchronizowany,
ale w pełni sprawny: następne kliknięcie i tak zmienia stan na przeciwny i wysyła zdarzenie.

### 5.5 Trwałość i restart

`State` przeżywa restart węzła; zapis do pamięci nieulotnej następuje **pięć sekund po
ostatniej zmianie**, nie natychmiast — z tego samego powodu co w
[`ValueInput`](0x0011-value-input.md) §5.6.

Po `FactoryReset` `State` wynosi `0`.

Jest to **odstępstwo od reguły „po starcie stan ma wartość brak"**, którą stosuje
[`Contact`](0x0012-contact.md) §5.5, i odstępstwo świadome. Tam stanu nie wolno zgadywać,
bo pochodzi z pomiaru, którego jeszcze nie było. Tutaj nie ma czego mierzyć — stan jest
tym, co węzeł zapamiętał, i pamięć jest jedynym jego źródłem.

### 5.6 Koszt na magistrali

| Sytuacja | Ramki |
|---|---|
| jedno kliknięcie | 1 zdarzenie + 1 raport |
| raport cykliczny | 1 ramka na `ReportInterval`, domyślnie 300 s |

Raport ze zmiany nie jest tu tłumiony ani histerezą — `bool` jej nie podlega
([`../01-model-danych.md`](../01-model-danych.md) §6.2) — ani w praktyce
`ReportMinGap`, bo klawisza nie da się klikać wystarczająco szybko. Dwie ramki na
kliknięcie są ceną akceptowalną, bo kliknięć jest kilkadziesiąt dziennie, a nie kilkaset
na sekundę.

---

## 6. Konfiguracje typowe

| Urządzenie | Cechy | `IndicatorMode` | Uwagi |
|---|---|---|---|
| Klawisz oświetlenia z diodą | `INDICATOR` | `FOLLOW` | dioda świeci, gdy światło włączone |
| Klawisz w ciemnym korytarzu | `INDICATOR` | `LOCATOR` | świeci, gdy zgaszone — żeby go znaleźć |
| Klawisz z podświetlaną ramką | `INDICATOR` | `ALWAYS` | podświetlenie nic nie znaczy |
| Klawisz bez diody | — | — | cecha niezadeklarowana |
| Trybik „tryb nocny" bez odbiornika | `INDICATOR` | `FOLLOW` | stan czyta wyłącznie automatyka huba |
| **Łącznik bistabilny** | — | — | **nie tym typem** — [`Contact`](0x0012-contact.md) |

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia ten typ na zewnątrz, **nie należy do tej specyfikacji**.
Jedno zalecenie wynika z charakteru stanu:

> **`State` jest intencją człowieka, a nie potwierdzeniem, że coś się stało.**

Klawisz w położeniu „włączony" nad przepaloną żarówką nadal mówi „włączony" — i mówi
prawdę, bo opisuje to, czego chciał człowiek. Czy odbiornik wykonał, mówi wyłącznie
atrybut `OnOff` sterowanego wyjścia ([`Output`](0x0020-output.md) §5.1).

Systemy nadrzędne, które skleją jedno z drugim w jeden przełącznik, dostaną obiekt
kłamiący dokładnie wtedy, gdy coś jest zepsute.
