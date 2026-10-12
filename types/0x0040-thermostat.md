# Typ endpointu `0x0040` · Thermostat

> **Stabilne.** Rewizja 1 zamknięta. Pierwszy typ z wejściami i pierwszy, który reguluje.

**Rewizja 1** · regulacja temperatury w jednym obiegu

Utrzymuje zadaną temperaturę, załączając i wyłączając wyjście: zawór ogrzewania
podłogowego, grzejnik elektryczny, siłownik termostatyczny. Wyjście może siedzieć na tym
samym węźle albo na innym — regulator nie widzi różnicy, bo **nigdy nie adresuje go sam**
(§5.4).

> **Jeden endpoint, jeden obieg.** Ogrzewanie podłogowe z czterema pętlami to cztery
> endpointy `Thermostat`, każdy na swoim kanale — a nie jeden z czterema nastawami.

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
| — | *(rdzeń typu, zawsze)* | grzanie: `Mode = HEAT`, histereza, ochrona urządzenia |
| 0 | `COOL` | `Mode = COOL`, regulacja w drugą stronę |
| 1 | `WEATHER` | wejście `OutdoorTemperature`, atrybut `WeatherSlope` |
| 2–15 | — | zarezerwowane, nadawaj `0` |

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `Temperature` | `i16` | RO | V | **tak** | M | na której regulator pracuje |
| `0x01` | `Source` | `enum8` | RO | V | **tak** | M | skąd ona pochodzi, §2.4 |
| `0x02` | `Running` | `bool` | RO | V | **tak** | M | czy wyjście jest teraz załączone |
| `0x03` | `EffectiveSetpoint` | `i16` | RO | V | tak | `[WEATHER]` | nastawa po kompensacji (§5.6) |

`Temperature` jest wartością, na której regulator **faktycznie** pracuje — nie surowym
odczytem żadnego konkretnego czujnika. `Source` mówi, skąd ją wziął, i te dwa atrybuty
czyta się razem.

### 2.2 Wejścia

| Bit | Atrybut | Typ | Dostęp | Konf. | Czym jest |
|---|---|---|---|---|---|
| 0 | `RemoteTemperature` | `i16` | RW, V | O | temperatura z czujnika **poza tym węzłem** |
| 1 | `OutdoorTemperature` | `i16` | RW, V | `[WEATHER]` | temperatura zewnętrzna |
| 2–15 | — | | | | zarezerwowane |

Numery bitów są te, których hub używa w `QueryEnabled`
([`../04-interakcje.md`](../04-interakcje.md) §8.6). Oba wejścia są **ulotne** — po
restarcie mają wartość „brak", dopóki hub ich nie wypełni.

`RemoteTemperature` służy typowej sytuacji: siłownik siedzi w rozdzielaczu, a termometr
w pokoju, na innym węźle. Bez huba te dwie rzeczy nie mają jak się spotkać.

### 2.3 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|
| `0x10` | `Setpoint` | `i16` | RW | P | M | `MinSetpoint`…`MaxSetpoint` | `2000` |
| `0x11` | `Hysteresis` | `u16` | RW | P | M | 10–500 | `50` |
| `0x12` | `MinSetpoint` | `i16` | RW | P | M | — | `500` |
| `0x13` | `MaxSetpoint` | `i16` | RW | P | M | — | `3000` |
| `0x14` | `Mode` | `enum8` | RW | P | M | §2.5 | `0` — `OFF` |
| `0x15` | `MinRunTime` | `u16` [s] | RW | P | O | 0–3600 | `0` |
| `0x16` | `MinIdleTime` | `u16` [s] | RW | P | O | 0–3600 | `0` |
| `0x17` | `SourceTimeout` | `u16` [s] | RW | P | O | 60–3600 | `600` |
| `0x18` | `WeatherSlope` | `u16` | RW | P | `[WEATHER]` | 0–2000 | `0` |

Wszystkie temperatury w setnych stopnia, jak wszędzie
([`../02-typy-danych.md`](../02-typy-danych.md) §3). `Hysteresis` = `50` to pół stopnia.

### 2.4 `Source`

| Wartość | Nazwa | Znaczy |
|---|---|---|
| `0` | `NONE` | **brak temperatury** — regulator nie pracuje (§5.3) |
| `1` | `LOCAL` | z endpointu `Sense` na tym samym kanale |
| `2` | `REMOTE` | z wejścia `RemoteTemperature` |

### 2.5 `Mode`

| Wartość | Nazwa | Konf. |
|---|---|---|
| `0` | `OFF` | M |
| `1` | `HEAT` | M |
| `2` | `COOL` | `[COOL]` |

`OFF` wyłącza regulację i wyjście. Nie jest to to samo co `Enabled = 0`
([`../01-model-danych.md`](../01-model-danych.md) §4): endpoint wyłączony nie raportuje
i nie odpowiada, a termostat w trybie `OFF` raportuje normalnie i widać, że stoi.

