# Punkty otwarte

> **Dokument żywy.** Jedyne miejsce, w którym zbiera się rzeczy nierozstrzygnięte.
> Rozdziały opisują to, co ustalone ([`POJECIA.md`](POJECIA.md) §4); uzasadnienia tego, co
> już rozstrzygnięte, są w [`DECYZJE.md`](DECYZJE.md).

Dwa rodzaje pozycji, bo biorą się z różnych miejsc:

| | co | skąd |
|---|---|---|
| **W**, **D** | rzeczy **świadomie nierozstrzygnięte** | przy pisaniu specyfikacji |
| **B** | rzeczy, które **wyglądają na rozstrzygnięte, a nie są** — sprzeczności i braki | przy implementacji huba i firmware |

Przy pozycji **B** zapisane jest, **jak implementacja zachowuje się dzisiaj**, żeby dało się
to cofnąć, gdy rozstrzygnięcie pójdzie inaczej.

Waga: 🔴 **blokujące albo rozjeżdża implementacje** — dwa zgodne wykonania zachowają się
różnie · 🟠 **ważne** — da się odłożyć, ale wróci · 🟡 **drobne**.

Stan na **2026-09-28**. Rozstrzygnięta pozycja stąd znika, a jej uzasadnienie trafia do
[`DECYZJE.md`](DECYZJE.md).

---

## Sprzeczności znalezione przy implementacji

### 🔴 B1. Czy endpointy systemowe mają atrybuty wspólne

**Gdzie:** [`01-model-danych.md`](01-model-danych.md) §4 i §5.3 wobec
[`types/0x0002-diagnostics.md`](types/0x0002-diagnostics.md) §5.4.

Trzy zdania, które nie mogą być prawdziwe naraz:

| Gdzie | Co mówi |
|---|---|
| [`01`](01-model-danych.md) §4 | „Każdy endpoint **funkcjonalny** ma je niezależnie od typu" |
| [`01`](01-model-danych.md) §5.3 | „Atrybuty wspólne — a więc i `Channel` — ma **wyłącznie** endpoint funkcjonalny" |
| [`types/0x0002`](types/0x0002-diagnostics.md) §5.4 | `Diagnostics` ma domyślny `ReportInterval` **300 s** i histerezę **16** |

`ReportInterval` (`0xF8`) i `ReportHysteresis` (`0xFA`) **są atrybutami wspólnymi**.
Trzeci wiersz przeczy więc drugiemu.

