# Typ endpointu `0x0020` · Output

> **Stabilne.** Relacja `OnOff` ↔ `Level` rozstrzygnięta twardo; komendy są transakcjami.

**Rewizja 1** · sterowane wyjście

Obsługuje wszystko, co się włącza, ściemnia albo koloruje: przekaźnik, ściemniacz
triakowy, wyjście 0–10 V, taśmę LED RGBW, zawór ogrzewania podłogowego, brzęczyk,
sterownik bramy.

W Matter ten zakres pokrywają cztery klastry (`OnOff`, `LevelControl`, `ColorControl`,
`ValveConfigurationAndControl`) i osiem typów urządzeń. Tutaj to jeden typ
z czterema cechami.

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
| — | *(zawsze)* | `OnOff`, komendy `On` / `Off` / `Toggle` |
| 0 | `LEVEL` | `Level`, `LastLevel`, `MinLevel`, `MaxLevel`, `DefaultFadeTime`, komendy `SetLevel` / `Step` / `Stop` |
| 1 | `COLOR_RGB` | `Red`, `Green`, `Blue`, `White`, komenda `SetColor` |
| 2 | `COLOR_CCT` | `ColorTemperature`, komenda `SetColorTemperature` |
| 3 | `PULSE` | `PulseDuration`, komenda `Pulse` |
| 4–15 | — | zarezerwowane, nadawaj `0` |

`COLOR_RGB` i `COLOR_CCT` wymagają `LEVEL`. Zadeklarowanie koloru bez poziomu jest
błędem konfiguracji urządzenia.

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | `OnOff` | `bool` | RO | V | tak | M | — | `0` |
| `0x01` | `Level` | `u16` | RO | V | tak | `[LEVEL]` | 0–1000 ‰ | `0` |
| `0x02` | `Red` | `u8` | RO | P | tak | `[COLOR_RGB]` | 0–254 | `254` |
| `0x03` | `Green` | `u8` | RO | P | tak | `[COLOR_RGB]` | 0–254 | `254` |
| `0x04` | `Blue` | `u8` | RO | P | tak | `[COLOR_RGB]` | 0–254 | `254` |
| `0x05` | `White` | `u8` | RO | P | tak | `[COLOR_RGB]` | 0–254 | `0` |
| `0x06` | `ColorTemperature` | `u16` | RO | V | tak | `[COLOR_CCT]` | 153–500 mired | `370` |
| `0x07` | `Transitioning` | `bool` | RO | V | tak | `[LEVEL]` | — | `0` |
| `0x08` | `LastLevel` | `u16` | RO | P | nie | `[LEVEL]` | 1–1000 ‰ | `1000` |

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `MinLevel` | `u16` | RW | P | nie | `[LEVEL]` | 1–1000 ‰ | `10` |
| `0x11` | `MaxLevel` | `u16` | RW | P | nie | `[LEVEL]` | 1–1000 ‰ | `1000` |
| `0x12` | `DefaultFadeTime` | `u16` | RW | P | nie | `[LEVEL]` | 0–60000 ms | `400` |
| `0x13` | `PowerOnBehaviour` | `enum8` | RW | P | nie | M | §2.3 | `0` |
| `0x14` | `Invert` | `bool` | RW | P | nie | O | — | `0` |
| `0x15` | `PulseDuration` | `u16` | RW | P | nie | `[PULSE]` | 10–60000 ms | `500` |
| `0x16` | `AutoOffTime` | `u16` | RW | P | nie | O | 0–65534 s | `0` |
| `0x17` | `Purpose` | `enum8` | RW | P | nie | M | §2.4 | `0` |

### 2.3 `PowerOnBehaviour`

Co robi wyjście po powrocie zasilania.

| Wartość | Nazwa | Znaczenie |
|---|---|---|
| `0` | `OFF` | pozostaje wyłączone |
| `1` | `ON` | włącza się na `LastLevel` |
| `2` | `RESTORE` | odtwarza stan sprzed zaniku |

