# Typ endpointu `0x0002` · Diagnostics

> **Stabilne.** Liczniki i zdarzenia ustalone. Progi domyślne mogą się jeszcze zmienić.

**Rewizja 1** · kondycja węzła i magistrali

Siedzi zawsze na **endpoincie 1** i jest — obok [`Device`](0x0001-device.md) — jedynym
typem obecnym w każdym węźle bez wyjątku. Odpowiada na pytanie „jak ci się jedzie",
zadawane wtedy, gdy wszystko jeszcze działa.

Ten typ istnieje po to, żeby dotrzymać trzeciej gwarancji z
[`00-wprowadzenie.md`](../00-wprowadzenie.md) § Trzy gwarancje: **degradację połączenia
widać na wykresie, zanim stanie się odczuwalna dla mieszkańca**. Bez liczników nie da się
odróżnić instalacji zdrowej od takiej, która od pół roku powtarza co dziesiątą ramkę
i właśnie kończy jej się zapas.

---

## 1. Cechy

**Brak.** Tak jak `Device`, `Diagnostics` jest identyczny w każdym węźle. Diagnostyka,
której zakres zależy od urządzenia, nie nadaje się do porównywania urządzeń między sobą —
a porównywanie jest jej głównym zastosowaniem.

Część atrybutów jest natomiast **opcjonalna** (`O`): węzeł, który nie ma jak zmierzyć
napięcia zasilania, po prostu tego atrybutu nie ma.

---

## 2. Atrybuty

### 2.1 Stan magistrali

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `TxErrorCount` | `u16` | RO | V | **tak** | M | licznik błędów nadawania z kontrolera |
| `0x01` | `RxErrorCount` | `u16` | RO | V | **tak** | M | licznik błędów odbioru z kontrolera |
| `0x02` | `BusState` | `enum8` | RO | V | **tak** | M | §2.4 |
| `0x03` | `BusOffCount` | `u16` | RO | P | nie | M | ile razy węzeł odpadł od magistrali |

`TxErrorCount` i `RxErrorCount` są **liczbami szesnastobitowymi, choć kontroler trzyma je
na ośmiu**. Powód jest wyłącznie taki, że `u8` rezerwuje `0xFF` na wartość „brak"
([`02-typy-danych.md`](../02-typy-danych.md) §2.1), a licznik błędów nadawania sięga
dokładnie 255 — i właśnie ta wartość jest najważniejsza ze wszystkich, bo oznacza
odpadnięcie od magistrali. Typ, w którym najciekawszy odczyt jest nieodróżnialny od
awarii czujnika, byłby błędem projektowym.

### 2.2 Ruch i straty

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x04` | `TxFrames` | `u32` | RO | V | nie | O | ramki nadane od startu |
| `0x05` | `RxFrames` | `u32` | RO | V | nie | O | ramki odebrane i przyjęte przez filtry |
| `0x06` | `TxDropped` | `u16` | RO | P | nie | M | porzucone przy przepełnieniu kolejki (§5.3) |
| `0x07` | `RxOverruns` | `u16` | RO | P | nie | O | utracone, bo procesor nie nadążył odebrać |

`TxFrames` i `RxFrames` są ulotne i liczone od startu — służą do wyliczenia **udziału**
strat, a nie do inwentaryzacji ruchu. `TxDropped` i `RxOverruns` są trwałe, bo strata,
która zdarzyła się przed ostatnim restartem, nadal jest stratą i nadal coś znaczy.

### 2.3 Kondycja węzła

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x10` | `SupplyVoltage` | `u32` | RO | V | tak | O | skala `VOLTAGE`, 0,001 V |
| `0x11` | `McuTemperature` | `i16` | RO | V | nie | O | skala `TEMPERATURE`, 0,01 °C |

Oba używają **skal wspólnych dla całej specyfikacji**, nie własnych
([`02-typy-danych.md`](../02-typy-danych.md) §3). Napięcie zasilania mierzone przez węzeł
jest napięciem jak każde inne i nie ma powodu, by system nadrzędny musiał wiedzieć,
skąd pochodzi, żeby je narysować.

`SupplyVoltage` jest pierwszą rzeczą do sprawdzenia, gdy `Device.LastResetReason` pokazuje
`BROWNOUT` ([`0x0001-device.md`](0x0001-device.md) §2.4). Zwykle znaczy to za długi odcinek
albo za cienką żyłę zasilania, a nie wadę węzła.

### 2.4 `BusState`

| Wartość | Nazwa | Znaczenie |
|---|---|---|
| `0` | `ACTIVE` | praca normalna; węzeł zgłasza błędy aktywnie |
| `1` | `PASSIVE` | licznik przekroczył 127 — węzeł nadal pracuje, ale ustępuje |
| `2` | `BUS_OFF` | węzeł odłączony od magistrali, nie nadaje nic (§5.2) |

