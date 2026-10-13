# 01 · Model danych

> **Stabilne.** Model zamknięty. Rozróżnienie atrybutu i zdarzenia jest założeniem,
> od którego zależy cała reszta — zmiana tutaj unieważnia wszystkie typy.

## 1. Hierarchia

Model ma **dwa poziomy zagnieżdżenia i ani jednego więcej**: węzeł zawiera endpointy,
endpoint ma typ. Wszystko inne jest własnością jednego z tych dwóch.

```
WĘZEŁ                                   jedno urządzenie fizyczne, jeden adres
 │
 │  tożsamość   Uid                     ze sprzętu, nie zmienia się nigdy
 │  model       VendorId + DeviceType    czym to jest — nie co potrafi
 │  droga       Address                  11 bitów, może się zmienić
 │
 ├── ep0   Device      ─┐
 ├── ep1   Diagnostics  │  SYSTEMOWE — numer i typ ustala ta specyfikacja,
 ├── ep2   Groups       │  więc nie ma ich w deskryptorze
 ├── ep3   Scenes      ─┘  ep3 obecny tylko wtedy, gdy węzeł ma wyjście
 │
 ├── ep4   ─┐
 ├── ep5    │  FUNKCJONALNE — numerowane od 4 bez przerw,
 ├── ep6    │  w porządku fizycznym urządzenia, do 63
 └── ep…   ─┘
```

Endpoint ma **dokładnie jeden typ**. Typ jest nazwanym kontraktem i to on rozstrzyga,
co na endpoincie siedzi:

```
ENDPOINT · numer 0–63
│
├── typ             TypeId          0xF0
├── rewizja typu    TypeRevision    0xF1
├── cechy           Features        0xF2
│
├── atrybuty ───┬── z typu          0x00–0xEF
│               └── wspólne         0xF3–0xFA
├── komendy ─────── z typu
└── zdarzenia ───── z typu
```

Typ **nie jest** żadnym z tych trzech zbiorów — definiuje je wszystkie naraz, a każdy
z nich bywa pusty:

| Typ | Atrybuty | Komendy | Zdarzenia |
|---|---|---|---|
| [`Output`](types/0x0020-output.md) — sterowane wyjście | 17 | 9 | **0** |
| [`KeyInput`](types/0x0010-key-input.md) — klawisz | 7 | **0** | 6 |

Wyjście ma stan i przyjmuje polecenia, więc nie ma o czym powiadamiać. Klawisz niczego nie
przyjmuje i nie ma stanu wartego odczytania — mówi wyłącznie o faktach.

Typ, rewizja i cechy **same są atrybutami wspólnymi**: endpoint opisuje siebie tym samym
mechanizmem, którym podaje swój stan. Dlatego deskryptor odtwarza się zwykłym odczytem,
bez osobnej procedury (§7).

Opisy: typ i cechy — §2, trzy rodzaje elementów — §3, atrybuty wspólne — §4.

### 1.1 Reguła naczelna

> **Jeden endpoint ma dokładnie jeden typ.**

To jest główne odejście od Matter, gdzie endpoint skupia wiele klastrów. Wynikają
z tego trzy rzeczy:

1. **Numer endpointu implikuje typ.** Ramka nie musi nieść pola typu — przy
   ośmiu bajtach danych decyduje to o tym, czy model w ogóle się mieści.
2. **Endpoint jest najmniejszą jednostką, która ma osobną nazwę i osobny stan.**
   System nadrzędny odwzorowuje go wprost, bez heurystyk zgadujących, co dana
   kombinacja klastrów miała znaczyć.
3. **Deskryptor urządzenia jest płaską listą** `endpoint → typ + cechy`.

Cena: urządzenia mają więcej endpointów niż w Matter. Ściemniacz z pomiarem mocy to
dwa endpointy zamiast jednego. Przy 64 dostępnych endpointach i realnym maksimum
około ośmiu — to nie jest ograniczenie.

### 1.2 Endpointy systemowe

Cztery pierwsze numery są zarezerwowane. Nie pojawiają się w deskryptorze, bo ich numer
i typ są **ustalone przez tę specyfikację**, a nie przez urządzenie:

| Endpoint | Typ | Obecność |
|---|---|---|
| `0` | [`Device`](types/0x0001-device.md) | zawsze |
| `1` | [`Diagnostics`](types/0x0002-diagnostics.md) | zawsze |
| `2` | [`Groups`](types/0x0004-groups.md) | zawsze |
| `3` | [`Scenes`](types/0x0003-scenes.md) | wtedy i tylko wtedy, gdy węzeł ma wyjście |
| `4`–`63` | funkcjonalne | wg typu urządzenia |

Dzięki stałym numerom reguła „jeden endpoint = jeden typ” nie ma ani jednego
wyjątku, a hub wie, gdzie szukać diagnostyki, zanim pozna typ urządzenia.

