# Typ endpointu `0x0030` · Sense

> **Stabilne.** Wielkości i skale w [`../registry/quantities.yaml`](../registry/quantities.yaml).
> Wielkości kumulacyjne obsługuje osobny typ [`Meter`](0x0031-meter.md).

**Rewizja 1** · pomiar analogowy

Jedna mierzona wielkość ciągła: temperatura, wilgotność, natężenie światła, stężenie
dwutlenku węgla, ciśnienie, przepływ, napięcie, prąd, moc.

W Matter każda z tych wielkości ma **własny klaster i własny typ urządzenia** — dziewięć
klastrów robiących dokładnie to samo z inną jednostką. Tutaj jest jeden typ, a wielkość
jest jego parametrem.

> **Jeden endpoint mierzy jedną wielkość.** Czujnik BME280 to trzy endpointy `Sense`:
> temperatura, wilgotność, ciśnienie. Nie jest to marnotrawstwo — endpoint jest
> najmniejszą jednostką, która ma osobną nazwę, osobny stan i osobne ustawienia
> raportowania, a te trzy pomiary różnią się we wszystkich trzech aspektach.

Wielkości **skumulowane**, które tylko rosną — energia, objętość wody, ilość gazu —
nie należą tutaj. Obsługuje je typ [`Meter`](0x0031-meter.md) — **`Sense` mierzy,
`Meter` liczy**.

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

| Bit | Cecha | Dokłada |
|---|---|---|
| 0 | `MIN_MAX` | `MinMeasured`, `MaxMeasured`, komenda `ResetMinMax` |
| 1 | `THRESHOLD` | `ThresholdLow`, `ThresholdHigh`, `ThresholdHysteresis`, zdarzenie `Threshold` |
| 2–15 | — | zarezerwowane, nadawaj `0` |

---

## 2. Atrybuty

Typ i skala atrybutów oznaczonych jako `⟨Q⟩` **wynikają z `Quantity`** — tabela wielkości
znajduje się w [`02-typy-danych.md`](../02-typy-danych.md) §3. Dla `TEMPERATURE` jest to
`i16` w setnych stopnia, dla `ILLUMINANCE` — `u32` w setnych luksa.

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `Value` | `⟨Q⟩` | RO | V | **tak** | M | wartość po kalibracji |
| `0x01` | `Quantity` | `enum8` | RO | P | nie | M | §2.3 |
| `0x02` | `MinMeasured` | `⟨Q⟩` | RO | P | nie | `[MIN_MAX]` | minimum od ostatniego zerowania |
| `0x03` | `MaxMeasured` | `⟨Q⟩` | RO | P | nie | `[MIN_MAX]` | maksimum od ostatniego zerowania |

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Domyśl. |
|---|---|---|---|---|---|---|---|
| `0x10` | `Offset` | `i16` | RW | P | nie | O | `0` |
| `0x11` | `ThresholdLow` | `⟨Q⟩` | RW | P | nie | `[THRESHOLD]` | brak |
| `0x12` | `ThresholdHigh` | `⟨Q⟩` | RW | P | nie | `[THRESHOLD]` | brak |
| `0x13` | `ThresholdHysteresis` | `u16` | RW | P | nie | `O [THRESHOLD]` | §5.4 |

Ustawienia raportowania — okres, minimalny odstęp i histereza — są **atrybutami wspólnymi**
`0xF8`–`0xFA` i ten typ ich nie powiela
([`01-model-danych.md`](../01-model-danych.md) §4).

### 2.3 `Quantity`

| Wart. | Nazwa | | Wart. | Nazwa |
|---|---|---|---|---|
| `0x00` | `TEMPERATURE` | | `0x07` | `FLOW` |
| `0x01` | `HUMIDITY` | | `0x08` | `SOIL_MOISTURE` |
| `0x02` | `ILLUMINANCE` | | `0x09` | `VOLTAGE` |
| `0x03` | `CO2` | | `0x0A` | `CURRENT` |
| `0x04` | `VOC` | | `0x0B` | `POWER` |
| `0x05` | `PM25` | | `0x0C` | `DISTANCE` |
| `0x06` | `PRESSURE` | | | |

`Quantity` jest ustawiane przez producenta urządzenia i **nie zmienia się w czasie pracy**.
Zapis jest niedozwolony: czujnik temperatury nie zaczyna nagle mierzyć ciśnienia, a zmiana
tego atrybutu unieważniłaby typ wszystkich pozostałych.

---

## 3. Komendy

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | `ResetMinMax` | — | `[MIN_MAX]` |