`PASSIVE` jest stanem, w którym **wszystko jeszcze działa** i właśnie dlatego jest
najważniejszy. Węzeł w tym stanie nadaje i odbiera, tyle że przy błędzie nie przerywa już
cudzej transmisji. Instalacja sprawia wrażenie zdrowej, a jeden węzeł stracił zdolność
obrony przed zakłóceniami.

### 2.5 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x20` | `ErrorThreshold` | `u16` | RW | P | nie | M | 16–255 | `96` |

Próg, po którego przekroczeniu węzeł emituje `BusDegraded` (§4). Wartość domyślna `96`
jest progiem ostrzegawczym przyjętym w kontrolerach CAN — na tyle wysoko, żeby nie reagować
na pojedyncze zakłócenie, i na tyle nisko, żeby zostało zapasu do `127`, gdzie zaczyna się
`PASSIVE`.

---

## 3. Komendy

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | `ResetCounters` | — | M |

Zeruje liczniki trwałe: `BusOffCount`, `TxDropped`, `RxOverruns`.

**Nie zeruje** `TxErrorCount` ani `RxErrorCount` — te należą do kontrolera i zmieniają się
wyłącznie według reguł warstwy łącza. Węzeł nie ma jak ich sfałszować i nie powinien mieć.

Komenda służy jednej rzeczy: wyzerowaniu stanu po naprawie, żeby dało się sprawdzić, czy
naprawa poskutkowała. Liczniki, których nie da się wyzerować, po roku znaczą tylko tyle,
że kiedyś było źle.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet |
|---|---|---|---|
| `0x01` | `BusDegraded` | `tec: u16`, `rec: u16` | `WARNING` |
| `0x02` | `BusRecovered` | `busOffCount: u16`, `downtime: u16` [s] | `CRITICAL` |
| `0x03` | `QueueOverflow` | `dropped: u16` | `WARNING` |

`BusDegraded` jest emitowane przy **przekroczeniu** `ErrorThreshold`, raz na przejście —
nie przy każdym błędzie. Powrót poniżej progu z zapasem szesnastu emituje je ponownie
z wartościami niższymi, co w dzienniku czyta się jako koniec epizodu.

`BusRecovered` ma priorytet `CRITICAL` i jedzie jako rodzaj `ALARM`
([`05-mapowanie-can.md`](../05-mapowanie-can.md) §2), bo jest zgłoszeniem awarii węzła —
dokładnie tym, dla czego ten rodzaj istnieje.

### 4.1 Dlaczego nie ma zdarzenia `BusOff`

Węzeł w stanie `BUS_OFF` jest **odłączony od magistrali i nie może nadać niczego** —
łącznie z wiadomością o tym, że odpadł. Zdarzenie zgłaszające odpadnięcie byłoby więc
zdarzeniem, którego nikt nigdy nie zobaczy.

Dlatego węzeł mówi o tym **po powrocie**, a `BusRecovered` niesie czas nieobecności.
Wynika stąd rzecz istotna dla huba: **odpadnięcia węzła nie da się wykryć z magistrali
w chwili, gdy zachodzi.** Wykrywa się je przez milczenie i odpytywanie
([`06-cykl-zycia-urzadzenia.md`](../06-cykl-zycia-urzadzenia.md) §5), a `BusRecovered`
dopiero potem wyjaśnia, co to było.

---

## 5. Zachowanie

### 5.1 Liczniki pochodzą ze sprzętu

`TxErrorCount`, `RxErrorCount` i `BusState` są odczytywane **z kontrolera CAN**, a nie
liczone przez oprogramowanie. Węzeł je przepisuje, nie wylicza.

Ma to znaczenie, bo liczniki warstwy łącza rosną i maleją według reguł, których warstwa
aplikacyjna nie widzi: błąd nadawania podnosi o osiem, poprawna ramka obniża o jeden.
Własna implementacja dałaby liczby podobne, ale nieporównywalne z niczym.

### 5.2 Odpadnięcie od magistrali i powrót

Wejście w `BUS_OFF` następuje przy `TxErrorCount = 255`. Węzeł:

1. przestaje nadawać i odbierać — robi to za niego kontroler,
2. **uruchamia przywracanie automatyczne** i czeka na jego zakończenie,
3. po powrocie odtwarza filtry akceptacji, zeruje kolejkę nadawczą,
4. zwiększa `BusOffCount` i emituje `BusRecovered`.

> **Przywracanie jest automatyczne i obowiązkowe.** Węzeł nie ma prawa wymagać restartu
> ani ingerencji człowieka, żeby wrócić na magistralę.