Nie jest to spór o literę. [`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md)
§5.1 definiuje próg ciszy jako „dwa razy najkrótszy niezerowy `ReportInterval`
**wśród jego endpointów**". Jeśli `Diagnostics` nie ma `ReportInterval`, to węzeł
raportujący wyłącznie diagnostykę — czyli **typowy panel klawiszowy** — nie ma
wyliczalnego progu i cały mechanizm wykrywania nieobecności traci oparcie.

#### Co robi dziś hub

**Zakłada, że mają** — wszystkie cztery endpointy systemowe dostają pełny zestaw
`0xF0`–`0xFA`. Jednolitość okazała się tańsza niż wyjątek dla jednego endpointu.

#### Możliwe rozstrzygnięcia

| Wyjście | Koszt |
|---|---|
| **§5.3 mówi wyłącznie o `Channel`** i trzeba to napisać wprost | jedno zdanie; `Device` dostaje przy okazji `Enabled`, co jest dziwne |
| `Diagnostics` dostaje **własne** atrybuty konfiguracji raportowania, spoza zakresu wspólnego | dwa numery w przestrzeni typu; za to §5.3 zostaje prawdziwe bez zastrzeżeń |
| atrybuty wspólne dzielą się na **zawsze obecne** i **tylko funkcjonalne** | najdokładniejsze i najdroższe: nowy podział do opisania w §4 |

---

### 🟠 B2. Budżet czasu huba jest ostrzejszy, niż komukolwiek potrzeba

**Gdzie:** [`07-hub.md`](07-hub.md) §4.2.

> Dopasowanie powiązania — **poniżej 1 ms**

Liczba jest wzięta z wyobrażenia o sprzęcie, a nie z tego, co człowiek zauważa. Próg
odczuwalności opóźnienia reakcji leży gdzieś od stu milisekund; sama specyfikacja pisze
w [`types/0x0010-key-input.md`](types/0x0010-key-input.md) §5.2, że **80–150 ms jest
niezauważalne** i że `Click` powstaje dopiero przy zwolnieniu właśnie dlatego.

Zdanie w §4.2 jest więc **sto razy ostrzejsze** niż zdanie w §5.2 tego samego kontraktu,
i to ono będzie decydowało, czy przyszła implementacja uzna się za zgodną.

#### Co robi dziś hub

Przyjmuje budżet **kilkudziesięciu milisekund** i świadomie rozjeżdża się z §4.2
([`hub/ARCHITEKTURA.md`](../hub/ARCHITEKTURA.md) §5). Pomiar na magistrali wirtualnej
daje 22 µs, więc zapas jest trzy rzędy wielkości — ale zapas ma być zapasem, a nie
wymaganiem.

#### Proponowane rozstrzygnięcie

Zapisać budżet rzędu **kilkudziesięciu milisekund** i wprost powiedzieć, skąd się bierze:
z progu odczuwalności, a nie z możliwości sprzętu.

**Zdanie o zakazie kolejkowania zostaje** — jest słuszne i to ono niesie treść:

> Hub nie może kolejkować ani grupować powiązań w czasie.

Chroni przed tym, żeby powiązanie przeszło przez bazę danych albo czekało na przebieg
pętli — i ta ochrona nie zależy od tego, czy próg wynosi milisekundę, czy pięćdziesiąt.

---

### 🔴 B3. Węzeł, który sam ma adres, a hub go nie zna, nie ma drogi do instalacji

**Gdzie:** [`03-adresacja.md`](03-adresacja.md) §5.1 i [`03`](03-adresacja.md) §7 wobec
[`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §2.1, przy
[`03`](03-adresacja.md) §2.2.

Węzeł z adresem w pamięci trwałej **nie bierze udziału w przyłączaniu** ([`03`](03-adresacja.md)
§5.1) — i słusznie, bo inaczej każdy powrót zasilania byłby burzą zgłoszeń. Ale przyłączanie
jest **jedyną drogą** do instalacji, a bramka trybu przyjmowania rozpoznaje węzeł po
`ShortId` ([`06`](06-cykl-zycia-urzadzenia.md) §2.1), który jedzie wyłącznie w ramce
zgłoszeniowej.

Taki węzeł odzywa się więc `Booted`, a `Booted` niesie `resetReason` i `firmwareVersion` —
**nie `Uid`**. Tożsamością jest `Uid` ([`03`](03-adresacja.md) §2.2), więc hub słyszy adres,
którego nie potrafi z niczym związać. Nie ma też jak go poszukać: odpytania wszystkich
adresów zabrania wprost [`07-hub.md`](07-hub.md) §5.1, a mechanizmu skanowania specyfikacja
nie definiuje w ogóle.

Kiedy to się zdarza: baza huba odtworzona z niepełnej kopii, baza utracona, węzeł
przeniesiony z innej instalacji, zapis rekordu zgubiony między przydziałem adresu
a utrwaleniem.

#### Co robi dziś hub

Zlicza `unknown_booted` i nic więcej; licznik widać w `/health`. Węzeł pracuje na
magistrali, a instalacja go nie widzi — i nigdy nie zobaczy.

#### Rozstrzygnięcie

**Hub odczytuje tożsamość spod tego adresu i wystawia węzeł jako `OCZEKUJĄCY`; decyduje
operator.** Węzeł ma adres, więc zwykły odczyt zadziała istniejącymi środkami — nie trzeba
ani nowej ramki, ani nowego stanu, bo `OCZEKUJĄCY` z [`06`](06-cykl-zycia-urzadzenia.md)
§1.2 znaczy dokładnie „zgłosił się, ale sam z siebie nie wchodzi".

Zachowana zostaje asymetria z [`06`](06-cykl-zycia-urzadzenia.md) §2.1: **nieznane
urządzenie nadal nie wchodzi do instalacji samo**. Gdyby hub przyjmował je po cichu,
bramka trybu przyjmowania przestałaby cokolwiek chronić — wystarczyłoby podłączyć węzeł
z dowolnym adresem.

Operator ma dwie drogi, i to one wymagają dopisania:

| Droga | Co się dzieje |
|---|---|
| **przyjmij** | hub potwierdza adres, enumeruje, węzeł przechodzi w `GOTOWY` |
| **przywróć ustawienia fabryczne** | węzeł kasuje adres, wstaje bezadresowy i przechodzi normalne przyłączanie ([`06`](06-cykl-zycia-urzadzenia.md) §7) |

**Hub czyta `ShortId` z węzła, nie wylicza go z `Uid`.** Atrybut jest obowiązkowy i RO
([`types/0x0001`](types/0x0001-device.md) §2.1), więc odpowiedź węzła jest rozstrzygająca —
a wyliczanie po swojej stronie zakłada, że węzeł liczy tak samo. Dokładnie na tym
przewrócił się firmware: liczył cztery starsze bajty `Uid` zamiast CRC-32 i nikt tego nie
widział, dopóki nikt nie policzył dwa razy.

#### Do zrobienia

- [ ] rozdziały: [`06`](06-cykl-zycia-urzadzenia.md) dostaje przebieg dla `Booted` spod
      nieznanego adresu; [`03`](03-adresacja.md) §5.1 odsyłacz, że to nie jest ślepa uliczka
- [ ] **hub**: odczyt tożsamości zamiast samego licznika `unknown_booted`
- [ ] **hub**: operacje „przyjmij" i „przywróć ustawienia fabryczne" w `lagunhub.api`
- [ ] **TUI i powłoka**: lista węzłów `OCZEKUJĄCY` z tych dwóch akcji — dziś nie ma gdzie
      takiego węzła nawet zobaczyć
- [ ] [`COMPLIANCE.md`](COMPLIANCE.md): wymaganie dla huba

---

## Świadomie nierozstrzygnięte

**Nic nie blokuje implementacji węzła.**

### W2. Prędkość magistrali i maksymalna długość odcinka

Nie wybrano między 250 a 500 kbit/s. [`05-mapowanie-can.md`](05-mapowanie-can.md) §6
pokazuje, że **przepustowość nie jest czynnikiem** — obciążenie jest znacznie poniżej
jednego procenta w obu wariantach. Decyduje wyłącznie długość kabla i odporność na
zakłócenia, a to jest pytanie do pomiaru na prawdziwej instalacji, nie do rozstrzygnięcia
przy biurku.

### W3. Ładunki rodzajów, których typy jeszcze nie powstały

[`05-mapowanie-can.md`](05-mapowanie-can.md) §5 opisuje układy ładunków częściowo.
Domknie się samo wraz z katalogiem typów — ale warto po każdym nowym typie sprawdzić
**najciaśniejszy przypadek**: dziś jest nim odpowiedź na `Groups.GetMembership` —
**osiem bajtów z ośmiu**, bez ani jednego wolnego ([`05-mapowanie-can.md`](05-mapowanie-can.md) §5.3).

### D7. „Linia" i „magistrala" to synonimy

Obu słów używa się zamiennie. [`POJECIA.md`](POJECIA.md) §1.1 opisuje to jako świadomy
synonim — „linia" tam, gdzie mowa o przebiegu kabla w domu. Do rozstrzygnięcia, czy
zostawić, czy ujednolicić do jednego słowa.

---

## Świadomie odłożone

Nie są to luki — są to rzeczy, których v1 **nie będzie** robić.

| Co | Dlaczego odłożone |
|---|---|
| Wymiana uszkodzonego modułu z zachowaniem konfiguracji | Dziś: usuń stary, dodaj nowy, skonfiguruj. Ciągłość wymagałaby rezerwowania adresu i odtwarzania ustawień z kopii ([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §8) |
| Rozmowy między węzłami | Rozstrzygnięte przeciw, nie odłożone ([`00-wprowadzenie.md`](00-wprowadzenie.md) § Kierunek ruchu) |
| Zabezpieczenie kryptograficzne magistrali | Magistrala biegnie w ścianie; kto ma do niej dostęp, ma większe możliwości ([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §2.1) |
| Wzorzec „dwuklik i przytrzymaj" | Pole w `HoldStart` zarezerwowane ([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §5.4) |
| Nastawa wejściowa w jednostkach fizycznych | Ścienne pokrętło zadające 21,5 °C nie mieści się w [`ValueInput`](types/0x0011-value-input.md) §5.1, bo ten zna wyłącznie promile. Wymaga pola `Quantity` jak w [`Sense`](types/0x0030-sense.md), czyli nowej cechy albo nowej rewizji |
| Aktualizacja firmware przez magistralę | Segmenty jej nie uniosą — 1536 B to nie jest obraz programu. Wymaga własnego mechanizmu ([`05-mapowanie-can.md`](05-mapowanie-can.md) §6.9) |