Ustawia `MinMeasured` i `MaxMeasured` na bieżącą wartość `Value`. Nie na „brak" — bo
minimum i maksimum z zera pomiarów nie istnieje, a z jednego pomiaru istnieje i jest
poprawne.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Konf. |
|---|---|---|---|---|
| `0x01` | `Threshold` | `zone: enum8`, `value: ⟨Q⟩` | `WARNING` | `[THRESHOLD]` |

`zone`: `0` = `NORMAL`, `1` = `BELOW_LOW`, `2` = `ABOVE_HIGH`.

---

## 5. Zachowanie

### 5.1 Kalibracja

`Value` jest wartością **po dodaniu** `Offset`. Wartość surowa nie jest nigdzie wystawiana.

Powód jest prosty: gdyby oba były widoczne, prędzej czy później ktoś odczytałby nie tę,
co trzeba. Jedna wartość, jedno znaczenie — a `Offset` jest zapisany w węźle i widoczny
dla każdego, kto chce sprawdzić, dlaczego czujnik pokazuje o pół stopnia więcej.

`Offset` ma **stałą jednostkę zgodną z `Quantity`**, więc dla temperatury `-50` znaczy
pół stopnia w dół. Nie ma mnożników ani korekcji wielopunktowej — czujnik, który tego
wymaga, powinien to załatwić wewnętrznie, zanim odda wynik.

### 5.2 Awaria czujnika

Gdy odczyt jest niemożliwy albo niewiarygodny, `Value` przyjmuje **wartość „brak"**
właściwą dla swojego typu ([`02-typy-danych.md`](../02-typy-danych.md) §2.1) i jest
raportowana normalnie.

To rozstrzygnięcie jest istotniejsze, niż wygląda. Milczenie byłoby dwuznaczne — hub nie
odróżniłby zepsutego czujnika od zerwanego kabla ani od węzła, który akurat nic nie wysyła.
Jawna wartość „nie wiem" jest informacją, a cisza nią nie jest.

Zerowanie na `0` przy awarii byłoby błędem znacznie gorszym: termostat dostałby
wiarygodnie wyglądające zero stopni i zacząłby grzać.

`MinMeasured` i `MaxMeasured` **nie uwzględniają** odczytów nieudanych.

### 5.3 Kiedy raportować

| Wyzwalacz | Warunek |
|---|---|
| zmiana | `\|Value − ostatnio raportowana\|` ≥ `ReportHysteresis` (`0xFA`) |
| cyklicznie | upływ `ReportInterval` (`0xF8`), nawet bez zmiany |
| na żądanie | odczyt atrybutu |

Odstęp między raportami nigdy nie jest mniejszy niż `ReportMinGap` (`0xF9`).

**Histereza dotyczy atrybutu `Value` i tylko jego**, w jednostkach wynikających
z `Quantity` ([`../01-model-danych.md`](../01-model-danych.md) §6.2). `MinMeasured`
i `MaxMeasured` nie są raportowane, `Quantity` się nie zmienia — `Value` jest jedynym
atrybutem tego typu, dla którego pojęcie histerezy ma sens.

Histereza jest tu **niezbędna, nie opcjonalna**. Przetwornik dwunastobitowy na wejściu
czujnika temperatury szumi ostatnim bitem bez przerwy; bez histerezy pojedynczy czujnik
nadawałby kilkanaście razy na sekundę, nie mierząc przy tym niczego nowego.

Domyślne histerezy wynikają z wielkości:

| `Quantity` | Domyślna histereza | `ReportInterval` |
|---|---|---|
| `TEMPERATURE` | 0,20 °C | 60 s |
| `HUMIDITY` | 1,00 % | 60 s |
| `ILLUMINANCE` | 50 lx **lub** 10% wartości, co większe | 60 s |
| `CO2` | 30 ppm | 60 s |
| `PRESSURE` | 0,5 hPa | 300 s |
| `POWER` | 5 W | 30 s |
| pozostałe | 1% zakresu | 60 s |

Histereza `ILLUMINANCE` jest **względna**, bo natężenie światła zmienia się o rzędy
wielkości. Bezwzględne 50 luksów jest sensowne w pokoju i bezużyteczne na zewnątrz,
gdzie różnica między 40 000 a 40 050 luksów nikogo nie obchodzi.

### 5.4 Progi

Przy zadeklarowanej cesze `THRESHOLD` czujnik śledzi, w której z trzech stref się znajduje,
i emituje `Threshold` **przy każdym przejściu między nimi** — nie przy każdym pomiarze.

```
                    ThresholdLow          ThresholdHigh
                          │                     │
    BELOW_LOW ────────────┤      NORMAL         ├──────────── ABOVE_HIGH
                          │                     │
    powrót do NORMAL:  Low + Hysteresis   High − Hysteresis
```

