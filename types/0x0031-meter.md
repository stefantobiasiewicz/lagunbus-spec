# Typ endpointu `0x0031` · Meter

> **Stabilne.** Rewizja 1 zamknięta.

**Rewizja 1** · licznik kumulacyjny

Zlicza to, co **przez coś przepłynęło i nie wraca**: energię elektryczną, wodę, gaz,
ciepło. Wartość rośnie przez całe życie instalacji i nigdy nie maleje.

> **`Meter` liczy, [`Sense`](0x0030-sense.md) mierzy.** Licznik wody i pomiar przepływu to
> dwie różne rzeczy: pierwszy odpowiada na „ile zużyliśmy od stycznia", drugi na „ile leci
> teraz". Moduł, który umie jedno i drugie, ma dwa endpointy — i jest to właściwy podział,
> bo te wartości mają inne skale, inne tempo zmian i inne ustawienia raportowania.

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
| — | *(rdzeń typu, zawsze)* | `Imported`, opcjonalnie `ImportedOffset` |
| 0 | `EXPORT` | `Exported`, opcjonalnie `ExportedOffset` |
| 1–15 | — | zarezerwowane, nadawaj `0` |

`EXPORT` deklaruje licznik dwukierunkowy. Wodomierz i gazomierz jej nie mają — woda nie
wraca do wodociągu. Licznik energii w instalacji z fotowoltaiką ma.

---

## 2. Atrybuty

Typ i skala atrybutów oznaczonych `⟨Q⟩` **wynikają z `Quantity`** — tabela wielkości
znajduje się w [`../02-typy-danych.md`](../02-typy-danych.md) §3.

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `Imported` | `⟨Q⟩` | RO | **P** | **tak** | M | pobrane przez instalację |
| `0x01` | `Exported` | `⟨Q⟩` | RO | **P** | **tak** | `[EXPORT]` | oddane na zewnątrz |
| `0x02` | `Quantity` | `enum8` | RO | P | nie | M | §2.3 |

Oba liczniki są **trwałe** — to jedyne atrybuty stanu w całej specyfikacji, które muszą
przeżyć zanik zasilania. Licznik, który zeruje się przy każdym mrugnięciu prądu, nie jest
licznikiem.

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `ImportedOffset` | `u32` | RW | P | nie | O | — | `0` |
| `0x11` | `ExportedOffset` | `u32` | RW | P | nie | `O [EXPORT]` | — | `0` |
| `0x12` | `Purpose` | `enum8` | RW | P | nie | M | §2.4 | `0` |

### 2.3 `Quantity`

| Wartość | Nazwa | Typ | Skala | Jednostka |
|---|---|---|---|---|
| `0x00` | `ENERGY` | `u32` | 1 | `Wh` |
| `0x01` | `VOLUME` | `u32` | 1 | `L` |

Ustawiane przez producenta i **niezmienne w czasie pracy** — licznik wody nie zaczyna nagle
liczyć kilowatogodzin.

Przy trzydziestu dwóch bitach i skali jednej watogodziny licznik przepełni się po 4,29 GWh,
czyli po jakichś ośmiuset latach zużycia typowego domu. Przy litrach — po 4,29 miliarda
litrów, czyli po kilkudziesięciu tysiącach lat. **Przepełnienia nie trzeba obsługiwać
i specyfikacja go nie przewiduje.**

### 2.4 `Purpose`

`Quantity` mówi, **co** jest liczone; `Purpose` — **czego to dotyczy**. Bez tego woda
i gaz są nieodróżnialne, bo obie są objętością w litrach.

| Wartość | Nazwa | Typowe `Quantity` |
|---|---|---|
| `0` | `GENERIC` | — |
| `1` | `ELECTRICITY` | `ENERGY` |
| `2` | `WATER` | `VOLUME` |
| `3` | `GAS` | `VOLUME` |
| `4` | `HEAT` | `ENERGY` |