`RESTORE` wymaga zapisu stanu do EEPROM przy każdej zmianie. Przy 20 przełączeniach
dziennie i wytrzymałości 10⁶ cykli daje to ponad sto lat, ale zapis musi być
**opóźniony o 5 s od ostatniej zmiany** — inaczej ściemnianie przytrzymaniem klawisza
wypaliłoby komórkę w jeden wieczór.

### 2.4 `Purpose`

Do czego to wyjście fizycznie służy. Typ nie może tego wiedzieć sam — przekaźnik
jest przekaźnikiem niezależnie od tego, czy wisi na nim żarówka czy zawór. Wartość
ustawia typ urządzenia, a użytkownik może ją zmienić.

`Purpose` nie zmienia zachowania typu ani o jotę. Niesie wyłącznie **intencję**:
informację o tym, czym to wyjście jest dla mieszkańca. Korzysta z niej hub, dobierając
sposób prezentacji, domyślne wartości konfiguracji i sensowne reguły — bo „zgaś
wszystkie światła" ma dotyczyć żarówek, a nie zaworów ogrzewania.

| Wartość | Nazwa | | Wartość | Nazwa |
|---|---|---|---|---|
| `0` | `GENERIC` | | `5` | `BUZZER` |
| `1` | `LIGHT` | | `6` | `GATE` |
| `2` | `VALVE` | | `7` | `PUMP` |
| `3` | `HEATER` | | `8` | `INDICATOR` |
| `4` | `FAN` | | | |

`INDICATOR` to sygnalizator: podświetlenie klawisza, dioda stanu, pierścień wokół
enkodera. Wygląda jak światło i jest sterowany jak światło, ale **nie jest światłem** —
i to jest dokładnie ta różnica, dla której `Purpose` istnieje. Bez tej wartości
podświetlenie panelu musiałoby deklarować `LIGHT`, a wtedy „zgaś wszystkie światła"
gasiłoby klawisze w całym domu.

---

## 3. Komendy

Wszystkie kierowane **do węzła**. Każda jest transakcją i dostaje odpowiedź z kodem
wyniku; zmiana stanu wywołuje dodatkowo raport zmienionego atrybutu (§5.4).

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | `Off` | — | M |
| `0x01` | `On` | — | M |
| `0x02` | `Toggle` | — | M |
| `0x03` | `SetLevel` | `level: u16`, `transition: u16` [ms] | `[LEVEL]` |
| `0x04` | `Step` | `delta: i16` [‰], `transition: u16` [ms] | `[LEVEL]` |
| `0x05` | `Stop` | — | `[LEVEL]` |
| `0x06` | `SetColor` | `r, g, b, w: u8`, `transition: u16` [ms] | `[COLOR_RGB]` |
| `0x07` | `SetColorTemperature` | `mired: u16`, `transition: u16` [ms] | `[COLOR_CCT]` |
| `0x08` | `Pulse` | `duration: u16` [ms], `0` = użyj `PulseDuration` | `[PULSE]` |

Argument `transition` równy `0` oznacza zmianę natychmiastową; wartość `0xFFFF`
oznacza „użyj `DefaultFadeTime`".

`SetColor` ze wszystkimi czterema składowymi równymi zero dostaje `INVALID_VALUE` (§5.8),
tak samo jak składowa `0xFF` — to wartość „brak” typu `u8`
([`02-typy-danych.md`](../02-typy-danych.md) §2), nie pełna jasność kanału.

`On`, `Off` i `Toggle` nie mają argumentu `transition`: przy cesze `LEVEL` przechodzą
w czasie `DefaultFadeTime`.

---

## 4. Zdarzenia

**Brak.** Wyjście ma stan, nie fakty — wszystko, co się z nim dzieje, jest widoczne
w raportach atrybutów. To rozróżnienie opisuje [`01-model-danych.md`](../01-model-danych.md) §3.

---

## 5. Zachowanie