`ThresholdHysteresis` zapobiega drganiu na granicy. Bez niej temperatura oscylująca wokół
progu generowałaby zdarzenie po zdarzeniu; z nią wyjście ze strefy wymaga przekroczenia
progu z zapasem.

Histereza progów jest **opcjonalna**, choć same progi są obowiązkowe w cesze. Progi opisują
użycie — przy jakiej temperaturze ktoś chce wiedzieć o mrozie — i ustawia je hub.
Histereza chroni przed szumem czujnika, a ten zna autor urządzenia: urządzenie, które jej
nie wystawia, stosuje własną, stałą wartość
([`../01-model-danych.md`](../01-model-danych.md) §8.1).

Próg pozostawiony bez wartości („brak") jest nieaktywny — można używać samego górnego
albo samego dolnego.

Progi są **niezależne od raportowania**. Czujnik może raportować co minutę i jednocześnie
zgłosić przekroczenie natychmiast po jego wykryciu. To jest właśnie sens ich istnienia:
temperatura kotła przekraczająca granicę jest faktem wymagającym reakcji, a nie kolejnym
punktem na wykresie.

### 5.5 Stan początkowy

Do chwili pierwszego udanego pomiaru `Value` ma wartość „brak" i **nie jest raportowana**.
Śledzenie progów zaczyna się dopiero od pierwszego poprawnego odczytu — inaczej każdy
start węzła generowałby fałszywe `Threshold`.

### 5.6 Co ten czujnik mierzy

`Quantity` mówi, **jaką wielkość** czujnik mierzy. Nie mówi, **czego** ta wielkość dotyczy —
a bez tego pomiar bywa dwuznaczny. Lampka z czujnikiem `ILLUMINANCE` może mierzyć światło
własne, żeby domknąć pętlę ściemniania, albo światło w pomieszczeniu, żeby zgasić się przy
słońcu. Wielkość jest w obu przypadkach ta sama, a znaczenie przeciwne.

Rozstrzyga to atrybut wspólny `0xF5 Channel`
([`../01-model-danych.md`](../01-model-danych.md) §5.1):

> **`Channel = N` na endpoincie `Sense` znaczy: mierzę skutek kanału `N`.**
> **`Channel = 0` znaczy: mierzę coś, czego nie da się przypisać do pojedynczego kanału.**

| Zapis | Znaczy |
|---|---|
| `Output ch1` + `Sense ILLUMINANCE ch1` | czujnik mierzy światło **tej lampy** |
| `Output ch1` + `Sense ILLUMINANCE ch0` | czujnik mierzy światło **w pomieszczeniu** |
| `Output ch1…ch4` + `Sense CURRENT ch2` | pomiar prądu **drugiego kanału** |
| `Output ch1…ch4` + `Sense CURRENT ch0` | pomiar **sumaryczny** całego modułu |

Ostatni wiersz pokazuje, po co `0` brzmi „nie należę do pojedynczego kanału", a nie
„mierzę otoczenie" — uzasadnienie jest w [`../01-model-danych.md`](../01-model-danych.md)
§4.1.

---

## 6. Konfiguracje typowe

| Urządzenie | `Quantity` | Cechy | Uwagi |
|---|---|---|---|
| Czujnik temperatury pomieszczenia | `TEMPERATURE` | `MIN_MAX` | |
| Czujnik temperatury zewnętrznej | `TEMPERATURE` | `MIN_MAX \| THRESHOLD` | próg mrozu |
| Czujnik wilgotności | `HUMIDITY` | `THRESHOLD` | próg kondensacji |
| Czujnik światła | `ILLUMINANCE` | `THRESHOLD` | próg zmierzchu |
| Czujnik jakości powietrza | `CO2` | `THRESHOLD` | próg wietrzenia |
| Pomiar mocy obwodu | `POWER` | `MIN_MAX \| THRESHOLD` | próg przeciążenia |
| Czujnik wilgotności gleby | `SOIL_MOISTURE` | `THRESHOLD` | próg podlewania |
| Temperatura kotła | `TEMPERATURE` | `THRESHOLD` | próg przegrzania |

---

## 7. Reprezentacja poza magistralą

`Quantity` określa jednostkę i skalę — dokładnie to, czego system nadrzędny potrzebuje,
by pokazać wartość i narysować wykres. Więcej informacji nie trzeba.

Jedno zalecenie niezależne od adaptera: **wartość „brak" musi zostać przekazana jako brak,
nie jako zero.** Podstawienie zera w miejsce nieudanego odczytu niweczy całe rozróżnienie
z §5.2 i kończy się wykresem, na którym awaria czujnika wygląda jak nagły mróz.
