# Typ endpointu `0x0012` · Contact

> **Stabilne.** Rewizja 1 zamknięta. Od 2026-10-13 odbicie i polaryzacja są opcjonalne —
> wystawia je moduł, do którego instalator podłącza czujnik.

**Rewizja 1** · wejście dwustanowe ze stanem

Wszystko, co jest albo zwarte, albo rozwarte, i **zostaje w tym położeniu**: kontaktron
drzwiowy, czujka zalania, wyjście przekaźnikowe czujki dymu, czujnik ruchu, klasyczny
łącznik bistabilny.

> **Contact ma stan, `KeyInput` nie ma.** To jest jedyne kryterium podziału. Klawisz chwilowy
> wraca sam do położenia spoczynkowego, więc pytanie „czy jest teraz wciśnięty" nie ma
> sensu i typ [`KeyInput`](0x0010-key-input.md) emituje wyłącznie zdarzenia. Kontakt trwa
> w swoim stanie, więc da się go odczytać w dowolnej chwili.

Praktyczna konsekwencja: **klasyczny wyłącznik naścienny należy tutaj, nie do `KeyInput`.**
Po przestawieniu zostaje w położeniu, więc niesie stan.

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

**Brak.** Wszystkie warianty zastosowania obsługuje atrybut `Purpose` (§2.3), który nie
zmienia zachowania typu, a jedynie znaczenie jego stanu.

**Odbicie i polaryzacja są opcjonalne, bo zależą od tego, co jest podłączone.** Urządzenie
z czujnikiem wbudowanym — czujka zalania z własnymi elektrodami, kontaktron w obudowie —
zna je z budowy i ustala samo. Moduł z zaciskami nie wie, czy instalator przykręci
kontaktron zwierny czy rozwierny, ani czy krańcówka bramy drga dwie sekundy; taki moduł
**powinien** wystawiać `DebounceTime` i `Invert`, bo wartość zna dopiero instalator
([`../01-model-danych.md`](../01-model-danych.md) §8.1).

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `State` | `bool` | RO | V | **tak** | M | `1` = stan czynny, §5.1 |
| `0x01` | `ChangeCount` | `u32` | RO | P | nie | O | liczba zmian przez całe życie |

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `DebounceTime` | `u16` | RW | P | nie | O | 5–10000 ms | `50` |
| `0x11` | `Invert` | `bool` | RW | P | nie | O | — | `0` |
| `0x12` | `Purpose` | `enum8` | RW | P | nie | M | §2.3 | `0` |
| `0x13` | `HoldTime` | `u16` | RW | P | nie | O | 0–65534 s | `0` |

### 2.3 `Purpose`

Czym ten kontakt jest dla mieszkańca. Nie zmienia zachowania typu o jotę — niesie
wyłącznie znaczenie, którego sam sygnał elektryczny nie ma. Zwarcie na wejściu to zwarcie;
dopiero `Purpose` mówi, czy znaczy ono „otwarte okno", czy „woda na podłodze".

| Wartość | Nazwa | `State = 1` znaczy |
|---|---|---|
| `0` | `GENERIC` | zwarte |
| `1` | `DOOR` | drzwi otwarte |
| `2` | `WINDOW` | okno otwarte |
| `3` | `MOTION` | wykryto ruch |
| `4` | `OCCUPANCY` | pomieszczenie zajęte |
| `5` | `WATER_LEAK` | **wykryto zalanie** |
| `6` | `SMOKE` | **wykryto dym** |
| `7` | `CO` | **wykryto tlenek węgla** |
| `8` | `GAS` | **wykryto gaz** |
| `9` | `TAMPER` | naruszono obudowę |
| `10` | `SWITCH` | łącznik w położeniu włączonym |
| `11` | `GARAGE_DOOR` | brama otwarta |

Wartości `5`–`9` są **stanami alarmowymi**. Wpływa to na sposób raportowania (§5.4).

### 2.4 `HoldTime`

Minimalny czas, przez jaki stan czynny jest podtrzymywany po ustaniu pobudzenia.
Dopóki nie upłynie, `State` pozostaje `1`, choćby wejście już dawno wróciło do spoczynku.

Wartość `0` wyłącza podtrzymanie: `State` odwzorowuje wejście jeden do jednego.

Bez tego czujnik ruchu jest bezużyteczny. Typowy moduł PIR daje impuls na sekundę lub dwie
przy każdym wykryciu, więc człowiek siedzący w pokoju generuje serię krótkich pobudzeń
z przerwami. `HoldTime = 300` zamienia je w jeden ciągły stan „pomieszczenie zajęte",
a magistrala widzi dwie zmiany zamiast czterdziestu.

Każde kolejne pobudzenie **zeruje odliczanie** — stan gaśnie dopiero po `HoldTime` od
ostatniego, nie od pierwszego.

---

## 3. Komendy

**Brak.** Kontakt jest wejściem; niczego nie przyjmuje.

---

## 4. Zdarzenia

**Brak.** Kontakt ma stan, więc każda zmiana jest raportem atrybutu `State`. Dokładanie
zdarzenia opisującego to samo dawałoby dwa opisy jednego faktu, które mogłyby się rozjechać
([`01-model-danych.md`](../01-model-danych.md) §3).