---

## 3. Komendy

**Brak.** Wszystko, co da się z termostatem zrobić, jest zapisem atrybutu: zmiana nastawy,
trybu, granic. Komenda `Boost` czy `SetTemporarySetpoint` byłaby początkiem harmonogramu,
a ten należy do systemu nadrzędnego (§5.1).

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Konf. |
|---|---|---|---|---|
| `0x01` | `DemandChanged` | `active: bool` | `INFO` | M |

Emitowane przy **każdej zmianie decyzji regulatora**: gdy zaczyna żądać ciepła i gdy
przestaje. Jest to ta sama rola, jaką przy klawiszu pełni `Click` — sygnał, na który hub
reaguje powiązaniem.

Utrata czujnika osobnego zdarzenia nie ma: widać ją jako zmianę `Source` na `NONE`, a ta
jest raportowana.

### 4.1 Dlaczego zdarzenie, skoro jest `Running`

Jest to wyjątek od podziału na stan i fakt, i jest świadomy, więc wymaga uzasadnienia
mocniejszego niż wygoda. Ten sam wyjątek biorą wejścia obsługiwane przez człowieka
([`../01-model-danych.md`](../01-model-danych.md) §3) — tam jednak wynika on z reguły
dla całej rodziny, a tutaj z pojedynczego rozstrzygnięcia.

Reguła ogólna zabrania takiego dublowania i słusznie
([`0x0012-contact.md`](0x0012-contact.md) §4): dwa opisy jednego faktu mogą się rozjechać.
Ale reguła ta powstała dla **telemetrii** — dla kontaktronu, którego stan nikogo nie
zobowiązuje do działania. Tu jest inaczej:

| | `Contact.State` | `Thermostat.Running` |
|---|---|---|
| Czym jest zmiana | obserwacją | **decyzją sterującą** |
| Czy ktoś musi zareagować | nie | **tak — siłownik ma się ruszyć** |
| Priorytet raportu | właściwy | **za niski** ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §2) |

Raport jedzie z priorytetem `0x8`, czyli na końcu stawki. Dla sygnału, od którego zależy
czyjeś zachowanie, jest to złe miejsce — zdarzenie jedzie z `0x1` i wyprzedza nawet komendy
huba.

Dwie wiadomości pełnią więc **różne role i obie są potrzebne**:

| | Rola |
|---|---|
| `DemandChanged` | **szybka ścieżka** — hub dowiaduje się natychmiast i działa |
| `Running` | **prawda i odtwarzanie** — przeżywa zgubione zdarzenie, wraca cyklicznie |

> **Przy rozbieżności obowiązuje raport.** Zdarzenie może przepaść i nie jest powtarzane
> ([`../04-interakcje.md`](../04-interakcje.md) §7.1); raport przyjdzie znowu najpóźniej po
> `ReportInterval` i to on jest rozstrzygający.

Dzięki tej jednej regule ryzyko, przed którym broni zakaz dublowania, znika: rozjazd jest
możliwy, ale ma jawnego zwycięzcę i sam się naprawia.

---

## 5. Zachowanie

### 5.1 Co ten typ robi, a czego nie robi

> **Jedna pętla, jeden obieg, żadnego kalendarza.**

| Robi | Nie robi |
|---|---|
| utrzymuje nastawę | harmonogramów i pory dnia |
| wybiera źródło temperatury | trybów domu i obecności |
| chroni urządzenie przed taktowaniem | koordynacji między pomieszczeniami |
| kompensuje pogodowo | uczenia się i predykcji |

Granica jest ta sama, którą [`../00-wprowadzenie.md`](../00-wprowadzenie.md) wyznacza dla
całego systemu, i przebiega w jednym miejscu: **regulator nie zna czasu kalendarzowego**
([`../02-typy-danych.md`](../02-typy-danych.md) §3.2). Wszystko, co wymaga wiedzy „która
godzina" albo „czy ktoś jest w domu", zmienia `Setpoint` **z zewnątrz** — i jest wtedy
zwykłym zapisem atrybutu.

To jest cały interfejs między tym typem a automatyką: **jedna liczba, zapisywana przez
kogoś mądrzejszego.**

### 5.2 Skąd bierze temperaturę

W kolejności:

```
RemoteTemperature świeża      → Source = REMOTE
   inaczej: Sense na kanale   → Source = LOCAL
   inaczej:                   → Source = NONE
```

**Zdalna wygrywa z lokalną**, bo jeśli ktoś ją skonfigurował, to właśnie po to: czujnik
w pokoju mierzy lepiej niż termometr w rozdzielaczu obok gorącej rury.