### 5.1 Relacja `OnOff` ↔ `Level`

To jest miejsce, w którym Zigbee jest niejednoznaczne i każdy producent implementuje
je inaczej. Tutaj rozstrzygamy je twardo:

> Gdy zadeklarowano cechę `LEVEL`, **`Level` jest jedynym stanem prawdziwym**,
> a `OnOff` jest z niego wyprowadzany: `OnOff = (Level > 0)`.

Nie istnieje stan „włączone, ale z poziomem zero" ani „wyłączone z poziomem 500".

| Komenda | Skutek |
|---|---|
| `Off` | `LastLevel ← Level` (o ile `Level > 0`), potem `Level ← 0` |
| `On` | `Level ← LastLevel` |
| `Toggle` | `Off` gdy `Level > 0`, w przeciwnym razie `On` |
| `SetLevel(0, …)` | równoważne `Off` |
| `SetLevel(v > 0, …)` | `Level ← v`, `LastLevel ← v` |

`LastLevel` nigdy nie przyjmuje zera — dzięki temu `On` po `Off` zawsze zapala światło.
Po `FactoryReset` wynosi `MaxLevel`.

Bez cechy `LEVEL` atrybut `OnOff` jest zapisywalny wprost i nie ma żadnej zależności.

### 5.2 Ograniczenia poziomu

`MinLevel` istnieje, bo poniżej pewnego progu ściemniacz triakowy przestaje zapalać
lampę i zaczyna migotać, a taśma LED gaśnie nierówno.

- `SetLevel(v)` dla `0 < v < MinLevel` ustawia `MinLevel`, nie `v`.
- `SetLevel(v)` dla `v > MaxLevel` ustawia `MaxLevel`.
- `Step` nasyca się na `MinLevel` i `MaxLevel`; **nigdy nie przechodzi przez zero**,
  więc przytrzymanie klawisza ściemniania nie zgasi lampy.
- `Step` przy `Level = 0`: krok w górę zapala na wartości kroku, co najmniej `MinLevel`;
  krok w dół nic nie robi i nie jest błędem. Przytrzymanie „jaśniej” zapala lampę.

Zgasić można wyłącznie jawnie: `Off`, `Toggle` albo `SetLevel(0)`.

### 5.3 Przejścia

Przejście jest liniowe w promilach. W trakcie `Transitioning = 1`.

- Nowa komenda **przerywa** trwające przejście i rozpoczyna nowe od wartości bieżącej.
- `Stop` przerywa przejście i zostawia wyjście na wartości osiągniętej.
- `Stop` bez trwającego przejścia nie robi nic i nie jest błędem.

Wyjście **raportuje każdą zmianę stanu niezależnie od `ReportHysteresis`**
([`../01-model-danych.md`](../01-model-danych.md) §6.2). Zmiana stanu wyjścia jest tu
skutkiem polecenia, a nie pomiarem: nie ma szumu, przed którym histereza miałaby chronić,
a raport o połowicznie wykonanej komendzie byłby gorszy niż jego brak.

**Podczas przejścia atrybut `Level` nie jest raportowany.** Raport idzie na początku
(`Transitioning = 1`) i na końcu (`Transitioning = 0` wraz z wartością docelową).
Gdyby raportować każdy krok, pojedyncze dwusekundowe ściemnianie zalałoby magistralę
setkami ramek — a odbiorcy i tak interesuje wynik, nie przebieg.

### 5.4 Potwierdzanie komend

Komenda dostaje **odpowiedź** z kodem wyniku, a zmiana stanu wywołuje osobno **raport**
zmienionego atrybutu. Dwie wiadomości, dwa różne znaczenia
([`01-model-danych.md`](../01-model-danych.md) §3.2).

Komenda, która nie zmienia stanu — `On` na już włączonym wyjściu — **odpowiada `OK`
i nie wywołuje raportu**. Nie ma czego raportować, a odpowiedź już potwierdziła, że
polecenie dotarło.