Powód jest ten sam co przy adresach w pamięci trwałej
([`03-adresacja.md`](../03-adresacja.md) §7): instalacja ma wstawać sama. Węzeł w puszce
pod sufitem, który po zakłóceniu wymaga wyjęcia bezpiecznika, jest węzłem zepsutym,
niezależnie od tego, jak poprawnie zachował się w chwili błędu.

Węzeł po powrocie **nie emituje `Booted`** — nie było restartu, konfiguracja nie została
odtworzona, `Uptime` biegnie dalej. Mylenie tych dwóch rzeczy kazałoby hubowi ponownie
enumerować urządzenie po każdym zakłóceniu.

### 5.3 Przepełnienie kolejki nadawczej

Kolejka nadawcza węzła jest skończona, a magistrala bywa zajęta. Gdy w kolejce brakuje
miejsca, obowiązuje jedna reguła:

> **Porzuca się najstarszy raport. Zdarzeń i odpowiedzi nie porzuca się nigdy.**

Wynika to wprost z rozróżnienia stanu i faktu
([`01-model-danych.md`](../01-model-danych.md) §3). Raport ma następcę — przyjdzie kolejny,
najpóźniej po `ReportInterval`, i przyniesie wartość aktualną, a nie zaległą. Zdarzenie
następcy nie ma: porzucone znika bezpowrotnie. Odpowiedź porzucona zamienia transakcję
w ciszę nieodróżnialną od awarii węzła.

Każde porzucenie zwiększa `TxDropped`. Przekroczenie progu w obrębie jednej sekundy emituje
`QueueOverflow` — co w praktyce znaczy, że albo magistrala jest wysycona, albo węzeł
raportuje za często i trzeba mu podnieść `ReportMinGap`.

### 5.4 Raportowanie liczników

Liczniki błędów są raportowane jak każdy inny atrybut, z **domyślną histerezą `16`**
i `ReportInterval` **300 s** ([`01-model-danych.md`](../01-model-danych.md) §6).

Histereza jest tu obowiązkowa z tego samego powodu co w czujnikach: `TxErrorCount` drga
przy każdej udanej i nieudanej ramce, a diagnostyka, która sama obciąża magistralę,
przeczy własnemu celowi.

### 5.5 Stan początkowy

Po starcie liczniki trwałe są odtwarzane z pamięci, a ulotne zerowane. `BusState` jest
odczytywane z kontrolera od razu po jego inicjalizacji, więc nie przyjmuje wartości „brak" —
stan magistrali jest znany zawsze, nawet gdy jest zły.

---

## 6. Jak czytać liczniki

Tabela dla człowieka stojącego przy instalacji, nie dla implementacji:

| Objaw | Prawdopodobna przyczyna |
|---|---|
| `TxErrorCount` rośnie powoli na **jednym** węźle | zły styk, uszkodzona żyła, złe zakończenie odcinka |
| `TxErrorCount` rośnie na **wszystkich** węzłach linii | brak albo nadmiar terminatora, za długi odcinek, zła prędkość |
| Błędy narastają **o określonych porach** | zakłócenie od odbiornika dużej mocy: pompa, ściemniacz, indukcja |
| `BusOffCount` rośnie, `TxErrorCount` zwykle zerowy | zakłócenie krótkie i silne; magistrala zdrowa między epizodami |
| `RxOverruns` rosną tylko na jednym węźle | za wolna obsługa przerwań w firmwarze tego węzła |
| `TxDropped` rosną | węzeł raportuje częściej, niż magistrala jest w stanie przyjąć |
| `SupplyVoltage` spada przy załączeniu przekaźników | niewydolne zasilanie linii; sprawdź `LastResetReason` |

Zasada ogólna: **liczniki porównuje się między węzłami tej samej linii**, a nie z zerem.
Instalacja, w której wszystkie węzły mają po kilkanaście błędów dziennie, jest zdrowa.
Instalacja, w której jeden ma ich tysiąc, a reszta zero, ma dokładnie jeden problem
i wiadomo, gdzie leży.

---

## 7. Reprezentacja poza magistralą

`Diagnostics` nie jest funkcją urządzenia i nie odpowiada niczemu, co użytkownik obsługuje.
Hub wystawia go jako informacje serwisowe.

Jedno zalecenie niezależne od adaptera: **liczniki błędów mają sens wyłącznie jako szereg
czasowy.** Pojedyncza wartość `TxErrorCount = 24` nie znaczy nic — nie wiadomo, czy to
dwadzieścia cztery błędy przez rok, czy przez ostatnie pięć minut. Wykres odpowiada na to
natychmiast, a liczba w tabeli nie odpowie nigdy.