`RemoteTemperature` jest **świeża przez `SourceTimeout`** od ostatniego zapisu. Potem
regulator wraca na czujnik lokalny, a jeśli go nie ma — przechodzi w `NONE`. Przeterminowanie
jest tu obowiązkowe: wartość sprzed godziny jest gorsza niż jej brak, bo wygląda tak samo
jak świeża.

`SourceTimeout` jest **opcjonalny**. Regulator bez wejść zdalnych nie ma czego
przeterminowywać, a regulator z nimi, który go nie wystawia, stosuje własny, stały czas
z zakresu 60–3600 s ([`../01-model-danych.md`](../01-model-danych.md) §8.1).

Źródło lokalne to endpoint [`Sense`](0x0030-sense.md) z `Quantity = TEMPERATURE` **na tym
samym kanale** ([`../01-model-danych.md`](../01-model-danych.md) §5). Kanał jest tu jedynym
spoiwem: mówi, że ten termometr, ten regulator i ten zawór opisują ten sam obieg.

### 5.3 Bez temperatury nie reguluje

> **Przy `Source = NONE` wyjście jest wyłączone i pozostaje wyłączone.**

Regulator, który nie wie, jak jest ciepło, nie ma czym regulować. Nie zgaduje, nie utrzymuje
ostatniej mocy i nie przechodzi w tryb zastępczy z ustalonym wypełnieniem — wyłącza się
i mówi o tym w `Source`.

Wyłączenie jest bezpieczniejsze niż grzanie w ciemno: przegrzanie podłogówki uszkadza
wylewkę, a wychłodzenie domu jest odwracalne. **Nie zastępuje to jednak ochrony
przeciwzamrożeniowej po stronie kotła** — regulator bez czujnika nie ochroni instalacji
przed zamarznięciem i nie jest do tego przeznaczony.

### 5.4 Co regulator załącza

Są dwa układy i typ obsługuje oba. Rozstrzyga jedno: **czy na kanale regulatora jest
endpoint [`Output`](0x0020-output.md)**.

```
ep4  Thermostat  ch1
ep5  Output      ch1     → jest: regulator załącza go sam, bez ramki
```

```
ep4  Thermostat  ch1
     (brak wyjścia)      → nie ma: jedynym wyjściem jest raport Running
```

**Regulator nigdy nie adresuje cudzego wyjścia.** Nie wysyła komendy do innego węzła i nie
zna jego adresu — mówi wyłącznie „grzeję" albo „nie grzeję", atrybutem `Running`. Co z tego
wynika, rozstrzyga hub swoim powiązaniem, dokładnie tak samo jak przy klawiszu
([`../03-adresacja.md`](../03-adresacja.md) §4.3):

```
klawisz          zdarzenie Click              → hub → komenda Toggle
termostat        zdarzenie DemandChanged(1)   → hub → komenda On
```

Jest to **dosłownie ten sam wzorzec**: węzeł mówi, co zaszło, hub przenosi to powiązaniem.
Silnik powiązań w hubie nie musi odróżniać klawisza od regulatora.

Dzięki temu siłownik może siedzieć w rozdzielaczu, na innym węźle i innej magistrali —
a jest to układ typowy dla ogrzewania podłogowego, nie wyjątek.

Sygnałem sterującym jest **zdarzenie**, nie raport — właśnie dlatego, że raport jedzie
z priorytetem `0x8`, czyli na końcu stawki, a zdarzenie z `0x1` (§4.1). `Running` pozostaje
przy tym raportowany i to on jest rozstrzygający przy rozbieżności.

**Wyjście lokalne pozostaje normalnym `Output`em**: hub widzi jego `OnOff`, dostaje raporty
i może je przełączyć komendą. Ręczne przełączenie trwa do najbliższej decyzji regulatora
i nie jest błędem — jest po prostu nadpisane.

#### Sterowanie zdalne wymaga zabezpieczenia

Układ bez lokalnego wyjścia ma słabość, którą trzeba obsłużyć, a nie przemilczeć:
**gdy hub zamilknie z `Running = 1`, zdalne wyjście zostanie załączone na zawsze.**
Regulator dalej liczy poprawnie, ale nikt już nie przenosi jego decyzji.

> **Zdalne wyjście sterowane przez regulator powinno mieć ustawiony `AutoOffTime`**
> ([`0x0020-output.md`](0x0020-output.md) §5.5), a hub — odnawiać komendę cyklicznie.

Wyjście gaśnie wtedy samo, gdy komendy przestaną przychodzić. Jest to ta sama zasada, którą
stosuje się przy odświeżaniu cyklicznym raportów: mechanizm ma się degradować w stronę
bezpieczną, a nie utrwalać ostatni stan w nieskończoność.

### 5.5 Histereza i ochrona urządzenia