`Purpose` nie zmienia zachowania typu ani o jotę — niesie wyłącznie intencję, tak jak
w [`Output`](0x0020-output.md) §2.4 i [`Contact`](0x0012-contact.md) §2.3.

---

## 3. Komendy

**Brak.** Licznika nie da się wyzerować komendą i jest to zamierzone: wartość licznika jest
podstawą rozliczeń, a komenda kasująca ją byłaby jedną ramką dzielącą od utraty historii
całego roku.

Do wyrównania wskazania z licznikiem fizycznym służy `ImportedOffset` (§5.3), a do
skasowania wszystkiego — `FactoryReset`, który kasuje też całą resztę konfiguracji
i wymaga argumentu zabezpieczającego ([`0x0001-device.md`](0x0001-device.md) §3.3).

---

## 4. Zdarzenia

**Brak.** Licznik ma stan, nie fakty. Wszystko, co się z nim dzieje, widać w raportach
([`../01-model-danych.md`](../01-model-danych.md) §3).

---

## 5. Zachowanie

### 5.1 Kierunek jest atrybutem, nie osobnym endpointem

> **Energia pobrana i oddana to dwa atrybuty jednego endpointu.**

Wcześniejsze wydanie [`../02-typy-danych.md`](../02-typy-danych.md) zapowiadało dwa osobne
endpointy. Było to nie do utrzymania, bo **łamało regułę rozróżnialności**
([`../01-model-danych.md`](../01-model-danych.md) §2.2): dwa endpointy `Meter` o tej samej
wielkości, na tym samym kanale, niczym by się nie różniły. Hub nie miałby jak odgadnąć,
który jest który.

Jest też powód prostszy. Licznik dwukierunkowy to **jedno urządzenie z jednym przyłączem** —
mierzy ten sam przepływ w dwie strony. Dwa endpointy sugerowałyby dwie rzeczy fizyczne,
czyli dokładnie to, czemu zapobiega `Channel`
([`../01-model-danych.md`](../01-model-danych.md) §5).

Licznik jednokierunkowy nie deklaruje cechy `EXPORT` i ma po prostu jeden atrybut. Nie ma
sytuacji, w której `Exported` istnieje i jest bez znaczenia.

### 5.2 Wartość nigdy nie maleje

Poza jednym wyjątkiem: `FactoryReset` zeruje oba liczniki razem z resztą konfiguracji.

> **Spadek wartości licznika oznacza, że urządzenie zostało wyzerowane albo wymienione.**
> Hub ma to wykryć i **nie wolno mu policzyć różnicy ujemnej ani gigantycznej.**

Jest to jedyna rzecz, o którą hub musi zadbać sam, bo węzeł nie ma jak odróżnić własnego
zerowania od wymiany modułu — a różnica między dwoma odczytami jest podstawą każdego
rozliczenia, jakie ktokolwiek z tych danych zrobi.

### 5.3 `Offset` wyrównuje wskazanie

Wartość raportowana jest sumą **wewnętrznego licznika i offsetu**. Wartość surowa nie jest
nigdzie wystawiana — jedna wartość, jedno znaczenie, tak jak w [`Sense`](0x0030-sense.md) §5.1.

Po co: moduł zliczający impulsy z wodomierza, którego tarcza pokazuje już 1234 m³, ustawia
`ImportedOffset = 1234000` i od tej chwili raportuje to samo, co widać na liczniku. Bez tego
każdy odczyt wymagałby dodawania po stronie huba, a wartość w węźle nie znaczyłaby nic.

Ten sam mechanizm służy po wymianie modułu: nowy zaczyna od zera, a offset przywraca
ciągłość.

Oba przesunięcia są **opcjonalne**, każde na swoim liczniku. Wyrównanie z tarczą jest
sprawą instalacji — licznik impulsowy podłączony do starego wodomierza go potrzebuje,
licznik energii z własnym pomiarem od nowości nie ma czego wyrównywać.