Rozbieżność między odpowiedzią a raportem jest sygnałem diagnostycznym: odpowiedź `OK`,
po której **nie przychodzi spodziewany raport**, oznacza przekaźnik, który polecenie
przyjął i się nie przełączył. Jest to jedyny sposób wykrycia zaciętego styku.

### 5.5 Wyłączanie automatyczne

`AutoOffTime > 0` powoduje wyłączenie wyjścia po zadanym czasie od ostatniego
włączenia. Licznik startuje przy każdym przejściu do `Level > 0` i jest zerowany
przez każdą kolejną komendę włączającą.

Typowe zastosowanie: wentylator łazienkowy, oświetlenie garderoby, podlewanie.

### 5.6 Inwersja

Atrybuty `OnOff` i `Level` zawsze opisują **stan odbiornika**, nigdy stan pinu ani cewki.
Między jednym a drugim stoją dwie różne rzeczy i typ traktuje je różnie:

| | czym jest | kto ją zna | w typie |
|---|---|---|---|
| **polaryzacja sterowania** | czy przekaźnik płytki załącza się wysokim, czy niskim stanem pinu | autor urządzenia — zbudował płytkę | **nie ma atrybutu** |
| **styk odbiornika** | czy instalator podłączył odbiornik do styku zwiernego, czy rozwiernego | instalator | `Invert`, opcjonalny |

Polaryzacja sterowania nie zmienia się w czasie pracy i hub nie ma powodu jej znać;
gdyby była zapisywalna z magistrali, jeden zły zapis odwracałby przekaźnik, a z zewnątrz
wyglądałoby to jak zwykły błąd konfiguracji
([`../01-model-danych.md`](../01-model-danych.md) §8.1).

`Invert = 1` znaczy, że odbiornik pracuje na **styku rozwiernym**: przy `OnOff = 1` cewka
jest bez napięcia, a obwód odbiornika zwarty. Instalator wybiera tak wtedy, gdy odbiornik
ma działać także przy martwym węźle — oświetlenie awaryjne, zawór, który ma zostać
otwarty. Moduł z dostępnym stykiem rozwiernym **powinien** wystawiać `Invert`; urządzenie
z jednym stykiem albo bez przekaźnika — nie ma czego wystawiać.

### 5.7 Stan początkowy

Do chwili ustalenia stanu przez `PowerOnBehaviour` wyjście jest fizycznie wyłączone,
a atrybuty mają wartość „brak". Węzeł nie raportuje ich, dopóki nie zakończy odtwarzania
konfiguracji i nie wyemituje `Booted`
([`06-cykl-zycia-urzadzenia.md`](../06-cykl-zycia-urzadzenia.md) §1.1).

### 5.8 Barwa

Przy cesze `COLOR_RGB` stan wyjścia ma dwie niezależne części: **jasność** (`Level`)
i **barwę** (`Red`, `Green`, `Blue`, `White`). Barwa to składowe **przy pełnej jasności**;
to, co świeci, to każda składowa przemnożona przez `Level` / 1000.

> Barwa nie niesie jasności, a jasność nie niesie barwy. `On`, `Off`, `Toggle`,
> `SetLevel` i `Step` działają dokładnie tak jak bez koloru (§5.1, §5.2) i barwy nie
> ruszają; `SetColor` zmienia barwę i jasności nie rusza.

Dzięki temu ściemnianie pokrętłem nie zmienia koloru, a `On` po `Off` zapala w tym samym
kolorze, w którym zgasło.

- **`SetColor` przy zgaszonym wyjściu** zmienia samą barwę i niczego nie zapala. Zapala
  `On` albo `SetLevel`.
- **`SetColor(0, 0, 0, 0)` dostaje `INVALID_VALUE`.** Czarna barwa przy `Level > 0`
  byłaby stanem „włączone, a ciemne", którego §5.1 nie dopuszcza. Gasi się poziomem.