**Obecność `Scenes` nie wymaga sprawdzania.** Endpoint `3` istnieje dokładnie wtedy, gdy
wśród endpointów funkcjonalnych jest choć jeden typu [`Output`](types/0x0020-output.md) —
a to hub wie po enumeracji, bo zna typ każdego endpointu
([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §3). Reguła jest wyliczalna
z deskryptora, więc endpointy systemowe pozostają tym, czego się **nie odpytuje**.

Endpoint `2` był **zarezerwowany bez przeznaczenia** — właśnie po to, żeby dołożenie
czegokolwiek systemowego nie przesunęło endpointów funkcjonalnych. Zajęła go tablica
przynależności do grup, gdy okazało się, że nie mieści się w atrybucie
([`types/0x0004-groups.md`](types/0x0004-groups.md) §5.1). Rezerwa spełniła swoje zadanie
przy pierwszej okazji.

Jest obecny **zawsze**, także w węźle, który grup nie obsługuje — taki deklaruje po prostu
`GroupCapacity = 0`. Obecność warunkowa kosztowałaby hub kolejną regułę do wyliczania,
a oszczędziłaby kilkanaście bajtów.

---

## 2. Typ endpointu

Typ to nazwany kontrakt: zbiór atrybutów, komend i zdarzeń opisujący jedną zdolność.
`KeyInput` to klawisz. `Output` to sterowane wyjście. `Sense` to pomiar.

> **Dlaczego nie „klaster”.** W Zigbee i Matter to samo pojęcie nazywa się klastrem, ale
> tam endpoint skupia ich kilka — i dopiero wtedy warto osobno nazywać pojemnik
> i zawartość. Skoro u nas endpoint ma dokładnie jeden, pojemnik i zawartość są tym samym,
> a słowo „klaster” sugerowałoby możliwość, której w tym systemie nie ma.

Każdy typ ma:

| Pole | Znaczenie |
|---|---|
| **ID** | `uint16`, unikalne w katalogu |
| **Nazwa** | krótka, po angielsku, np. `Output` |
| **Rewizja** | `uint8`, rośnie przy każdej zmianie kontraktu typu |
| **Cechy** | `bitmap16` — opcjonalne rozszerzenia (§2.1) |

### 2.1 Cechy (features)

Typ opisuje **wszystko, co endpoint tego rodzaju może potrafić**. Konkretne urządzenie
rzadko potrafi wszystko: przekaźnik nie ma jasności, ściemniacz nie ma barwy. Cechy
rozstrzygają, **które części typu obowiązują na tym endpoincie**.

> **Cecha niczego nie dokłada spoza typu.** Wybiera z tego, co typ już definiuje.

Dzięki temu jeden typ obsługuje całą rodzinę urządzeń, zamiast rozpadać się na osobny typ
dla przekaźnika, osobny dla ściemniacza i osobny dla taśmy kolorowej — a hub, który zna typ,
zna je wszystkie.

Przykład — typ [`Output`](types/0x0020-output.md):

| Bit | Cecha | Co obejmuje |
|---|---|---|
| — | *(rdzeń typu, zawsze obecny)* | atrybut `OnOff`, komendy `On`/`Off`/`Toggle` |
| 0 | `LEVEL` | atrybut `Level`, komendy `SetLevel`/`Step`/`Fade`/`Stop` |
| 1 | `COLOR_RGB` | atrybuty `Red`/`Green`/`Blue`/`White`, komenda `SetColor` |
| 2 | `COLOR_CCT` | atrybut `ColorTemperature`, komenda `SetColorTemperature` |

Przekaźnik deklaruje cechy puste — zostaje mu sam rdzeń. Ściemniacz deklaruje `LEVEL`.
Taśma RGBW deklaruje `LEVEL | COLOR_RGB`. Wszystkie trzy są tego samego typu i wszystkie
trzy odpowiadają na `Toggle`.

Cechy są **właściwością urządzenia, nie ustawieniem**: mówią, co zbudował jego autor —
sprzętem albo oprogramowaniem. Urządzenie deklaruje je raz, w deskryptorze (`Features`,
`0xF2`), i nie zmieniają się w czasie pracy. Ściemniacz nie przestaje umieć ściemniać,
a dzwonek, w którym nikt nie zbudował wielokliku, nie deklaruje go, choć jego styk by go
uniósł ([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §1).

**Odwoływanie się do elementu spoza zadeklarowanych cech jest błędem** i zwraca
`UNSUPPORTED_FEATURE` ([`04-interakcje.md`](04-interakcje.md) §9). Element wtedy istnieje
w typie — po prostu to urządzenie go nie ma. Hub zna cechy z enumeracji, więc **nie
konfiguruje elementów spoza nich**: ustawienie takiego elementu w konfiguracji jest
błędem zgłaszanym operatorowi, a nie zapisem, który węzeł ma odrzucić.

### 2.2 Rozróżnialność endpointów

Reguła obowiązująca przy projektowaniu każdego nowego typu:

> **Jeśli typ potrafi wytworzyć w jednym węźle dwa endpointy nierozróżnialne
> w deskryptorze, a znaczące co innego — brakuje mu atrybutu.**

Jest to **usterka typu**, nie powód, żeby hub dobierał znaczenie z katalogu per model.
Katalog, bez którego hub nie umie poprawnie pokazać danych, jest bazą konwerterów —
i unieważnia zasadę, że odczyt z węzła rozstrzyga
([`types/0x0001-device.md`](types/0x0001-device.md) §5.2).

Test jest prosty: weź dwa endpointy swojego typu w jednym węźle i sprawdź, czy da się je
odróżnić samym odczytem. `Sense` przechodzi dzięki `Quantity` i `Channel`, `Output` —
dzięki `Purpose` i `Channel`.

Reguła ta raz już czegoś nie przepuściła. [`Meter`](types/0x0031-meter.md) miał pierwotnie
trzymać energię pobraną i oddaną na **dwóch osobnych endpointach** — a dwa endpointy tego
samego typu, o tej samej wielkości i na tym samym kanale, są nie do odróżnienia. Kierunek
musiał więc zejść do wnętrza typu i został **atrybutem**
([`types/0x0031-meter.md`](types/0x0031-meter.md) §5.1). Tak wygląda ta reguła w działaniu:
nie zabrania budować, tylko wskazuje, gdzie brakuje pola.

---

## 3. Atrybut, komenda, zdarzenie

To rozróżnienie jest najważniejszą rzeczą w całym modelu i najczęstszym źródłem
pomyłek przy projektowaniu urządzeń.

| | **Atrybut** | **Zdarzenie** |
|---|---|---|
| Czym jest | **stan** | **fakt** |
| Ma wartość bieżącą | tak, zawsze | nie |
| Da się odczytać | tak | nie — można tylko usłyszeć, gdy zajdzie |
| Przegapienie | nieszkodliwe, przyjdzie kolejny raport | traci informację bezpowrotnie |
| Kiedy nadawany | przy zmianie i cyklicznie | raz, w chwili zajścia |

Przekaźnik ma **atrybut** `OnOff`: w każdej chwili jest albo włączony, albo nie,
i można o to zapytać. Klawisz ma **zdarzenie** `Click`: kliknięcie zaszło o określonej
godzinie i nie istnieje pytanie „czy klawisz jest teraz kliknięty".

**Jeden wyjątek od tego podziału jest dozwolony.** Gdy zmiana stanu jest **decyzją
sterującą**, na którą ktoś musi zareagować, a nie samą obserwacją, typ może opisać ją
**zarówno atrybutem, jak i zdarzeniem**: zdarzenie jest szybką ścieżką, bo jedzie
z priorytetem `0x1` zamiast `0x8`, a raport — prawdą, która przeżywa zgubienie i wraca
cyklicznie.

Wyjątek wolno wziąć **tylko razem z rozstrzygnięciem sporu**: przy rozbieżności obowiązuje
raport. Bez tego wraca dokładnie to ryzyko, przed którym broni podział — dwa opisy jednego
faktu, które się rozjeżdżają, i nie wiadomo, który jest prawdziwy.

Korzystają z tego dziś trzy typy:

| Typ | Co jest decyzją sterującą |
|---|---|
| [`Thermostat`](types/0x0040-thermostat.md) §4.1 | regulator zaczyna albo przestaje żądać ciepła |
| [`ValueInput`](types/0x0011-value-input.md) §4.1 | człowiek zmienił wartość |
| [`ToggleInput`](types/0x0013-toggle-input.md) §4.1 | człowiek przełączył stan |

> **Wejścia obsługiwane przez człowieka biorą ten wyjątek z zasady, nie wyjątkowo.**

Naciśnięcie klawisza jest decyzją, a nie obserwacją — i dochodzi tu drugi powód, którego
termostat nie ma: raport ze zmiany podlega histerezie i minimalnemu odstępowi (§6). Oba
mechanizmy powstały, żeby tłumić szum przetwornika, a zastosowane do palca zjadłyby
pojedyncze kliknięcie albo je opóźniły. Zdarzenie nie podlega żadnemu z nich.

Wejście, które **stanu nie ma** — [`KeyInput`](types/0x0010-key-input.md) — wyjątku nie
potrzebuje, bo nie ma czego dublować. Wejście, którego stan pochodzi ze świata, a nie
z decyzji — [`Contact`](types/0x0012-contact.md) — wyjątku brać **nie wolno**.

Konsekwencja praktyczna: **klawisz nie ma atrybutu stanu i nie da się go odpytać.**
Jeśli węzeł-klawisz był offline, gdy ktoś go nacisnął, to naciśnięcie przepadło.
Dlatego zdarzenia mają wyższy priorytet na magistrali niż raporty stanu.

### 3.1 Atrybut

| Pole | Znaczenie |
|---|---|
| **ID** | `uint8`; `0x00`–`0xEF` własne typu, `0xF0`–`0xFF` wspólne (§4) |
| **Typ** | patrz [`02-typy-danych.md`](02-typy-danych.md) |
| **Dostęp** | `RO` odczyt · `RW` odczyt i zapis · `WO` tylko zapis |
| **Trwałość** | `V` ulotny (RAM) · `P` trwały (EEPROM, przeżywa restart) |
| **Raportowany** | czy podlega automatycznemu raportowaniu (§6) |
| **Konformancja** | `M` obowiązkowy · `O` opcjonalny · `[CECHA]` zależny od cechy |
| **Zakres** | dopuszczalne wartości; zapis poza zakresem → `INVALID_VALUE` |
| **Domyślna** | wartość po `FactoryReset` |

Atrybuty konfiguracyjne (`RW`, `P`) mieszkają w tym samym typie co funkcja, której
dotyczą — próg przytrzymania jest atrybutem typu `KeyInput`, nie osobnym mechanizmem
konfiguracji. Dzięki temu istnieje jeden sposób czytania i zapisywania czegokolwiek.

### 3.2 Komenda

| Pole | Znaczenie |
|---|---|
| **ID** | `uint8`, unikalne w typie |
| **Kierunek** | zawsze do węzła |
| **Argumenty** | lista typowanych pól |
| **Odpowiedź** | **zawsze** — kod wyniku, opcjonalnie dane |

Komenda zmienia stan albo wywołuje akcję. **Jest transakcją**, tak samo jak odczyt
i zapis: dostaje odpowiedź z kodem wyniku
([`04-interakcje.md`](04-interakcje.md) §5).

Odpowiedź i raport mówią jednak **dwie różne rzeczy** i obie są potrzebne:

| | Mówi |
|---|---|
| **Odpowiedź** | „przyjąłem i wykonałem" albo „odrzucam, oto dlaczego" |
| **Raport** | jaki był **fizyczny skutek** |

Bez odpowiedzi komenda odrzucona byłaby nieodróżnialna od zgubionej — w obu przypadkach
cisza. Bez raportu nie dałoby się wykryć przekaźnika, który komendę przyjął, potwierdził
i się nie przełączył.

### 3.3 Zdarzenie

| Pole | Znaczenie |
|---|---|
| **ID** | `uint8`, unikalne w typie |
| **Parametry** | lista typowanych pól |
| **Priorytet** | `INFO` · `WARNING` · `CRITICAL` |
| **Licznik** | `uint8`, inkrementowany per endpoint, zawija `255 → 0` |

Zdarzenie jest nadawane **raz i bez wskazania adresata** — niesie adres nadawcy, nie
odbiorcy. Słucha go hub; nie ma potrzeby wpisywać go do każdej ramki, skoro jest jeden
([`04-interakcje.md`](04-interakcje.md) §1).

Licznik pozwala odbiorcy wykryć zgubione zdarzenie. Reguła: dziura w liczniku znaczy,
że coś przepadło — **zaloguj, ale wykonaj bieżące**. Nigdy nie próbuj odtwarzać
przeszłości.

---

## 4. Atrybuty wspólne

Każdy endpoint — **systemowy i funkcjonalny** — ma je niezależnie od typu. Zajmują
górny zakres ID, żeby nigdy nie kolidowały z atrybutami typu.

| ID | Nazwa | Typ | Dostęp | Opis |
|---|---|---|---|---|
| `0xF0` | `TypeId` | `u16` | RO | jaki typ ma ten endpoint |
| `0xF1` | `TypeRevision` | `u8` | RO | rewizja kontraktu typu |
| `0xF2` | `Features` | `map16` | RO | zadeklarowane cechy |
| `0xF3` | `Enabled` | `bool` | RW,P | endpoint wyłączony nie reaguje i nie raportuje |
| `0xF5` | `Channel` | `u8` | RO,P | kanał fizyczny, `0` = nie należy do pojedynczego (§5) |
| `0xF6` | `QueryEnabled` | `map16` | RW,P | które wejścia endpointu wolno odpytywać, bit na wejście |
| `0xF8` | `ReportInterval` | `u16` | RW,P | odświeżanie cykliczne [s], `0` = wyłączone |
| `0xF9` | `ReportMinGap` | `u16` | RW,P | minimalny odstęp raportów [ms] |
| `0xFA` | `ReportHysteresis` | `u16` | RW,P | próg zmiany wyzwalający raport |

Atrybuty typu i atrybuty wspólne **nie są dwiema różnymi rzeczami** — są jedną
przestrzenią ośmiobitową, podzieloną zakresem (§1). Czyta się je i zapisuje tak samo, tym
samym rodzajem wiadomości; różni je tylko to, że jedne definiuje typ, a drugie ta
specyfikacja.

Dlatego odczyt `0xF0`–`0xF2` i `0xF5` z każdego endpointu po kolei odtwarza pełny
deskryptor urządzenia — bez żadnego dodatkowego mechanizmu.

### 4.1 Na endpointach systemowych

Zestaw jest ten sam; dwa atrybuty mają na endpointach systemowych wartość ustaloną przez
tę specyfikację:

| Atrybut | Na endpoincie systemowym | Dlaczego |
|---|---|---|
| `Channel` | zawsze `0` | endpoint systemowy nie jest funkcją żadnego kanału (§5.3) |
| `Enabled` | zawsze `1`; zapis `0` → `INVALID_VALUE` | wyłączony `Device` odciąłby hub od tożsamości i komend węzła, wyłączony `Diagnostics` — od wykrywania nieobecności; `Groups` i `Scenes` mówią „nie obsługuję" własnymi środkami (`GroupCapacity = 0`, brak ep3) |
| `ReportInterval`, `ReportMinGap`, `ReportHysteresis` | działają jak na każdym endpoincie | na nich stoją domyślne ustawienia raportowania [`Diagnostics`](types/0x0002-diagnostics.md) §5.4 |
| `QueryEnabled` | `0` | typy systemowe nie deklarują wejść |

Raportowanie jest powodem, dla którego wyjątku tu nie ma. Próg ciszy węzła wylicza się
z najkrótszego `ReportInterval` wśród jego endpointów
([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §5.1) — a typowy panel
klawiszowy nie ma ani jednego atrybutu raportowanego poza diagnostyką. Bez
`ReportInterval` na `Diagnostics` taki węzeł nie miałby progu wcale.

### 4.2 Endpoint wyłączony

`Enabled = 0` wyłącza **funkcję** endpointu, nie jego obsługę. Endpoint wyłączony:

| | Zachowanie |
|---|---|
| odczyt i zapis | działają jak zawsze — inaczej hub nie mógłby go z powrotem włączyć ani sprawdzić, że jest wyłączony |
| komenda | odpowiedź `INVALID_STATE`; komenda nie jest wykonywana |
| zdarzenia | nie są nadawane; licznik zdarzeń nie rośnie, bo nic nie wyszło |
| raporty | nie są nadawane — ani przy zmianie, ani cyklicznie |

Komenda dostaje odpowiedź, a nie ciszę, bo cisza jest nieodróżnialna od zgubionej ramki
i hub powtórzyłby ją trzy razy ([`04-interakcje.md`](04-interakcje.md) §2). `INVALID_STATE`
mówi dokładnie to, co trzeba: komenda jest poprawna, ale nie w tym stanie endpointu.

## 5. Kanał fizyczny

Deskryptor jest płaską listą i sam z siebie nie niesie **żadnej relacji między endpointami**.
Dla urządzenia wielokanałowego jest to za mało: cztery wyjścia i cztery pomiary prądu nie
mówią, który pomiar dotyczy którego wyjścia.

Rozstrzyga to atrybut wspólny `0xF5 Channel` — na tyle nośny, że zasługuje na własną
sekcję, choć jest jednym wierszem w tabeli §4.

### 5.1 Co znaczy numer kanału

> **Endpointy o tej samej niezerowej wartości `Channel` opisują tę samą rzecz fizyczną.**
> Wartość `0` znaczy „nie należę do żadnego pojedynczego kanału".

```
0x0205 — Czterokanałowy przekaźnik z pomiarem prądu

  ep4  Output  ch1      ep8   Sense CURRENT  ch1
  ep5  Output  ch2      ep9   Sense CURRENT  ch2
  ep6  Output  ch3      ep10  Sense CURRENT  ch3
  ep7  Output  ch4      ep11  Sense CURRENT  ch4

  ep12 Sense TEMPERATURE  ch0    temperatura w rozdzielnicy
```

Numer kanału jest **lokalny dla węzła** i poza nim nic nie znaczy.

**Zero znaczy „samodzielny", nie „nieznany".** Różnica jest istotna: czujnik temperatury
w panelu klawiszowym jest samodzielny naprawdę, a pomiar sumaryczny prądu w module
czterokanałowym nie należy do żadnego pojedynczego kanału, choć dotyczy wszystkich.
Gdyby `0` znaczyło „nie wiem", każde urządzenie byłoby dwuznaczne z urzędu — a to jest
ta sama pomyłka, przed którą broni wartość „brak"
([`02-typy-danych.md`](02-typy-danych.md) §2.1).

`Channel` jest `RO`, bo jest faktem **produkcyjnym**: który zacisk siedzi na którym
boczniku, rozstrzyga płytka drukowana. Instalator tego nie zmieni, a błędna wartość cicho
rozjechałaby prezentację zamiast być widocznym błędem. Tym różni się od `Invert`, który
jest faktem montażowym i dlatego jest zapisywalny.

### 5.2 Czym kanał nie jest

Kanał grupuje endpointy, więc łatwo pomylić go z trzema innymi rzeczami. Wszystkie trzy
pomyłki są częste i wszystkie trzy warto odciąć wprost.

**Nie jest poziomem hierarchii.** Jest **podziałem zbioru endpointów** — etykietą, nie
pojemnikiem. Rozstrzygają to trzy pytania, wszystkie z odpowiedzią przeczącą:

| Czy kanał… | |
|---|---|
| ma własny stan? | **nie** — cały stan siedzi w endpointach |
| da się go zaadresować? | **nie** — w ramce nie ma pola kanału |
| istnieje bez endpointów, które go wskazują? | **nie** — kanał pusty nie istnieje |

Dlatego hierarchia ma dwa poziomy, a nie trzy (§1).

**Nie jest grupą.** Oba grupują endpointy i na tym podobieństwo się kończy:

| | Grupa ([`types/0x0004-groups.md`](types/0x0004-groups.md)) | `Channel` (`0xF5`) |
|---|---|---|
| Czym jest | **adresowanie** na magistrali | **układ fizyczny** urządzenia |
| Zasięg | cała instalacja | wyłącznie ten węzeł |
| Kto nadaje | hub, komendami | firmware, `RO` |

Grupa mówi „wywołaj mnie razem z tamtymi" i da się do niej wysłać komendę
([`03-adresacja.md`](03-adresacja.md) §3.2). Do kanału nie da się wysłać niczego.

**Nie mówi, czym endpoint jest.** Kanał odpowiada na pytanie **którą** rzeczą fizyczną
endpoint jest; **czym** ta rzecz jest, mówi `Purpose` — atrybut typów, które go potrzebują
([`types/0x0020-output.md`](types/0x0020-output.md) §2.4). Oba są niezależne i oba są
potrzebne:

```
ep6  Output  ch1  INDICATOR   podświetlenie klawisza z ep4
ep8  Output  ch3  LIGHT       oświetlenie
ep10 Output  ch5  GENERIC     wyjście ogólne
```

Hub czyta z tego, które wyjście należy do „zgaś wszystkie światła", a które jest diodą
i do tej akcji nie należy — bez żadnej wiedzy o modelu urządzenia.

### 5.3 Jak to wygląda w hubie

> **Zalecenie, nie wymaganie.** Sposób prezentacji nie należy do tej specyfikacji. Warto
> je jednak zapisać, bo wynika wprost z modelu, a nie z wyboru adaptera północnego.

Kanał jest **naturalną jednostką prezentacji** — czymś, co człowiek nazywa i co widzi jako
jedną rzecz. Ani węzeł, ani endpoint się do tego nie nadają: węzeł jest za duży
(czterokanałowy przekaźnik to cztery rzeczy), endpoint za mały (wyjście i jego pomiar
prądu to jedna rzecz opisana dwoma endpointami).

Ten sam przekaźnik co w §4.1, widziany od strony huba:

```
Węzeł 0x02A  ·  VendorId 0 / DeviceType 0x0205
│
├─ kanał 1 ──── Output LIGHT      Sense CURRENT     ─┐
├─ kanał 2 ──── Output LIGHT      Sense CURRENT      │ nazywane przez
├─ kanał 3 ──── Output GENERIC    Sense CURRENT      │ człowieka
├─ kanał 4 ──── Output GENERIC    Sense CURRENT     ─┘
│
├─ urządzenie ─ Sense TEMPERATURE                     kanał 0
│
└─ serwis ───── Device · Diagnostics                  ep0, ep1
```

Trzy rzeczy, które z tego wynikają:

**Endpointy systemowe są poza widokiem kanałów.** Mają `Channel = 0` jak każdy endpoint
(§4.1), ale do poziomu urządzenia nie należą: hub rozpoznaje je **po numerze `0`–`3`**,
a nie po kanale. `Device` i `Diagnostics` nie są funkcjami urządzenia, tylko informacją
o nim samym.

**Kanał `0` to poziom urządzenia.** Zbiera to, czego nie da się przypisać do pojedynczego
kanału: czujnik otoczenia, pomiar sumaryczny, podświetlenie wspólne dla całego panelu.

**Kolejność kanałów bierze się z numerów endpointów.** Kanały uporządkowane według
najniższego endpointu, który do nich należy, wychodzą w porządku fizycznym urządzenia —
bo endpointy funkcjonalne są tak właśnie numerowane
([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §3.2). Nie trzeba do tego
żadnego dodatkowego pola.

Stąd też praktyczny wniosek o nazwach. [`02-typy-danych.md`](02-typy-danych.md) §2.2 mówi,
że nazwy nadane przez człowieka mieszkają w bazie huba, kluczowane po `Uid` — ale nie mówi,
co jest kluczem wewnątrz węzła. **Naturalnym kluczem jest kanał**: `(Uid, Channel)` dla
kanałów od `1` w górę i `(Uid, endpoint)` dla tego, co siedzi na kanale `0`. Dzięki temu
„Lampa nad stołem" nazywa się raz, a nie osobno dla wyjścia i osobno dla jego pomiaru.

---

---

## 6. Raportowanie

Atrybut oznaczony jako raportowany jest nadawany **rozgłoszeniowo** w trzech sytuacjach:

| Wyzwalacz | Warunek |
|---|---|
| **Zmiana** | wartość zmieniła się o co najmniej `ReportHysteresis` |
| **Cyklicznie** | upłynęło `ReportInterval`, nawet gdy nic się nie zmieniło |
| **Na żądanie** | odczyt atrybutu przez hub |

Odstęp między kolejnymi raportami z jednego endpointu nigdy nie jest mniejszy niż
`ReportMinGap` — to chroni magistralę przed szumem przetwornika.

Odstęp liczy się między **rundami**, nie między ramkami. Runda to wszystkie atrybuty
endpointu, którym w danej chwili należy się raport, nadane razem: odświeżanie cykliczne
wysyła w jednej rundzie każdy atrybut raportowany, a wyjście kończące przejście —
`Transitioning = 0` razem z osiągniętym poziomem ([`types/0x0020-output.md`](types/0x0020-output.md)
§5.3). Gdyby odstęp dotyczył pojedynczych ramek, raporty opisujące jeden stan
rozjechałyby się o `ReportMinGap` i hub widziałby przez chwilę stan, którego nie było.
Raport wstrzymany przez odstęp nie przepada: wychodzi, gdy odstęp minie, i niesie
wartość **bieżącą**, nie tę sprzed chwili.

### 6.1 Wyzwalacze działają jednocześnie

> **Zmiana i odświeżanie cykliczne nie są alternatywą.** Oba są aktywne naraz i nie
> wyłączają się nawzajem.

Jest to najczęstsza pomyłka przy czytaniu tego rozdziału, więc warto powiedzieć wprost,
czemu każdy z nich służy:

| | Odpowiada za |
|---|---|
| `ReportHysteresis` | **gadatliwość** raportów ze zmiany — ile musi się zmienić, żeby warto było mówić |
| `ReportInterval` | **dno świeżości** — po jakim czasie hub ma pełny obraz, nawet gdy nic się nie dzieje |

Odświeżanie cykliczne istnieje po to, żeby hub po restarcie odzyskał pełny obraz
instalacji **bez odpytywania stu urządzeń**. Wystarczy poczekać jeden okres. Gdyby
ustawienie interwału wyłączało raportowanie przy zmianie, czujnik z odświeżaniem
pięciominutowym zgłaszałby pożar średnio po dwóch i pół minuty.

Oba zachowania skrajne są zresztą osiągalne bez dodatkowego przełącznika:
`ReportInterval = 0` daje „tylko przy zmianie", a bardzo wysoka histereza — „praktycznie
tylko cyklicznie".

### 6.2 Czego dotyczy histereza

**Histereza dotyczy wyłącznie atrybutów liczbowych** i jest wyrażona **w jednostkach tego
atrybutu**: dla temperatury w setnych stopnia, dla poziomu w promilach.

| Typ atrybutu | Co znaczy zmiana |
|---|---|
| liczbowy (`u8`…`i32`) | różnica od ostatnio raportowanej wartości ≥ `ReportHysteresis` |
| `bool`, `enum`, pole bitowe | **każda zmiana jest zmianą**; histereza jest ignorowana |
| `string`, `blob` | j.w. — te i tak nie są raportowane |

`ReportHysteresis = 0` znaczy **raportuj każdą zmianę, choćby o jeden bit**. Jest to
wartość dopuszczalna, ale dla czujnika analogowego zwykle błędna: przetwornik szumi
ostatnim bitem bez przerwy ([`types/0x0030-sense.md`](types/0x0030-sense.md) §5.3).

**Typ raportujący więcej niż jeden atrybut liczbowy musi powiedzieć, którego z nich
histereza dotyczy.** Jedna wartość nie stosuje się sensownie do kilku różnych skal naraz —
poziom w promilach i składowa barwy w zakresie 0–255 nie mają wspólnej miary. Typy,
w których zmiana stanu jest zdarzeniem sterującym, a nie pomiarem — jak
[`Output`](types/0x0020-output.md) — raportują każdą zmianę niezależnie od histerezy.

---

## 7. Deskryptor urządzenia

Typ urządzenia to nic więcej niż lista endpointów z typami i cechami:

```
Typ 0x0102 — Przycisk trzyklawiszowy z podświetleniem i termometrem

  ep4   KeyInput                             ch1   klawisz górny
  ep5   KeyInput                             ch2   klawisz środkowy
  ep6   KeyInput                             ch3   klawisz dolny
  ep7   Output [LEVEL|COLOR_RGB] INDICATOR   ch0   podświetlenie całego panelu
  ep8   Sense  quantity = TEMPERATURE        ch0   termometr

  (ep0–ep2 systemowe, ep3 obecny bo węzeł ma wyjście)
```

Hub widzi z tego pięć niezależnych funkcji: trzy źródła zdarzeń, jedno wyjście
sterowane i jeden pomiar. Odwzorowanie na obiekty systemu nadrzędnego jest mechaniczne,
bo endpoint jest najmniejszą jednostką, która ma osobną nazwę i osobny stan.

Podświetlenie ma `Purpose = INDICATOR`, a nie `LIGHT` — inaczej „zgaś wszystkie światła"
zgasiłoby podświetlenie klawiszy w całym domu. `Channel = 0` przy obu ostatnich
endpointach, bo jedna dioda obsługuje cały panel, a termometr nie mierzy żadnego
z klawiszy. Gdyby każdy klawisz miał własną diodę, jej endpoint niósłby `ch1`, `ch2`,
`ch3` — i hub wiedziałby, która należy do którego klawisza, bez pytania człowieka.

Katalog typów endpointów: [`types/`](types/).
Rejestr modeli urządzeń: [`registry/device-types.yaml`](registry/device-types.yaml).

---

## 8. Konformancja

Notacja używana w tabelach całej specyfikacji:

| Zapis | Znaczenie |
|---|---|
| `M` | obowiązkowy — implementacja **musi** go mieć |
| `O` | opcjonalny — **może** go mieć |
| `[LEVEL]` | obowiązkowy wtedy i tylko wtedy, gdy zadeklarowano cechę `LEVEL` |
| `[MULTICLICK, RAW]` | obowiązkowy wtedy i tylko wtedy, gdy zadeklarowano **którąkolwiek** z wymienionych cech |
| `O [HOLD]` | opcjonalny, ale **wolno go mieć** tylko przy zadeklarowanej cesze `HOLD`; bez niej odwołanie daje `UNSUPPORTED_FEATURE` |
| `!` | zabroniony w tym kontekście |

Urządzenie, które deklaruje typ, musi zaimplementować **wszystkie** jego atrybuty
i komendy oznaczone `M`. Brak choćby jednego oznacza, że nie wolno deklarować tego
typu — trzeba użyć innego albo zdefiniować nowy.

### 8.1 Ustawienie, którego urządzenie nie wystawia

Ustawienie oznaczone `O` albo `O [CECHA]`, którego endpoint nie ma, **nie znaczy, że
ustawienia nie ma** — znaczy, że wartość ustala autor urządzenia i hub nie może jej
zmienić. Obowiązują wtedy trzy zasady:

1. Wartość stosowana przez urządzenie **mieści się w kolumnie „Zakres"** typu. Zakres jest
   wymaganiem wobec zachowania, nie wobec atrybutu.
2. Kolumna „Domyśl." jest dla takiego urządzenia **zaleceniem**, nie obowiązkiem.
3. Wartość jest **stała w czasie pracy**. Czego nie da się ustawić z magistrali, tego
   urządzenie nie zmienia samo.

Które ustawienie typ czyni obowiązkowym, a które opcjonalnym, rozstrzyga pytanie,
**kto zna właściwą wartość**:

| Wartość wynika z… | Kto ją zna | W typie |
|---|---|---|
| **budowy** — czegoś, co autor urządzenia sam zbudował: drgania wbudowanego styku, polaryzacja pinu, szum własnego przetwornika | autor urządzenia | **nie ma atrybutu** albo atrybut `O` |
| **instalacji** — tego, co instalator podłączył do zacisków: kontaktron zwierny czy rozwierny, krańcówka drgająca sekundami, odbiornik na styku rozwiernym | instalator, przez hub | atrybut `O`; urządzenie z czujnikiem wbudowanym ustala wartość samo, moduł z zaciskami **powinien** ją wystawić |
| **użycia** — tego, do czego mieszkaniec chce rzeczy używać: nastawa, krok, czy przytrzymanie ma działać | mieszkaniec, przez hub | atrybut `M` albo `[CECHA]` |

Rozróżnienie budowy od instalacji bywa subtelne, bo to samo pojęcie trafia do obu: drgania
styku klawisza wbudowanego w panel zna jego autor, a drgań kontaktronu przykręconego do
bramy — tylko instalator.