**Zapis `Offset` nie jest zerowaniem.** Licznik biegnie dalej od swojej wartości; zmienia
się tylko to, co jest do niej dodawane.

### 5.4 Zapis do pamięci trwałej

Licznik musi przeżyć zanik zasilania, ale **nie wolno go zapisywać przy każdej zmianie** —
pamięć nieulotna ma skończoną liczbę cykli, a licznik energii zmienia się setki razy
dziennie.

> Zapis **nie częściej niż raz na dziesięć minut** i dodatkowo przed zaplanowanym restartem.

Ceną jest utrata co najwyżej dziesięciu minut zliczania przy nagłym zaniku zasilania. Jest
to cena właściwa: dziesięć minut zużycia jest błędem pomijalnym, a wypalona komórka pamięci
kończy życie urządzenia.

Węzeł, który potrafi wykryć zanik zasilania z wyprzedzeniem, powinien zapisać licznik wtedy.

### 5.5 Raportowanie

Licznik rośnie bez przerwy, więc raportowanie każdej zmiany zalałoby magistralę. Obowiązuje
zwykły mechanizm ([`../01-model-danych.md`](../01-model-danych.md) §6) z histerezą wyrażoną
w jednostkach licznika.

| `Purpose` | Domyślna histereza | `ReportInterval` |
|---|---|---|
| `ELECTRICITY` | 10 Wh | 300 s |
| `WATER`, `GAS` | 1 L | 900 s |
| `HEAT` | 100 Wh | 900 s |

Odświeżanie cykliczne jest tu ważniejsze niż gdzie indziej: hub po restarcie musi odzyskać
stan licznika, a odczytanie go z opóźnieniem nie szkodzi, bo wartość i tak nie maleje.

### 5.6 Stan początkowy

Po starcie licznik ma wartość odtworzoną z pamięci trwałej i **jest raportowany od razu** —
inaczej niż w [`Sense`](0x0030-sense.md) §5.5, gdzie do pierwszego pomiaru obowiązuje
wartość „brak".

Różnica bierze się stąd, że licznik nie musi niczego zmierzyć, żeby znać swoją wartość.
Wartość „brak" pojawia się tu tylko wtedy, gdy pamięć trwała jest uszkodzona i węzeł nie wie,
ile naliczył.

---

## 6. Konfiguracje typowe

| Urządzenie | `Quantity` | `Purpose` | Cechy | Uwagi |
|---|---|---|---|---|
| Licznik energii, jednokierunkowy | `ENERGY` | `ELECTRICITY` | — | |
| Licznik energii z fotowoltaiką | `ENERGY` | `ELECTRICITY` | `EXPORT` | dwa kierunki, jeden endpoint |
| Wodomierz impulsowy | `VOLUME` | `WATER` | — | `ImportedOffset` z tarczy |
| Gazomierz impulsowy | `VOLUME` | `GAS` | — | |
| Ciepłomierz | `ENERGY` | `HEAT` | — | |
| Pomiar mocy chwilowej | — | — | — | **to nie jest `Meter`** — użyj `Sense` z `POWER` |

Ostatni wiersz jest tam celowo: najczęstsza pomyłka przy tym typie to próba zmieszczenia
w nim wartości chwilowej.

---

## 7. Reprezentacja poza magistralą

`Quantity` daje jednostkę, `Purpose` — medium, a to wystarcza, żeby narysować wykres zużycia
i podpisać go sensownie.

Jedno zalecenie niezależne od adaptera: **hub powinien przechowywać historię odczytów, a nie
tylko wartość bieżącą.** Licznik sam z siebie odpowiada wyłącznie na pytanie „ile łącznie";
na „ile w zeszłym miesiącu" odpowiada dopiero różnica dwóch odczytów, a tej węzeł nie liczy
i liczyć nie będzie — nie ma zegara kalendarzowego
([`../02-typy-danych.md`](../02-typy-danych.md) §3.2).