```
HEAT:   załącz  gdy  Temperature ≤ EffectiveSetpoint − Hysteresis/2
        wyłącz  gdy  Temperature ≥ EffectiveSetpoint + Hysteresis/2

COOL:   odwrotnie
```

`MinRunTime` i `MinIdleTime` są ważniejsze, niż wyglądają. Zawór strefowy i sprężarka mają
skończoną liczbę cykli, a regulator z małą histerezą przy szybko zmieniającym się odczycie
potrafi taktować co kilkanaście sekund. Wartość `0` wyłącza ochronę i jest właściwa dla
grzania elektrycznego, gdzie przełącza przekaźnik półprzewodnikowy.

Ochrona **wygrywa z histerezą**: regulator, który powinien już wyłączyć, ale nie minął
`MinRunTime`, grzeje dalej. Jest to świadome — przekroczenie nastawy o ułamek stopnia jest
tańsze niż wymiana siłownika.

### 5.6 Kompensacja pogodowa

Przy cesze `WEATHER` regulator podnosi nastawę, gdy na dworze jest zimniej:

```
EffectiveSetpoint = Setpoint + WeatherSlope × (2000 − OutdoorTemperature) / 1000
```

Przy `WeatherSlope = 300` i −10 °C na dworze nastawa rośnie o 9,00 °C ponad `Setpoint`.
Wynik jest zawsze przycinany do `MinSetpoint`…`MaxSetpoint`.

Gdy `OutdoorTemperature` ma wartość „brak" albo jest przeterminowana, **kompensacja nie
działa** i `EffectiveSetpoint` równa się `Setpoint`. Regulator pracuje dalej — kompensacja
jest ulepszeniem, nie warunkiem.

### 5.7 Co działa bez huba

To jest powód, dla którego ten typ istnieje w węźle, a nie w systemie nadrzędnym:

| | Przy sprawnym hubie | Przy hubie wyłączonym |
|---|---|---|
| Pętla regulacji | działa | **działa** |
| Czujnik lokalny na kanale | działa | **działa** |
| **Wyjście na kanale** | działa | **działa** |
| **Wyjście na innym węźle** | działa | **nie działa** — gaśnie po `AutoOffTime` |
| `RemoteTemperature` | świeża | przeterminowana → powrót na lokalny |
| Kompensacja pogodowa | działa | wygasa → `EffectiveSetpoint = Setpoint` |
| Zmiana nastawy | z zewnątrz | ostatnia zapisana, trwała |

Widać stąd, ile kosztuje każdy wybór montażowy. **Czujnik i siłownik na tym samym węźle co
regulator** dają instalację, która grzeje przez tydzień bez huba i nikt tego nie zauważy.
Każdy element przeniesiony na drugą stronę magistrali **dokłada zależność od huba** —
i trzeba to wiedzieć przy projektowaniu, a nie odkryć przy pierwszej awarii.

Jest to wybór projektanta, nie usterka. Dom z siłownikami w rozdzielaczu jest normalny
i działa dobrze; po prostu nie przetrwa tygodnia bez huba.

---

## 6. Konfiguracje typowe

| Zastosowanie | Cechy | Źródło | Uwagi |
|---|---|---|---|
| Podłogówka, czujnik w wylewce | — | `LOCAL` | `MinRunTime` 300 s, siłownik wolny |
| Podłogówka, czujnik pokojowy | — | `REMOTE` + zapasowy `LOCAL` | najczęstszy układ |
| Grzejnik elektryczny | — | `LOCAL` | `MinRunTime = 0`, przekaźnik półprzewodnikowy |
| Obieg z kotłem, krzywa grzewcza | `WEATHER` | `REMOTE` | `WeatherSlope` wg charakterystyki budynku |
| Klimakonwektor | `COOL` | `REMOTE` | `MinIdleTime` 180 s, ochrona sprężarki |
| Siłownik w rozdzielaczu, na innym węźle | — | `LOCAL` albo `REMOTE` | brak wyjścia na kanale; `AutoOffTime` na siłowniku |
| Sterowanie z harmonogramem | — | dowolne | harmonogram **w systemie nadrzędnym**, zapisuje `Setpoint` |

---

## 7. Reprezentacja poza magistralą

System nadrzędny widzi cztery rzeczy: **nastawę**, którą może zmienić, **temperaturę**,
**tryb** i to, **czy grzeje teraz**. To wystarcza do każdej reprezentacji, jaką ekosystemy
smart home dla termostatów mają.

Jedno zalecenie niezależne od adaptera: **`Source` powinien być widoczny**, choćby jako
ikona ostrzegawcza. Regulator, który po cichu przeszedł z `REMOTE` na `LOCAL`, grzeje dalej
i wygląda na sprawny — a mierzy w innym miejscu i utrzymuje inną temperaturę, niż
mieszkaniec ustawił. Jest to jedyna usterka tego typu, która nie objawia się zimnem.