- **Przejście barwy** jest liniowe na każdej składowej osobno. Barwa i poziom mają
  **jedno** przejście: nowa komenda — poziomu albo barwy — przerywa trwające i zaczyna od
  wartości bieżących, `Stop` zatrzymuje oba. Raporty jak w §5.3: `Transitioning = 1` na
  początku, barwa docelowa i `Transitioning = 0` na końcu, bez składowych w trakcie.
- **Barwa jest trwała**, niezależnie od `PowerOnBehaviour`: zapis opóźniony o 5 s od
  ostatniej zmiany, jak przy `RESTORE` (§2.3). `ON` zapala na `LastLevel` w zapamiętanej
  barwie. Po `FactoryReset` barwa jest biała: `254, 254, 254, 0`. Składowa kończy się na
  254, bo `0xFF` to „brak” typu `u8`; różnicy jednego kroku na 255 oko nie widzi.
- **Urządzenie bez białego kanału** — dioda RGB — raportuje w `White` to, co zadano,
  a wykonuje to, dodając `White` równo do czerwonej, zielonej i niebieskiej, z nasyceniem. Atrybuty opisują intencję; jak urządzenie przekłada ją na prąd diod —
  korekcja jasności, kolejność kanałów, ograniczenie prądu — należy do urządzenia.

---

## 6. Konfiguracje typowe

| Urządzenie | Cechy | `Purpose` | Uwagi |
|---|---|---|---|
| Przekaźnik oświetleniowy | — | `LIGHT` | |
| Przekaźnik ogólny | — | `GENERIC` | |
| Ściemniacz triakowy | `LEVEL` | `LIGHT` | `MinLevel` ≈ 100 ‰ |
| Wyjście 0–10 V | `LEVEL` | `LIGHT` | `MinLevel` = 1 ‰ |
| Taśma LED RGBW | `LEVEL \| COLOR_RGB` | `LIGHT` | |
| Diody WS2812 w linii, jedna barwa | `LEVEL \| COLOR_RGB` | `LIGHT` | bez białego kanału — `White` dodawany do RGB (§5.8) |
| Taśma LED CCT | `LEVEL \| COLOR_CCT` | `LIGHT` | |
| Zawór ogrzewania | — | `VALVE` | `PowerOnBehaviour` = `OFF` |
| Zawór proporcjonalny | `LEVEL` | `VALVE` | |
| Sterownik bramy | `PULSE` | `GATE` | `PulseDuration` = 500 ms |
| Brzęczyk | `PULSE` | `BUZZER` | |
| Wentylator łazienkowy | — | `FAN` | `AutoOffTime` = 600 s |
| Podświetlenie klawisza | `LEVEL \| COLOR_RGB` | `INDICATOR` | `Channel` równy kanałowi klawisza |
| Dioda stanu | — | `INDICATOR` | **nie** `LIGHT`; nie należy do wygaszania świateł |

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia to wyjście na zewnątrz, **nie należy do tej specyfikacji** —
zależy od wybranego adaptera północnego, a ten nie jest jeszcze ustalony.

Typ dostarcza hubowi cztery informacje, które do tego wystarczają:

| Informacja | Skąd | Odpowiada na pytanie |
|---|---|---|
| `Purpose` | atrybut `0x17` | czym to jest dla mieszkańca |
| `Channel` | atrybut wspólny `0xF5` | którą rzeczą fizyczną urządzenia to jest |
| `Features` | atrybut wspólny `0xF2` | co da się z tym zrobić |
| stan | `OnOff`, `Level`, barwa (§5.8) | jak jest teraz |

Para `(Purpose, Features)` jednoznacznie określa charakter wyjścia: `LIGHT` bez cech to
zwykły włącznik światła, `LIGHT | LEVEL | COLOR_RGB` to sterownik taśmy, `GATE | PULSE`
to impulsowe wyzwolenie bramy. Przeliczenie poziomu z promili na inną skalę jest
zadaniem huba.