Wyjątek od tej reguły przysługuje wyłącznie typom, w których zmiana stanu jest **decyzją
sterującą** — i dlatego nie przysługuje tutaj. Zmiana kontaktu jest obserwacją: nikt nią
niczego nie postanawia, a spóźniony o sekundę raport o otwartym oknie nikomu nie przeszkadza.
Wejście, w którym ten sam bit jest decyzją człowieka, to
[`ToggleInput`](0x0013-toggle-input.md) — i ono zdarzenie ma.

---

## 5. Zachowanie

### 5.1 Stan czynny

`State = 1` znaczy **stan czynny**, nie „napięcie wysokie". Czym jest stan czynny, mówi
`Purpose`; jak odwzorować go na poziom elektryczny, mówi `Invert` — albo budowa urządzenia.

Rozdzielenie tych trzech rzeczy jest celowe. Kontaktron drzwiowy bywa zwierny albo
rozwierny, zależnie od modelu i od tego, jak go ktoś przykręcił — ale `State = 1` ma
zawsze znaczyć „drzwi otwarte", niezależnie od tego, co się dzieje na wejściu. Instalator
ustawia `Invert` raz i nikt więcej nie musi o tym pamiętać.

Urządzenie bez atrybutu `Invert` odwzorowuje poziom na stan czynny samo — wie, jak
zbudowało wejście, i `State = 1` znaczy u niego to samo co u każdego innego.

Czujki bezpieczeństwa mają **stan czynny odpowiadający zagrożeniu**: `State = 1` to dym,
zalanie albo gaz. Nigdy odwrotnie, choćby fizyczne wyjście czujki działało w drugą stronę.

### 5.2 Drgania styków

Czas odbicia — z atrybutu `DebounceTime` albo ustalony przez urządzenie, które go nie
wystawia — liczy się od **pierwszej** zmiany poziomu; kolejne zmiany w tym oknie są
ignorowane, a stan uznaje się za ustalony na końcu okna.

Zakres sięga dziesięciu sekund — znacznie dalej niż drgania klawisza, które trwają
milisekundy. Powód jest praktyczny: kontaktron w bramie garażowej albo pływak w studzience potrafi drgać całymi
sekundami przy każdym poruszeniu. Filtrowanie tego w węźle jest o wiele tańsze niż
przesyłanie kilkudziesięciu zmian na magistralę.

### 5.3 Raportowanie

`State` jest raportowany przy każdej zmianie oraz cyklicznie, zgodnie z atrybutami
wspólnymi `0xF8`–`0xF9`. Odświeżanie cykliczne ma tu szczególne znaczenie: **stan kontaktu
jest informacją, która musi być prawdziwa także po restarcie huba**, a odczyt czterdziestu
kontaktronów po każdym restarcie jest gorszy niż odczekanie jednego okresu.

Domyślny `ReportInterval` dla tego typu wynosi 300 s.

### 5.4 Wejścia alarmowe

Przy `Purpose` z zakresu `5`–`9` obowiązują dwie dodatkowe reguły:

- **`ReportMinGap` nie ogranicza przejścia w stan czynny.** Ograniczanie częstotliwości
  ma chronić magistralę przed szumem, nie opóźniać sygnał o pożarze. Ograniczenie działa
  nadal przy powrocie do spoczynku.
- **Raport stanu czynnego ma podwyższony priorytet na magistrali.** Szczegóły należą do
  rozdziału o mapowaniu na CAN; tutaj wystarczy zapisać, że wykrycie dymu nie może czekać
  w kolejce za odczytem temperatury.

### 5.5 Stan początkowy

Do chwili pierwszego ustalonego odczytu `State` ma wartość „brak"
([`02-typy-danych.md`](../02-typy-danych.md) §2.1) i **nie jest raportowany**.

Zerowanie stanu na `0` po starcie byłoby błędem: węzeł zgłosiłby wtedy „brak dymu"
w chwili, gdy jeszcze nie zdążył niczego zmierzyć, a hub uznałby to za wiarygodną
informację.

---

## 6. Konfiguracje typowe

| Zastosowanie | `Purpose` | `Debounce` | `HoldTime` | Uwagi |
|---|---|---|---|---|
| Kontaktron drzwiowy | `DOOR` | 50 ms | 0 | |
| Kontaktron okienny | `WINDOW` | 50 ms | 0 | |
| Czujnik ruchu PIR | `MOTION` | 100 ms | 60 s | |
| Czujnik obecności | `OCCUPANCY` | 100 ms | 300 s | |
| Czujka zalania | `WATER_LEAK` | 500 ms | 0 | dłuższy debounce — chlapnięcie to nie zalanie |
| Czujka dymu | `SMOKE` | 100 ms | 0 | |
| Łącznik bistabilny | `SWITCH` | 20 ms | 0 | zwykły wyłącznik naścienny |
| Krańcówka bramy | `GARAGE_DOOR` | 2000 ms | 0 | mechanika drga długo |

---

## 7. Reprezentacja poza magistralą

Hub dostaje z tego typu dwie informacje: `Purpose` mówi, **co** ten kontakt oznacza,
a `State` mówi, **jak jest teraz**. To wystarcza do zbudowania dowolnej reprezentacji
w systemie nadrzędnym.

Warto natomiast zapisać zalecenie niezależne od wybranego adaptera: **stan czynny wejść
alarmowych powinien docierać na zewnątrz osobną, wyróżnioną drogą.** Zalanie i dym to
jedyne rzeczy w całej instalacji, których przegapienie kosztuje więcej niż niewygodę.
