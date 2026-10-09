# Rejestr decyzji

Rozdziały mówią, **jak jest**. Ten plik mówi, **dlaczego tak, a nie inaczej** — co było
do wyboru, co odrzucono i z jakiego powodu. Uzasadnienie rozstrzygnięcia jest tym, co
przeżyje autora: bez niego następna osoba odkryje odrzucony wariant na nowo i uzna go za
lepszy pomysł.

Rzeczy jeszcze nierozstrzygnięte nie mają pliku w specyfikacji: sprzeczność znaleziona
przy implementacji idzie od razu do decyzji autora ([`POJECIA.md`](POJECIA.md) §4).

**Jak pisać nowy wpis.** Ręcznie, w tym pliku, w tym samym kształcie co pozostałe:
co wybrano, co odrzucono, dlaczego, i — gdy trzeba — jaki to ma skutek. Wpis zastąpiony
nie znika: dostaje stan „zastąpione" i odsyłacz do następcy. Porządki, poprawki literówek
i przenumerowania nie są decyzjami i tu nie trafiają.

> Do 2026-09-28 ten plik był generowany z wiadomości commitów. Generowanie zostało
> usunięte, a treść przesiana: z 74 surowych wpisów zostały rozstrzygnięcia, odwrócone
> decyzje połączono w jeden wpis, porządki wypadły.

---

## 1. Zakres i założenia

### Specyfikacja opisuje standard, nie instalację

**Obowiązuje** · [`00`](00-wprowadzenie.md) · 2026-09-09

- **Wybrano:** warstwa fizyczna opisana ogólnie — magistrala niesie zasilanie i parę
  różnicową; kabel, napięcie i topologia to decyzje wdrożeniowe. W miejsce „gatewaya"
  pojęcie **huba**: urządzenia prowadzącego logikę sieci, obsługującego kilka magistral,
  z wymiennymi adapterami.
- **Odrzucono:** skrętkę, 24 V, rezerwę RS485, odwołania do STM32F103 i mapowanie na
  Home Assistant zapisane w specyfikacji.
- **Dlaczego:** specyfikacja przywiązana do jednej płytki i jednego systemu nadrzędnego
  przestaje być czymkolwiek więcej niż opisem jednej instalacji.

### Urządzenia nie rozmawiają ze sobą — i to nie jest system automatyki

**Obowiązuje** · [`00`](00-wprowadzenie.md) · 2026-09-11

- **Wybrano:** ruch idzie zawsze przez hub. Zakres to obsługa urządzeń plus pula prostych,
  szybkich powiązań w hubie (klawisz → przekaźnik). Bez harmonogramów, warunków, pory dnia
  i trybów domu — to robi Home Assistant albo Node-RED.
- **Odrzucono:** komunikację węzeł–węzeł (parowanie, tablicę reguł w mikrokontrolerze),
  także „na później".
- **Dlaczego:** ramka nie opuszcza magistrali, na której powstała, więc parowanie działałoby
  tylko w obrębie jednej magistrali — a wymagałoby tablicy reguł w każdym węźle i drugiej ścieżki
  sterowania do osobnego diagnozowania. Powiązania w hubie uzasadnia wyłącznie opóźnienie:
  kilka milisekund przez hub wobec dziesiątek albo setek przez system nadrzędny.
- **Skutek:** endpoint 2 przestał być rezerwą pod tablicę powiązań w węźle (dziś ma na nim
  typ `Groups`).

### Wyjątek: pętla regulacji w węźle

**Obowiązuje** · [`00`](00-wprowadzenie.md) · 2026-09-15

- **Wybrano:** regulator (typ `Thermostat`) prowadzi pętlę w węźle, bez huba.
- **Dlaczego:** nie opóźnienie, tylko **czas przeżycia**. Pętla grzewcza jest wolna
  i nikogo nie obchodzi, czy zareaguje po dziesięciu czy po dwustu milisekundach — ale dwa
  dni bez serwera to niewygoda przy oświetleniu i awaria przy ogrzewaniu.
- **Granica:** węzeł **nie zna czasu kalendarzowego**. Harmonogram zmienia mu jedną liczbę
  z zewnątrz.

### Wymiana urządzenia poza zakresem v1

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) · 2026-09-11

- **Wybrano:** uszkodzony moduł wymienia się przez usunięcie starego i dodanie nowego;
  konfigurację ustawia się od nowa.
- **Odrzucono (odłożono):** zachowanie ciągłości — rezerwowanie adresu i odtwarzanie
  ustawień z kopii.
- **Dlaczego:** to osobny mechanizm z własnymi przypadkami brzegowymi; odłożony świadomie,
  a nie wpychany w v1.

### Poza v1

**Obowiązuje** · 2026-09-28 · przeniesione z likwidowanego `OTWARTE.md`

Nie są to luki — są to rzeczy, których v1 **nie będzie** robić. Wymiana modułu — wpis wyżej;
rozmowy między węzłami są rozstrzygnięte przeciw, nie odłożone (wyżej, „Urządzenia nie
rozmawiają ze sobą").

| Co | Dlaczego odłożone |
|---|---|
| Zabezpieczenie kryptograficzne magistrali | magistrala biegnie w ścianie; kto ma do niej dostęp, ma większe możliwości ([`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) §2.1) |
| Wzorzec „dwuklik i przytrzymaj" | pole w `HoldStart` zarezerwowane ([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §5.4) |
| Nastawa wejściowa w jednostkach fizycznych | ścienne pokrętło zadające 21,5 °C nie mieści się w [`ValueInput`](types/0x0011-value-input.md) §5.1, bo ten zna wyłącznie promile; wymaga pola `Quantity` jak w [`Sense`](types/0x0030-sense.md), czyli nowej cechy albo nowej rewizji |
| Aktualizacja firmware przez magistralę | segmenty jej nie uniosą — 1536 B to nie jest obraz programu; wymaga własnego mechanizmu ([`05-mapowanie-can.md`](05-mapowanie-can.md) §6.9) |

---

## 2. Model danych

### Typ endpointu zamiast klastra

**Obowiązuje** · [`01`](01-model-danych.md) §2 · 2026-09-10

- **Wybrano:** endpoint ma **dokładnie jeden** typ — nazwany kontrakt z atrybutami,
  komendami i zdarzeniami, parametryzowany cechami.
- **Odrzucono:** słowo i model „klastra" z Zigbee i Matter.
- **Dlaczego:** tam endpoint skupia kilka klastrów, więc trzeba osobno nazwać pojemnik
  i zawartość. U nas pojemnik i zawartość są tym samym, a słowo „klaster" sugerowałoby
  możliwość, której nie ma. Zmiana była wyłącznie terminologiczna — ani jeden bit się nie
  zmienił.

### Kanał fizyczny zamiast przywrócenia klastrów

**Obowiązuje** · [`01`](01-model-danych.md) §5 · 2026-09-11

- **Problem:** deskryptor był płaską listą. Dla urządzenia wielokanałowego nie dało się
  wyrazić, że pomiar prądu z ep8 dotyczy wyjścia z ep4. Oddając współlokację klastrów,
  oddaliśmy nośnik relacji.
- **Wybrano:** atrybut wspólny `Channel` (0xF5, RO). `Sense` z `Channel = N` mierzy skutek
  kanału N; `Channel = 0` znaczy „samodzielny", nie „nieznany".
- **Odrzucono:** przywrócenie klastrów. Trzy powody, od najsilniejszego: nie ma ich gdzie
  zapisać (29 bitów identyfikatora bez wolnego, najciaśniejszy ładunek zajęty prawie
  w całości); rozbiłyby dopasowanie powiązań, które dziś idzie po trójce z identyfikatora
  bez zaglądania do ładunku; i tak nie rozwiązują przypadku „w jakiej roli" — Matter doszedł
  do tego samego i dołożył znaczniki semantyczne **obok** klastrów.
- **Dlaczego zero znaczy „samodzielny":** inaczej każde urządzenie byłoby dwuznaczne z urzędu.
- **Skutek:** `Channel` mówi, **którą** rzeczą fizyczną endpoint jest; **czym** ona jest,
  mówi `Purpose`. Stąd `INDICATOR` w `Output.Purpose` — podświetlenie panelu deklarujące
  `LIGHT` gasłoby przy „zgaś wszystkie światła". Koszt: jeden odczyt więcej na endpoint przy
  enumeracji, zero bajtów w ramkach roboczych.
- **Sprawdzone użyciem:** pierwszy typ prowadzący pętlę (`Thermostat`) wiąże czujnik,
  regulator i wyjście zwykłym numerem kanału — kanał nie potrzebował niczego więcej (W14).

### Rozróżnialność endpointów

**Obowiązuje** · [`01`](01-model-danych.md) §2.2 · 2026-09-11

- **Wybrano:** dwa endpointy nierozróżnialne w deskryptorze, a znaczące co innego, to
  **brakujący atrybut w typie**, nie powód do katalogu per model.
- **Dlaczego:** katalog, bez którego hub nie umie poprawnie pokazać danych, jest bazą
  konwerterów — dokładnie tym, czego protokół samoopisujący się ma unikać.
- **Sprawdzone:** reguła raz już czegoś nie przepuściła — `Meter` ma kierunek jako cechę
  właśnie przez nią (niżej).

### Cecha wybiera z typu, niczego nie dokłada

**Obowiązuje** · [`01`](01-model-danych.md) §2.1 · 2026-09-13

- **Wybrano:** typ opisuje wszystko, co endpoint danego rodzaju może potrafić; cecha
  **wybiera** z tego, co typ już definiuje.
- **Odrzucono:** sformułowanie „cecha włącza dodatkowe atrybuty", sugerujące, że cecha
  wnosi coś spoza typu.
- **Dlaczego:** jeden typ obsługuje całą rodzinę urządzeń (przekaźnik, ściemniacz, taśmę)
  zamiast rozpadać się na osobny typ dla każdego.

### DeviceType jest tożsamością modelu, nie opisem zdolności

**Obowiązuje** · [`types/0x0001-device.md`](types/0x0001-device.md) · 2026-09-11

- **Wybrano:** deskryptor odpowiada na pytanie **co urządzenie potrafi**, `DeviceType` —
  **czym jest**. Tożsamością modelu jest para (`VendorId`, `DeviceType`); `VendorId`
  obowiązkowy. Katalog `devices/` opisujący zdolności zastąpiony rejestrem modeli.
- **Dlaczego:** tej pary nie da się wyprowadzić z zachowania, a jest potrzebna do
  aktualizacji firmware (dwa produkty mogą mieć identyczny deskryptor i niekompatybilny
  plik), części zamiennej i pochodzenia. Opis zdolności w katalogu byłby czymś, czego nikomu
  nie wolno stamtąd brać — odczyt z węzła i tak rozstrzyga.

### Przestrzeń producencka typów

**Obowiązuje** · [`registry/endpoint-types.yaml`](registry/endpoint-types.yaml) · 2026-09-11

- **Wybrano:** typy endpointów producenta w 0x8000–0xFFFE; **zakaz** atrybutów
  producenckich w typach standardowych.
- **Dlaczego:** jedyna rzecz, której po fakcie nie da się wprowadzić. Bez niej pierwszy obcy
  autor potrzebujący typu spoza katalogu weźmie wolny numer standardowy — i drugi też.
  `Output` u jednego autora i u drugiego musi znaczyć to samo, bo na tym stoi
  samoopisywalność.

### Ten sam fakt jako stan i jako zdarzenie — tylko dla decyzji sterujących

**Obowiązuje** · [`01`](01-model-danych.md) §3 · 2026-09-15, uogólnione 2026-09-16

- **Reguła wyjściowa:** jednego faktu nie opisuje się dwiema wiadomościami, bo mogą się
  rozjechać (`Contact`).
- **Wybrano wyjątek:** wolno zdublować stan zdarzeniem, gdy zmiana jest **decyzją
  sterującą**, a nie obserwacją — i tylko razem z rozstrzygnięciem sporu: **przy
  rozbieżności obowiązuje raport**. Zdarzenie może przepaść i nie jest powtarzane; raport
  wraca cyklicznie.
- **Dlaczego:** zdarzenie jedzie z priorytetem 0x1, raport na 0x8 — na końcu stawki.
  Dla sygnału, od którego zależy czyjeś zachowanie, to złe miejsce. `Thermostat` z
  `DemandChanged` daje dosłownie ten sam wzorzec co klawisz z `Click`, więc silnik powiązań
  nie musi ich odróżniać.
- **Uogólnienie:** z wyjątku korzystają z zasady wszystkie wejścia, w których zmiana jest
  decyzją człowieka (`ValueInput`, `ToggleInput`). Drugi powód: raport ze zmiany podlega
  histerezie i `ReportMinGap`, które tłumią szum przetwornika — a zastosowane do palca
  zjadłyby pojedyncze kliknięcie.
- **Skutek dla huba:** przy typie, który celowo dubluje sygnał, hub wiąże **zdarzenie**.
  Wiązanie obu wysłałoby komendę dwa razy.

### Raportowanie: wyzwalacze działają jednocześnie

**Obowiązuje** · [`01`](01-model-danych.md) §6 · 2026-09-13

- **Wybrano:** `ReportInterval` i `ReportHysteresis` działają **jednocześnie**. Histereza
  dotyczy wyłącznie wartości liczbowych, a `0` ma zdefiniowane znaczenie.
- **Odrzucono:** tryb rozłączny („albo interwał, albo histereza").
- **Dlaczego:** czujnik z odświeżaniem pięciominutowym zgłaszałby pożar średnio po dwóch
  i pół minuty.

### Endpointy systemowe: ep0–ep3

**Obowiązuje** · [`01`](01-model-danych.md) §1.2 · 2026-09-11, ep2 2026-09-13

- **Wybrano:** numer i typ endpointu systemowego ustala specyfikacja; `Device` na ep0,
  `Diagnostics` na ep1, `Groups` na ep2 — obecne **zawsze** — i `Scenes` na ep3, obecne
  wtedy i tylko wtedy, gdy węzeł ma jakieś wyjście.
- **Odrzucono:** regułę „endpointy systemowe są identyczne w każdym węźle" (łamało ją
  `Scenes`) oraz obecność warunkową `Groups`.
- **Dlaczego:** obecność `Scenes` jest **wyliczalna** z deskryptora, więc hub nadal niczego
  nie odpytuje. `Groups` w węźle bez wyjść deklaruje `GroupCapacity = 0` — obecność warunkowa
  kosztowałaby hub kolejną regułę, a oszczędziłaby kilkanaście bajtów.

### Endpointy systemowe mają atrybuty wspólne

**Obowiązuje** · [`01`](01-model-danych.md) §4.1 · 2026-09-28

- **Wybrano:** pełny zestaw `0xF0`–`0xFA` na **każdym** endpoincie, także systemowym.
  Na systemowych `Channel` jest zawsze `0`, a `Enabled` zawsze `1` — zapis `0` dostaje
  `INVALID_VALUE`.
- **Odrzucono:** (a) zawężenie wyjątku do samego `Channel` bez ustalenia `Enabled` —
  zostawiało wyłączalny `Device`; (b) własne atrybuty raportowania w typie `Diagnostics`,
  spoza zakresu wspólnego — dwa numery w przestrzeni typu i drugi mechanizm tego samego;
  (c) podział atrybutów wspólnych na „zawsze obecne" i „tylko funkcjonalne" — nowe
  pojęcie w modelu dla jednego przypadku.
- **Dlaczego:** `Diagnostics` ma domyślny `ReportInterval` i histerezę, a próg ciszy węzła
  wylicza się z najkrótszego `ReportInterval` wśród jego endpointów. Panel klawiszowy
  raportuje wyłącznie diagnostykę — bez atrybutów wspólnych na ep1 nie miałby progu,
  a wykrywanie nieobecności straciłoby oparcie. Jednolity zestaw jest też tańszy
  w implementacji niż wyjątek: hub zakładał go od początku.
- **Skutek:** zdanie, że atrybuty wspólne ma „wyłącznie endpoint funkcjonalny", wypadło
  z opisu widoku kanałów; endpointy systemowe hub odróżnia po numerze, nie po kanale.

---

## 3. Adresacja

### Adres jest niepowtarzalny w całej instalacji

**Obowiązuje** · [`03`](03-adresacja.md) §2.1 · 2026-09-09 (trzy podejścia tego samego dnia), uzasadnienie poprawione 2026-09-13

- **Wybrano:** adresacja **globalna** — jeden adres na całą instalację, niezależnie od
  magistrali.
- **Odrzucono:** adresację lokalną dla magistrali (każda magistrala z własną pulą). Była
  przyjęta na kilka godzin: pojemność rosła z liczbą magistral, dołożenie magistrali nie
  wymagało uzgodnień. Cofnięta, bo adres przestawałby wskazywać węzeł bez numeru magistrali.
- **Dlaczego — prawdziwy powód:** sam adres wskazuje węzeł w całej instalacji, więc ani baza
  huba, ani powiązania, ani dziennik nie muszą nieść numeru magistrali, a węzeł przełożony na inną
  magistralę nie zmienia klucza, pod którym jest zapisany.
- **Powód odrzucony po drodze:** „hub przepisuje ramkę między magistralami bez tłumaczenia".
  Nieprawdziwy — hub niczego nie przepisuje (niżej), więc nie mógł niczego uzasadniać.
- **Skutek:** ten sam adres na dwóch magistralach **jest konfliktem**, a wykryć go może
  wyłącznie hub (§6).

### Adres 11-bitowy; numerowanie blokami jest mechanizmem priorytetu

**Obowiązuje** · [`05`](05-mapowanie-can.md) §1.2 · 2026-09-10

- **Wybrano:** `RODZAJ(4) ADRES(11) ENDPOINT(6) ELEMENT(8)` = 29 bitów; `Tid` przeniesiony
  do ładunku. Hub 0x7FE, rozgłoszenie 0x7FF, brak adresu 0x000.
- **Odrzucono:** adres 8-bitowy z `Tid` w identyfikatorze.
- **Dlaczego:** `Tid` służy wyłącznie do kojarzenia odpowiedzi i nikt nie filtruje po nim
  sprzętowo, więc identyfikator go nie potrzebuje. W odpowiedzi dzieli bajt z kodem wyniku,
  więc odpowiedź nie urosła ani o bajt. Zysk: 253 → 2045 węzłów.
- **Skutek najważniejszy:** arbitraż w obrębie rodzaju wygrywa niższy adres, więc bloki
  adresowe stają się priorytetem bez żadnego dodatkowego pola: 0x001–0x0FF sterowanie,
  0x100–0x3FF czujniki, 0x400–0x7FD rezerwa.

### Ramka niesie jeden adres

**Obowiązuje** · [`04`](04-interakcje.md) §1 · 2026-09-09

- **Wybrano:** jeden adres węzła; rodzaj wiadomości mówi, czy jest to nadawca (raport,
  zdarzenie, odpowiedź), czy odbiorca (odczyt, zapis, komenda). Drugą stroną jest zawsze hub.
- **Odrzucono:** adres nadawcy i odbiorcy w każdej ramce.
- **Dlaczego:** dwa adresy wymagałyby 34 bitów z 29. Na CAN każdą ramkę i tak odbierają
  wszyscy, a pole adresu jest podpowiedzią do filtrowania.

### Hub jest aktorem, nie repeaterem

**Obowiązuje** · [`03`](03-adresacja.md) §4.3 · 2026-09-09

- **Wybrano:** hub odbiera zdarzenie, sprawdza powiązania i nadaje **własną** komendę.
  Nigdy niczego nie przepisuje między magistralami.
- **Dlaczego:** repeater miałby sens tylko przy parowaniu węzeł–węzeł, a tego nie ma
  (rozdział 1).

### Konflikt adresów wykrywa hub po interfejsie

**Obowiązuje** · [`03`](03-adresacja.md) §6 · 2026-09-25

- **Problem:** reguła kazała uznać za konflikt „dwa `Booted` z tego samego adresu i różnych
  `ShortId`". `Booted` niesie wyłącznie `resetReason` i `firmwareVersion` — `ShortId` w nim nie
  ma i nie było. Reguła była niewykonalna, a w hubie leżała napisana i niepodłączona.
- **Wybrano:** hub rozpoznaje konflikt po **interfejsie**, którym ramka przyszła. Przy
  adresacji globalnej ten sam adres na dwóch interfejsach sam w sobie jest konfliktem;
  numer magistrali hub ma przy każdej ramce.
- **Dlaczego:** to jedyny konflikt, który może zobaczyć wyłącznie hub — węzły na osobnych
  magistralach nigdy się nie usłyszą, więc samodzielne ustępowanie ich nie ratuje.
- **Zapisane wprost w specyfikacji:** nie szukać tożsamości nadawcy w `Booted`, bo jej tam nie
  ma. Bez tego następna implementacja napisze tę samą martwą regułę — nasza to zrobiła.
- **Dalej:** dwa węzły pod jednym adresem na **jednym** kablu — następny wpis.

### Konflikt adresów: zapobieganie zamiast wykrywania

**Obowiązuje** · [`03`](03-adresacja.md) §6 · 2026-09-29

- **Problem:** konflikt na jednym kablu miały rozstrzygać węzły: kto usłyszy ruch spod
  własnego adresu, zeruje go i przyłącza się od nowa, „ustępuje ten, kto wykrył później".
  Warunek spełniają jednak **oba** węzły naraz — przy wspólnym powrocie zasilania ustępują
  oba, przy przybyszu ustępuje zasiedziały, a dwa identyczne moduły nadają identyczne
  `Booted`, które na CAN nakładają się bit w bit i nie wyglądają jak cudze. Żaden firmware
  tej reguły nie implementował.
- **Wybrano:** reguła wycofana; węzły konfliktu nie wykrywają. Zapobiega hub: **nie
  przydziela adresu, który słyszy na magistrali**, i rozpoznaje węzeł spod nieznanego adresu
  (wpis „Węzeł z adresem, którego hub nie zna"). Zapobiega instalator: **używany moduł przywraca się do ustawień
  fabrycznych przed podłączeniem**.
- **Odrzucono:** zgłoszenie adresu na wzór J1939 Address Claim — węzeł z adresem po każdym
  starcie nadaje `ZGŁOSZENIE` z adresem w bajtach rezerwy, czeka 250 ms i broni adresu; spory
  rozstrzyga niższy `ShortId`, a hub po starcie rozgłasza prośbę o zgłoszenia. Wykrywa
  wszystko, także bez huba — ale dokłada w każdym węźle stan przed `Booted`, obronę z tabelą
  rozstrzygania, `PRZYDZIAŁ` dla węzła z adresem i zmianę filtrów. Instalacja jest stała:
  urządzenia dochodzą raz masowo, potem pojedynczo, a przełożenie używanego modułu jest
  rzadkie. Koszt stały za zdarzenie raz na lata.
- **Przyjęte ryzyko:** używany moduł z adresem **zajętym na tym samym kablu**, wpięty bez
  resetu. Hub przypisze jego ruch znanemu węzłowi i niczego nie zauważy wprost; objawem są
  zderzające się odpowiedzi (ten sam identyfikator, różna treść), czyli przekroczone czasy
  transakcji i rosnące liczniki błędów przy jednym adresie. Gdyby zaczęło się to zdarzać,
  odrzucony wariant opisuje `zadania/zrobione/BUG-01.md` w repozytorium projektu.

### Grupy: 2047 numerów i tablica na ep2

**Obowiązuje** · [`03`](03-adresacja.md) §3.1 · 2026-09-13

- **Wybrano:** grup jest 2047. Przynależność trzyma typ `Groups` na ep2 — tablica wspólna dla
  węzła, wpis to para (endpoint, grupa), `GroupCapacity` ogranicza sumę wpisów.
- **Odrzucono:** atrybut wspólny `Groups` typu `u8[4]`.
- **Dlaczego:** pole ADRES interpretuje się zależnie od rodzaju, więc przestrzeń grup jest
  niezależna od adresów węzłów i poszerzenie nie kosztowało ani bitu. Ale zapis atrybutu
  musi zmieścić się w jednej ramce: `u16[n]` to tylko trzy wpisy — mniej niż było. Tablice
  o zmiennej długości nie są atrybutami (02 §5); `u8[4]` uchodził, bo był malutki.
- **Cena:** filtr sprzętowy na grupę wymaga banku filtrów na każdą grupę. Węzeł w kilkudziesięciu
  grupach musi przyjmować wszystkie ramki grupowe i odsiewać je programowo.

### Pole endpointu w komendzie grupowej nie jest ignorowane

**Obowiązuje** · [`04`](04-interakcje.md) §5.2 · 2026-09-13

- **Problem:** numery komend powtarzają się między typami (`Output.Off` = `Scenes.Store` =
  0x00). Ramka „element 0x00 do grupy 5" znaczyła naraz „zgaś salon" i „zapamiętaj bieżący
  stan jako scenę" — identyczny identyfikator, a jedna z tych operacji nadpisuje dane.
- **Wybrano:** `ENDPOINT = 0` — wykonuje każdy endpoint należący do grupy; `1..63` — tylko ten.
- **Dlaczego zero:** ep0 ma typ `Device`, który komend grupowych nie przyjmuje, więc nic nie
  tracimy. Błąd wyszedł dopiero przy liczeniu konkretnych ramek do `PRZYKLADY.md`.

### Sceny kluczowane parą (grupa, numer)

**Obowiązuje** · [`types/0x0003-scenes.md`](types/0x0003-scenes.md) · 2026-09-13

- **Problem:** grupowe przywołanie sceny nie miało jak zadziałać — `Scenes` siedzi na ep3,
  endpoincie systemowym, który nie należał do żadnej grupy.
- **Wybrano:** model z ZCL — scenę identyfikuje **para** (grupa, numer). Numer grupy jedzie
  w polu adresu ramki grupowej, więc węzeł zna go za darmo. Grupa 0 znaczy „wszystkie wyjścia
  węzła" i przywołuje się ją wyłącznie adresowo.
- **Dlaczego jeszcze:** ziarnistość — ośmiokanałowy przekaźnik może mieć osobną scenę dla
  każdej połowy.
- **Świadomie nie ma:** komendy definiującej scenę wartościami wprost — lista wartości dla
  kilku wyjść nie mieści się w ramce.

### Adres jest trwały

**Obowiązuje** · [`03`](03-adresacja.md) §7 · 2026-09-09

- **Wybrano:** węzeł pamięta przydzielony adres w pamięci trwałej.
- **Dlaczego:** instalacja ma wstawać w dowolnej kolejności, a przyłączanie masowe ma się
  zdarzać tylko przy pierwszym uruchomieniu — nie przy każdym powrocie zasilania.

---

## 4. Przyłączanie i cykl życia

### Identyfikator zgłoszenia wyprowadzony z ShortId

**Obowiązuje** · [`05`](05-mapowanie-can.md) §4.2 · 2026-09-09

- **Problem:** arbitraż CAN jest bezkolizyjny tylko wtedy, gdy identyfikatory się różnią.
  Wszystkie nieprzydzielone węzły nadające z adresu 0x00 zderzałyby się destrukcyjnie
  w polu danych i powtarzały bez końca — 40 urządzeń zablokowałoby magistralę.
- **Wybrano:** ramka przyłączania ma własny układ: rodzaj 0xF, bit kierunku, 24 bity
  `ShortId` w identyfikatorze; **pełny** 32-bitowy `ShortId` powtórzony w ładunku. Przydział
  ma `K = 0`.
- **Dlaczego:** identyfikator służy arbitrażowi i filtrowaniu, ładunek potwierdzeniu
  tożsamości. Przydział z niższym identyfikatorem wyprzedza kolejne zgłoszenia, więc odblokowuje
  węzły po kolei. Kolizja 24 bitów wśród 40 węzłów: ok. 0,005 %.

### NodeClass zamiast DeviceType w zgłoszeniu

**Obowiązuje** · [`05`](05-mapowanie-can.md) §4.1 · 2026-09-17

- **Problem:** hub wybiera blok adresowy — priorytet na całe życie węzła — w chwili, gdy
  nie może z węzła niczego odczytać.
- **Wybrano:** jeden bajt `NodeClass`: `0 UNSPECIFIED` → rezerwa, `1 CONTROL` → 0x001–0x0FF,
  `2 SENSOR` → 0x100–0x3FF.
- **Odrzucono:** `DeviceType` w zgłoszeniu — odpowiadał pośrednio i tylko dla znanego
  producenta, bo wymagał po stronie huba tablicy modeli, której dla obcego urządzenia nie ma.
- **Dlaczego zero to UNSPECIFIED:** wyzerowany bufor daje uczciwe „nie wiem" i adres
  z rezerwy, a nie ciche zajęcie najwyższego priorytetu przez każdy leniwy węzeł.
- **Świadomie:** `NodeClass` **nie jest atrybutem** i nie da się go odczytać. Gdyby był,
  powstałby drugi opis zdolności obok deskryptora. Klasa jest wskazówką, więc ścieżka naprawcza
  (zmiana adresu przez hub) zostaje obowiązkowa.

### Tryb przyjmowania jest asymetryczny

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §2.1 · 2026-09-11

- **Wybrano:** znany `ShortId` dostaje adres **zawsze i bez pytania**; nieznany — tylko przy
  włączonym trybie przyjmowania, który wygasa po 15 minutach. Węzeł oczekujący zgłasza się
  bez końca, więc po włączeniu trybu wejdzie sam.
- **Dlaczego:** wymiana bezpiecznika ani reset fabryczny nie mają wymagać ceremonii, a tryb
  zostawiony otwarty na stałe przed niczym nie chroni.

### Węzeł z adresem, którego hub nie zna

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §2.3 · 2026-09-25, wdrożone 2026-09-29

- **Problem:** węzeł z adresem w pamięci trwałej nie bierze udziału w przyłączaniu,
  a przyłączanie jest jedyną drogą do instalacji. Po utracie bazy huba albo przy węźle
  przeniesionym z innej instalacji taki węzeł pracuje, a instalacja go nie widzi.
- **Wybrano:** hub odczytuje tożsamość spod tego adresu i wystawia węzeł jako
  **OCZEKUJĄCY**; decyduje operator — przyjmuje albo przywraca ustawienia fabryczne.
- **Odrzucono:** ciche przyjmowanie — prostsze o jedną decyzję, ale wtedy tryb przyjmowania
  przestaje chronić przed czymkolwiek.
- **Przy okazji zapisane:** hub ma **czytać** `ShortId` z węzła, nie wyliczać go z `Uid`.
  Wyliczanie zakłada, że węzeł liczy tak samo — nasz firmware nie liczył i nikt tego nie
  widział, dopóki nikt nie policzył dwa razy.
- **Wyzwalacz — każda ramka, nie `Booted`:** hub na Raspberry Pi wstaje po węzłach, więc ich
  `Booted` zwykle przepada. Obowiązkowe raporty `Diagnostics` przychodzą najrzadziej co
  300 s, więc każdy nieznany węzeł pokaże się w ciągu pięciu minut, bez odpytywania.
- **Także przy włączonym trybie przyjmowania** węzeł z adresem czeka na człowieka: tryb
  dotyczy węzłów bez adresu, a ten przyniósł konfigurację, o której hub nic nie wie.
- **Odrzucono 2026-09-29:** zgłoszenie adresu przy starcie (wpis „Konflikt adresów:
  zapobieganie zamiast wykrywania") — rozwiązywało
  też ten przypadek, ale kosztem, który nie odpowiada rzadkości zdarzenia.

### Endpointy funkcjonalne numerowane od 4, bez przerw

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §3.2 · 2026-09-11

- **Wybrano:** endpointy funkcjonalne od 4, ciągle; `EndpointCount` mówi, ile ich jest.
  Wariant sprzętowy bez podzespołu nie zostawia dziury — endpoint istnieje z `Enabled = 0`.
  Endpointy numeruje się w porządku fizycznym urządzenia.
- **Dlaczego:** hub odpytywałby 60 numerów zamiast kilkunastu przy każdym nowym urządzeniu
  i zgadywałby z braku odpowiedzi. Porządek fizyczny rozstrzyga, który z trzech identycznych
  klawiszy jest górny — zero bajtów, zero odczytów.

### Ponowna enumeracja tylko po zmianie firmware

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §3.3 · 2026-09-11

- **Wybrano:** hub enumeruje ponownie tylko wtedy, gdy zmieni się wersja firmware.
- **Dlaczego:** `Booted` niesie `firmwareVersion`, więc decyzja nie kosztuje ani jednej ramki.

### Zmiana adresu: odzyskiwanie po zgubionej odpowiedzi

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §4.3 · 2026-09-11

- **Wybrano:** odczyt `Uid` najpierw spod nowego, potem spod starego adresu. Gdy oba milczą,
  **żadnego** nie wolno przydzielić komu innemu.
- **Dlaczego:** inaczej po powrocie zasilania powstaje konflikt adresów.

### Nieobecność węzła

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §5 · 2026-09-17 (zastępuje wariant z 2026-09-11)

- **Wybrano:** próg ciszy wynika z konfiguracji węzła — **dwa razy najkrótszy niezerowy
  `ReportInterval`**. Po jego przekroczeniu trzy nieudane próby co 10 s oznaczają NIEOBECNY.
  Stałe 300 s zostaje tylko dla węzła z raportowaniem cyklicznym wyłączonym wszędzie.
- **Odrzucono:** stały globalny próg; osobny atrybut „tętna" w `Device` (W5); pierwszy wariant
  z odpytywaniem milczących węzłów przez `Device.Uptime`.
- **Dlaczego:** założenie o istnieniu węzłów milczących było fałszywe — `Diagnostics` na ep1 ma
  w każdym węźle trzy obowiązkowe atrybuty raportowane z domyślnym `ReportInterval` 300 s.
  Czwarty byłby drugim tętnem obok pierwszego. Dwa pominięte raporty, nie jeden, bo pojedynczy
  ginie przy zajętej magistrali. Kto chce wiedzieć szybciej, obniża `ReportInterval` — osobne
  pokrętło dublowałoby to samo i prędzej czy później zaczęłoby mu przeczyć. Odstęp 10 s daje
  restartującemu się węzłowi czas na powrót.

### Usunięcie: zapomnienie w dwóch trybach; zablokowanie osobno

**Obowiązuje** · [`06`](06-cykl-zycia-urzadzenia.md) §6, §8 · 2026-10-02 (zastępuje stan `WYCOFANY` z 2026-09-11)

- **Problem:** stan `WYCOFANY` mieszał dwie rzeczy. Usunięcie miało zostawić w bazie ślad
  „ten `ShortId` może się zgłosić", ale hub i tak traktował go jak nieznany — ślad był
  notatką bez skutków. Implementacja huba pokazała, że skasowany rekord zachowuje się
  identycznie, także dla węzła, który resetu nie dostał: jego adres chroni reguła adresu
  słyszanego, a sam węzeł wraca jako `OCZEKUJĄCY`. Brakowało za to sposobu, by urządzenie
  **zostało** w instalacji i nie było obsługiwane.
- **Wybrano:** usunięcie **zapomina** urządzenie całkowicie i ma dwa tryby, jak w
  zigbee2mqtt — **zwykły**, w którym dopiero potwierdzenie `FactoryReset` cokolwiek usuwa,
  i **wymuszony**, w którym hub wysyła reset i nie czeka. Osobno **zablokowanie**: hub zna
  urządzenie po `Uid`, nie przydziela mu adresu, nie konfiguruje go i ignoruje jego
  zdarzenia; blokada leży w konfiguracji huba.
- **Dlaczego zwykły czeka:** bez potwierdzenia hub nie wie, czy węzeł stracił adres.
  Usunięcie „na ślepo" jako jedyna droga zostawiałoby po każdym usunięciu adres
  zablokowany do restartu huba i węzeł, który za chwilę wróci jako `OCZEKUJĄCY`.
- **Dlaczego jest wymuszony:** moduł zdemontowany albo martwy nigdy nie potwierdzi, a musi
  dać się usunąć.
- **Dlaczego blokada po `Uid`, nie po adresie:** adres zmienia się przy ponownym przyjęciu,
  a `Uid` nigdy. Cena: węzeł zgłaszający się bez adresu podaje tylko `ShortId`, więc hub
  rozpozna blokadę dopiero po odczycie tożsamości.
- **Odrzucono:** „wyciszenie" jako nazwa — sugeruje, że węzeł milknie, a hub nie ma czym
  go uciszyć; węzeł nadaje dalej, to hub przestaje słuchać.
- **Ślad:** `zadania/zrobione/FEAT-04.md` w katalogu projektu.

### Reset fabryczny wymaga argumentu zabezpieczającego

**Obowiązuje** · [`types/0x0001-device.md`](types/0x0001-device.md) · 2026-09-09

- **Wybrano:** `FactoryReset` wykonuje się tylko z argumentem 0x4C41474E. Węzeł traci przy
  nim adres, ale hub zna jego `ShortId` i oddaje mu ten sam bez trybu przyjmowania — reset
  służy naprawie węzła, a nie usuwaniu go z instalacji.
- **Dlaczego:** przypadkowe wyzerowanie węzła w ścianie kosztuje wyjazd z drabiną.

### Każde urządzenie ma przycisk serwisowy i diodę stanu

**Obowiązuje** · [`types/0x0001-device.md`](types/0x0001-device.md) · 2026-10-03

- **Wybrano:** przycisk serwisowy (lokalny reset fabryczny, zabezpieczony przed
  przypadkowym użyciem) i dioda stanu (reset, identyfikacja, usterka magistrali, brak
  adresu, praca — przy kilku naraz wyższy w tej kolejności) są **obowiązkowe** dla
  każdego urządzenia, bez wyjątku dla urządzeń bez miejsca.
- **Dlaczego przycisk:** reset przed podłączeniem był zasadą bez mechanizmu. Jedyną drogą
  był `FactoryReset` z huba, czyli moduł już na magistrali — a gdy przyniesiony adres jest
  zajęty, dwa węzły nadają spod jednego i nie da się ich rozróżnić.
- **Dlaczego dioda i dlaczego kolejność w specyfikacji:** `Identify` bez czego widocznego
  nie odpowiada na pytanie „który to moduł"; montażysta przy rozdzielnicy nie wie, czy
  moduł czeka na adres, czy ma usterkę. Jedna kolejność sprawia, że wszystkie urządzenia,
  także cudze, pokazują w tej samej sytuacji to samo.
- **Odrzucono:** czas przytrzymania w specyfikacji (5 s to wytyczna projektu, nie wymóg —
  zabezpieczenie należy do urządzenia); wzory mrugania i kolory w specyfikacji; wyjątek
  dla urządzeń bez miejsca (pad testowy, reset sekwencją zasilania — ten drugi łatwo
  wywołać migającym zasilaniem); stan „dostał adres" (przydział i `Booted` zachodzą
  naraz) i „brak huba" (węzeł nie zna huba; sam na kablu i tak przechodzi w `PASSIVE`).
- **Ślad:** `zadania/zrobione/CR-05.md` w katalogu projektu.

---

## 5. Interakcje i ramka

### Numer rodzaju jest priorytetem; rezerwa wysoka na 0x2

**Obowiązuje** · [`05`](05-mapowanie-can.md) §2 · 2026-09-10, rezerwa 2026-09-15

- **Wybrano:** RODZAJ na najstarszych bitach identyfikatora, więc numeracja rodzajów **jest**
  hierarchią priorytetów. Alarm na 0x0, zdarzenie na 0x1, **0x2 pusty**, dalej komenda,
  komenda grupowa, zapis, odczyt, odpowiedź, raport (0x8), segmenty, zapytanie, odpowiedź huba;
  przyłączanie na 0xF.
- **Dlaczego rezerwa:** wszystkie wolne wartości leżały poniżej raportu, więc żadnej przyszłej
  wiadomości wymagającej wysokiego priorytetu nie dałoby się dołożyć, a przenumerowanie po
  zamrożeniu v1 łamie zgodność u wszystkich naraz. Wiadomo już, kto się o nią upomni:
  regulator zadający wartość ciągłą (położenie zaworu) nie ma czego wysłać jako zdarzenia.
  Koszt: jedna wartość z szesnastu. (W15)

### Tid, deduplikacja i limit powtarzania

**Obowiązuje** · [`04`](04-interakcje.md) §2.2 · 2026-09-09, naprawione 2026-09-15 i 2026-10-09

- **Wybrano:** powtórzenie z tym samym `Tid` nie wykonuje komendy drugi raz — węzeł odsyła
  zapamiętany wynik. Klucz deduplikacji to `Tid` **razem z endpointem i numerem komendy**,
  okno 300 ms, bufor **co najmniej** 8 wpisów, mieszczący każdą komendę z okna (rozsądnie dwa
  na endpoint przyjmujący komendy). `Tid` liczy się osobno dla każdego klucza i nie wraca
  w obrębie klucza przed upływem okna. Tej samej komendy do tego samego endpointu nie wolno
  wysłać częściej niż osiem razy na 300 ms. `Tid` zostaje na trzech bitach.
- **Odrzucono:** klucz po samym `Tid` z oknem 2 s i buforem 4.
- **Dlaczego:** ściemnianie przytrzymaniem wysyła `Step` co 200 ms — dziesięć komend na dwie
  sekundy przy ośmiu wartościach `Tid`. Dziewiąta kolidowała z pierwszą i była po cichu
  połykana: **ściemnianie zatrzymywało się po 1,6 s**. Okno 300 ms to dokładnie budżet trzech
  prób po 100 ms. Bufor czterech wyrzucałby komendę wciąż mieszczącą się w oknie. Poszerzenie
  `Tid` zabrałoby miejsce kodom wyniku albo zepchnęło najciaśniejszą odpowiedź poza ramkę.
- **Poprawione 2026-10-09 (`zadania/zrobione/BUG-02`):** rozdział o transakcjach zakazywał ponownego
  użycia `Tid` wobec **całego węzła**, a rozdział o deduplikacji mówił, że budżet ośmiu `Tid`
  nie jest dzielony w obrębie węzła. Hub robił to drugie (licznik na adres, endpoint
  i element), a bufor ośmiu wpisów uzasadniano pierwszym („tyle, ile wartości `Tid`"). Przy
  liczeniu na klucz w oknie może przyjść więcej niż osiem różnych komend — moduł ośmiu
  wyjść wyłączany jednym klawiszem dostaje osiem naraz — i dziewiąta wypychała z bufora
  komendę wciąż w oknie, której powtórzenie wykonałoby się drugi raz. Zostało liczenie na
  klucz: liczenie na węzeł dzieliłoby osiem numerów między **wszystkie** transakcje węzła,
  także odczyty, i dławiło odczyt całego urządzenia.
- **Odrzucono przy tym szerszy `Tid`.** Jedyne miejsce to bajt nagłówka: cztery bity `Tid`
  i cztery na wynik dają szesnaście numerów, ale z dziewiętnastu wolnych kodów wyniku
  zostają trzy, a format zmienia się u wszystkich naraz; drugi bajt nagłówka nie wchodzi,
  bo najciaśniejsza odpowiedź zajmuje osiem z ośmiu bajtów. I nie pomaga — miejsca w buforze
  brakuje przez liczbę różnych kluczy w oknie, nie przez szerokość numeru. Wrócić do tego,
  gdy jakiś typ będzie musiał powtarzać tę samą komendę częściej niż osiem razy na 300 ms.

### Komenda jest transakcją i ma odpowiedź

**Obowiązuje** · [`04`](04-interakcje.md) §5 · 2026-09-11

- **Wybrano:** komenda ma `Tid` i odpowiedź, jak odczyt i zapis.
- **Odrzucono:** komendę bez odpowiedzi, potwierdzaną wyłącznie raportem atrybutu.
- **Dlaczego:** bez odpowiedzi komenda **odrzucona** jest nieodróżnialna od **zgubionej**.
  Odpowiedź i raport mówią dwie różne rzeczy: „przyjąłem i wykonałem" oraz „jaki był skutek
  fizyczny". Odpowiedź OK, po której nie przychodzi raport, to przekaźnik, który przyjął
  polecenie i się nie przełączył — jedyny sposób wykrycia zaciętego styku.

### Zdarzenie ma numer kolejny i nie jest powtarzane

**Obowiązuje** · [`04`](04-interakcje.md) §7 · 2026-09-09

- **Wybrano:** zdarzenie niesie licznik kolejny, raport nie. Zgubione zdarzenie nie jest
  powtarzane.
- **Dlaczego:** stan ma wartość bieżącą, fakt nie ma — licznik pozwala hubowi zobaczyć zgubę.
  Spóźniona reakcja na kliknięcie jest gorsza niż brak reakcji.

### Zapis trwały trafia do pamięci przed odpowiedzią

**Obowiązuje** · [`04`](04-interakcje.md) §4.1 · 2026-09-09

- **Wybrano:** OK na zapis atrybutu trwałego znaczy „zapisane", nie „przyjęte".

### Wartości dłuższe niż ramka

**Obowiązuje** · [`05`](05-mapowanie-can.md) §6 · 2026-09-14

- **Problem:** `Device.Uid` ma 8–16 bajtów, a jego odczyt jest krokiem rozpoznania
  urządzenia. Bez mechanizmu nie dało się dodać do instalacji ani jednego węzła.
- **Wybrano:** segmentowanie **nie jest osobną interakcją** — odczyt zostaje odczytem, zapis
  zapisem. Dwa własne rodzaje ramek, po jednym na kierunek, oba **poniżej raportu**. Ładunek
  segmentu: [0] = `LAST` + `Tid`, [1] = numer segmentu, [2..7] = dane; do 256 segmentów,
  1536 bajtów. Segment zerowy unieważnia wszystko odebrane wcześniej.
- **Dlaczego osobne rodzaje, a nie ciąg dalszy `ODPOWIEDZI`:** wyłącznie priorytet. Jako
  odpowiedzi segmenty wygrywałyby arbitraż z każdym raportem i pełny odczyt zagłodziłby raporty
  w całej instalacji na ok. 150 ms. Priorytet w CAN wynika tylko z identyfikatora.
- **Dlaczego `Tid` w segmencie:** kolejność jest darmowa (CAN nie przestawia ramek o tym samym
  identyfikatorze), ale `Tid` wiąże segmenty z transakcją — bez niego nie da się dokończyć
  zapisu, bo odpowiedź nie miałaby jak zostać skojarzona z żądaniem.
- **Nazwy:** `ODPOWIEDŹ_DŁUGA` i `ZAPIS_DŁUGI`, nie `TRANSFER_OUT/IN` — „transfer" sugerował
  osobny mechanizm, a `OUT/IN` jest dwuznaczne. Kod wyniku `SEGMENTED`.
- **Świadomie poza:** aktualizacja firmware. 1536 bajtów to nie obraz programu, a wymagania
  są inne (wznawianie, suma kontrolna, tryb awaryjny).

### Zapytanie: węzeł pyta hub o wartość

**Obowiązuje** · [`04`](04-interakcje.md) §8 · 2026-09-15 (W13)

- **Problem:** termostat potrzebuje temperatury zewnętrznej, której sam nie mierzy.
- **Wybrano:** **zapytanie** jako transakcja na zwykłych zasadach — `Tid`, 100 ms, trzy
  próby. Hub odpowiada **ze swojego modelu, natychmiast**; gdy wartości nie ma, odpowiada
  `UNAVAILABLE` i dopiero wtedy sięga po nią w tle. Typ deklaruje tabelę wejść, a atrybut
  wspólny `QueryEnabled` (bitmapa, domyślnie 0) mówi, które wolno odpytywać. Nie częściej niż
  raz na 10 s dla jednego atrybutu. Zapytanie jest opcjonalne i doradcze — węzeł bez odpowiedzi
  ma działać dalej.
- **Odrzucono:** wypychanie przez hub (hub musiałby bez przerwy odpytywać źródła spoza
  instalacji, żeby mieć czym pchać na czas); pierwszy kształt — niepotwierdzaną „prośbę",
  w której **cisza znaczyła wszystko naraz**; `QueryEnabled` jako jedna flaga na endpoint.
- **Dlaczego flaga mimo ryzyka rozjazdu:** po restarcie huba degraduje się dokładnie do
  zachowania bez flagi, a daje hubowi środek do włączania odpytywania i daje węzłowi sygnał,
  kiedy wolno mu pytać. Flaga mówi „czy wolno pytać" (statyczne), `UNAVAILABLE` — „czy wartość
  jest teraz" (dynamiczne).
- **Pierwszy raz:** węzeł jest stroną inicjującą transakcję — firmware musi umieć prowadzić
  własny `Tid`. Dlatego opcjonalne.

### Kolejka nadawcza i odpadnięcie od magistrali

**Obowiązuje** · [`types/0x0002-diagnostics.md`](types/0x0002-diagnostics.md) · 2026-09-11

- **Wybrano:** przy przepełnieniu kolejki nadawczej porzuca się najstarszy **raport**, nigdy
  zdarzenie ani odpowiedź. Odpadnięcie od magistrali (bus-off) ma przywracanie automatyczne
  i obowiązkowe; zdarzenia `BusOff` nie ma, jest `BusRecovered` po powrocie.
- **Dlaczego:** raport ma następcę, zdarzenie nie; porzucona odpowiedź zamienia transakcję
  w ciszę nieodróżnialną od awarii węzła. Węzeł w bus-off nie może nadać niczego, łącznie
  z informacją o tym.
- **Liczniki błędów jako `u16`:** `u8` rezerwuje 0xFF na „brak", a TEC = 255 znaczy
  odpadnięcie od magistrali — najważniejszy odczyt ze wszystkich.

### Zdania normatywne o ramce tylko w rozdziale 05

**Obowiązuje** · [`00`](00-wprowadzenie.md) · 2026-09-11

- **Wybrano:** w rozdziałach 01–04 CAN występuje wyłącznie jako uzasadnienie.
- **Odrzucono:** deklarację, że warstwa aplikacyjna jest niezależna od CAN.
- **Dlaczego:** nie jest — szerokość adresu, jeden typ na endpoint i jeden adres w ramce
  wynikają wprost z budżetu 8 bajtów i 29 bitów. Uczciwiej to powiedzieć niż udawać.

---

## 6. Typy endpointów

### KeyInput: Click przy zwolnieniu, tryby zamiast flagi

**Obowiązuje** · [`types/0x0010-key-input.md`](types/0x0010-key-input.md) · 2026-09-09

- **Wybrano:** `Click` powstaje **przy zwolnieniu**. Długie naciśnięcie daje `HoldStart`,
  `HoldTick`, `HoldEnd` — bez `Click`. `EventMode`: `CLICK` (domyślny), `MULTICLICK`, `RAW`
  (`Down` i `Up` osobno). Osiągnięcie `MaxClicks` wysyła `Click` od razu, bez czekania na
  okno. `HoldTick` ustaje po 60 s — zablokowany klawisz nie zajmie magistrali.
- **Odrzucono:** `Click` przy naciśnięciu; flagę `MultiClickEnabled`.
- **Dlaczego:** przytrzymanie nie emituje już `Click`, więc nie ma podwójnego zdarzenia do
  odfiltrowania w powiązaniach. `Click` jest tym samym zdarzeniem w `CLICK` i `MULTICLICK`,
  więc przejście między trybami nie unieważnia powiązań.
- **Koszt:** opóźnienie zależy od czasu trzymania palca (typowo 80–150 ms). Reakcja stała
  i natychmiastowa jest w trybie `RAW` przez powiązanie na `Down` — to uzasadnia jego istnienie.
- **Nazwa:** `Key` → `KeyInput` (2026-09-16). Przyrostek odróżnia wejścia obsługiwane przez
  człowieka od `Contact`, który obserwuje świat.
- **Dalej:** które z trzech trybów i przytrzymanie urządzenie w ogóle ma — następny wpis.

### KeyInput: cechy zamiast „każdy klawisz umie wszystko"; strojenie należy do urządzenia

**Obowiązuje** · [`types/0x0010-key-input.md`](types/0x0010-key-input.md) §1 · 2026-09-29

- **Problem:** typ miał siedem atrybutów obowiązkowych i trwałych, a sekcję cech pustą.
  Dzwonek do drzwi, któremu wystarcza `Click`, musiał przechowywać, walidować i obsługiwać
  odczyt i zapis okna wielokliku i progu przytrzymania, których nigdy nie użyje; panel
  trzyklawiszowy — 21 wartości w pamięci nieulotnej. Zasada „wszystko, czym klawisze się
  różnią, jest konfiguracją" była słuszna dla różnic sprzętowych, ale obciążenie brało się
  z czegoś innego: z tego, **co autor urządzenia zbudował**.
- **Wybrano:** kierunek „jak najwięcej implementacji urządzenia". Rdzeń to samo
  `Click(1)`, **zero atrybutów obowiązkowych**. Trzy cechy: `MULTICLICK`, `HOLD`, `RAW` —
  ten sam mechanizm, którym `Output` odróżnia przekaźnik od ściemniacza. `EventMode`
  obowiązkowy przy `MULTICLICK` lub `RAW`. Czasy działania (okno, próg, odstęp)
  **opcjonalne**: urządzenie, które ich nie wystawia, stosuje własne, stałe, w zakresach
  typu. `Invert` i `DebounceTime` **wypadły** — polaryzacja wejścia i odfiltrowanie drgań
  styku to sprawa budowy, o którą martwi się autor urządzenia, nie hub; typ wymaga tylko,
  żeby jedno naciśnięcie było jednym naciśnięciem. Hub **konfiguruje tylko to, co endpoint
  zadeklarował** (`LB-HUB-026`).
- **`HoldEnabled` zostaje** jako jedyny obowiązkowy atrybut `HOLD`. Rozważane było
  wyłączanie przez `HoldThreshold = 0`, ale przy progu opcjonalnym hub nie miałby czym
  wyłączyć przytrzymania — a to jest decyzja o **użyciu** klawisza (klawisz sceny obok
  klawisza oświetlenia), więc należy do huba.
- **Odrzucono:** (a) zostawić jak jest — dzwonek płaci za wieloklik, a biblioteka węzła
  staje się jedyną dopuszczalną implementacją; (b) odchudzić bez cech (wyciąć `HoldEnabled`
  i `MaxClicks`) — 7 → 5, ale tryby nadal obowiązkowe dla wszystkich; (c) dwie cechy
  z `RAW` w rdzeniu — dzwonek nie potrzebuje też `Down`/`Up`.
- **Rewizja zostaje 1** — v1 nie było wydane, kontrakt dopiero się ustala.
- **Przy okazji zapisane wprost:** `Down`/`Up` należą wyłącznie do `RAW`; kliknięcia sprzed
  przytrzymania kasuje `HoldStart`. Oba wynikały z diagramów, ale biblioteka węzła i tak
  robiła inaczej.
- **Świadomie nie opisane:** przypadki brzegowe wejścia — np. klawisz wciśnięty już przy
  starcie węzła. To sprawa implementacji urządzenia, nie kontraktu; specyfikacja mówi, co
  znaczą zdarzenia, a nie jak urządzenie radzi sobie z każdym stanem styku.
- **Ślad:** `zadania/zrobione/CR-01.md` w katalogu projektu.

### Wejścia: Contact, ToggleInput, ValueInput

**Obowiązuje** · [`types/0x0012-contact.md`](types/0x0012-contact.md), [`types/0x0013-toggle-input.md`](types/0x0013-toggle-input.md), [`types/0x0011-value-input.md`](types/0x0011-value-input.md) · 2026-09-09, 2026-09-16

- **Contact** — wejście dwustanowe, którego **stan pochodzi ze świata**. Łącznik bistabilny
  należy tutaj, nie do `KeyInput`. `State = 1` znaczy stan czynny, nie napięcie wysokie.
  `HoldTime` podtrzymuje stan — bez niego czujnik ruchu daje serię impulsów.
- **ToggleInput** — wejście dwustanowe, którego **stan tworzy węzeł** z kliknięć. Dioda idzie
  za stanem wewnątrz węzła. Odrzucono `KeyInput` + `Output INDICATOR`: dwa powiązania na klawisz
  i dioda martwa przy nieczynnym hubie — a panel ma pokazywać stan właśnie wtedy.
- **ValueInput** — wejście trzymające własną liczbę. Zdarzenie niesie wartość **bezwzględną**.
  Odrzucono wzorzec `KeyInput` → `Output.Step`: tam ubytki się kumulują i poziom rozjeżdża się
  na trwałe. Para klawiszy „jaśniej/ciemniej" to **jeden** endpoint — katalog nazywa funkcję,
  nie sprzęt.

### Sense: wielkość jest parametrem

**Obowiązuje** · [`types/0x0030-sense.md`](types/0x0030-sense.md) · 2026-09-09

- **Wybrano:** jeden typ dla wszystkich pomiarów ciągłych; wielkość (`Quantity`) jest
  parametrem urządzenia, skala jest właściwością wielkości. `Value` zawsze po kalibracji.
  Awaria czujnika daje wartość „brak", nie ciszę i nie zero.
- **Odrzucono:** osobny typ na każdą wielkość (w Matter — dziewięć klastrów robiących to samo
  z inną jednostką).
- **Nazwa `Quantity`:** zostaje (2026-09-29). To termin z metrologii — w ISO 80000
  *quantity* to temperatura, *unit* to °C — i odpowiada polskiej „wielkości fizycznej".
  Rozważano `Measure`, `Measurand`, `PhysicalQuantity`, `DeviceClass` (Home Assistant);
  żadna nie jest na tyle lepsza, żeby przepisywać kontrakt i huba, a na magistrali nazwa
  i tak nie jedzie. `Unit` odpada: to inne pojęcie i nazwa zajęta w rejestrze przez
  jednostkę. Ślad: `zadania/zrobione/CR-02.md` w katalogu projektu.

### Meter: kierunek jako cecha, licznik trwały, bez komend

**Obowiązuje** · [`types/0x0031-meter.md`](types/0x0031-meter.md) · 2026-09-15 (W12)

- **Wybrano:** kierunek to cecha `EXPORT`, nie osobny endpoint. Licznik jest **jedynym
  atrybutem stanu w specyfikacji, który musi być trwały**, zapisywany nie częściej niż raz na
  dziesięć minut. Typ **nie ma komend**. Spadek wartości obsługuje hub.
- **Odrzucono:** dwa endpointy na energię pobraną i oddaną — łamały regułę rozróżnialności.
- **Dlaczego:** licznik zerujący się przy mrugnięciu prądu nie jest licznikiem, a wypalona
  komórka kończy życie urządzenia — cena (do dziesięciu minut zliczania) jest właściwa.
  Komenda kasująca byłaby jedną ramką od utraty historii roku; do wyrównania jest `Offset`.
  Węzeł nie odróżni własnego zerowania od wymiany modułu, więc spadek musi rozstrzygać hub.

### Thermostat: pierwszy regulator

**Obowiązuje** · [`types/0x0040-thermostat.md`](types/0x0040-thermostat.md) · 2026-09-15 (W14)

- **Bez temperatury nie reguluje.** Żadnego trybu zastępczego. Przegrzanie podłogówki
  uszkadza wylewkę, wychłodzenie domu jest odwracalne. Nie zastępuje ochrony
  przeciwzamrożeniowej po stronie kotła.
- **Przeterminowanie wejścia jest obowiązkowe.** Wartość sprzed godziny jest gorsza niż jej
  brak, bo wygląda tak samo jak świeża.
- **Wyjście może być na innym węźle — przez hub.** Regulator nadal nie adresuje cudzego
  wyjścia; mówi tylko „grzeje/nie grzeje", a co z tego wynika, rozstrzyga powiązanie w hubie.
  Pierwsza wersja zakazywała wyjścia zdalnego i wykluczała większość realnych instalacji
  (siłownik w rozdzielaczu przy termostacie na ścianie). **Zdalne wyjście musi mieć
  `AutoOffTime`**, a hub odnawia komendę cyklicznie — przy milczącym hubie mechanizm ma
  degradować się w stronę bezpieczną, a nie utrwalać ostatni stan.
- **Nowy blok 0x0040–0x004F — regulacja:** termostat nie jest ani wejściem, ani wyjściem,
  ani pomiarem.

---

## 7. Hub

### Powiązania: jeden krok, na zmianę wartości, w budżecie czasu

**Obowiązuje** · [`07`](07-hub.md) §4 · 2026-09-15

- **Skutek powiązania nie wyzwala kolejnego.** Bez tej reguły pętla powstaje trywialnie —
  wyjście A raportuje, powiązanie włącza B, B raportuje, powiązanie włącza A. Łańcuchy dałoby
  się dopuścić z wykrywaniem cykli, ale byłby to mechanizm trudny do zdiagnozowania
  i niepotrzebny.
- **Powiązanie na atrybut wyzwala się przy zmianie wartości**, nie przy każdym raporcie —
  inaczej odświeżanie cykliczne generowałoby komendy w kółko.
- **Budżet czasu jest wiążący.** Jedyne wymaganie czasowe wobec huba, bo projekt istnieje po
  to, żeby światło zapalało się natychmiast. Liczba — wpis niżej.

### Budżet huba: 50 ms, z progu odczuwalności

**Obowiązuje** · [`07`](07-hub.md) §4.2 · 2026-09-28 · zastępuje „dopasowanie poniżej 1 ms"

- **Wybrano:** od odebrania zdarzenia do przekazania komendy magistrali **najwyżej 50 ms**.
  „Kilka ms" ze wstępu zostaje jako typowy wynik, nie wymaganie. Zakaz kolejkowania
  i grupowania powiązań w czasie — bez zmian.
- **Odrzucono:** dopasowanie poniżej 1 ms, rozpisane na trzy kroki po milisekundzie.
- **Dlaczego:** milisekunda była wzięta z wyobrażenia o sprzęcie, nie z tego, co człowiek
  zauważa. Zwłokę widać od około 100 ms, a `Click` przychodzi 80–150 ms po naciśnięciu —
  wymaganie było sto razy ostrzejsze niż uzasadnienie w katalogu typów tego samego kontraktu.
  Pierwsza implementacja huba mieści się w kilkudziesięciu mikrosekundach, ale zapas ma być
  zapasem, nie wymaganiem.
- **Skutek:** o zgodności rozstrzyga zakaz kolejkowania, a nie liczba — powiązanie przez
  bazę danych łamie wymaganie, choćby zwykle mieściło się w czasie.

### Restart huba: nasłuchiwanie, nie odpytywanie

**Obowiązuje** · [`07`](07-hub.md) §5 · 2026-09-15

- **Wybrano:** po restarcie hub odtwarza stan z raportów. Nie odtwarza zaległych zdarzeń
  i nie zakłada, że wyjścia są w stanie sprzed restartu.
- **Dlaczego:** od tego jest odświeżanie cykliczne. Węzły mogły zostać przełączone ręcznie,
  zrestartować się albo mógł zadziałać `AutoOffTime`.

### Konfiguracja huba jest źródłem prawdy

**Obowiązuje** · [`07`](07-hub.md) §5.3 · 2026-09-16

- **Wybrano:** to, co siedzi w węzłach, jest **odwzorowaniem** konfiguracji huba, nie kopią
  zapasową. Przepisywanie idzie zawsze od huba do węzła. Hub wykrywający rozbieżność albo brak
  własnej konfiguracji zgłasza to operatorowi, zamiast zgadywać z węzłów.
- **Dlaczego — jedna reguła, nie trzy przypadki:** z węzłów wraca **liczba, nigdy znaczenie**.
  Numery grup bez nazw, włączone wejścia bez źródeł, sceny o nieznanej zawartości. Konfiguracja
  odtworzona z samych liczb wygląda na kompletną i nie jest.
- **Wniosek wdrożeniowy:** kopia bazy huba jest kopią całej instalacji, a kopia węzłów nie
  jest niczyją kopią.

---

## 8. Wersjonowanie

### Rewizja typu tylko rośnie

**Obowiązuje** · [`08`](08-wersjonowanie.md) §3 · 2026-09-16

- **Założenie przesądzające o całym rozdziale:** aktualizacja węzła jest niemożliwa. Moduł
  w puszce podtynkowej żyje dwadzieścia lat.
- **Wybrano:** zmiana, która zepsułaby istniejącą implementację, wymaga **nowego
  identyfikatora typu**, a nie nowej rewizji.
- **Odrzucono:** „podnieś rewizję i zaktualizuj wszystkie węzły" — obietnicę, której nikt nie
  spełni.
- **Dlaczego jeszcze:** hub ma wtedy jedną implementację na typ, a rewizja mówi mu tylko, ile
  z typu istnieje w węźle.

### Nieznany kod wyniku jest błędem

**Obowiązuje** · [`08`](08-wersjonowanie.md) §4 · 2026-09-16

- **Wybrano:** nieznany kod wyniku to **błąd, nigdy powodzenie**. Odczyt `ProtocolVersion`
  z ep0 musi działać zawsze, cokolwiek zmieni przyszły major.
- **Dlaczego:** przy odwrotnej regule nowy kod błędu w wersji minor po cichu zepsułby każdy
  starszy hub — dostawałby niepowodzenie i uznawał je za wykonanie. Bez gwarantowanego odczytu
  wersji hub mógłby nieznany węzeł tylko zignorować, nie wiedząc nawet dlaczego.

---

## 9. Prowadzenie specyfikacji

### Rejestr jest źródłem prawdy; tabele są sprawdzane, nie generowane

**Obowiązuje** · [`README.md`](README.md) — Rejestr identyfikatorów · 2026-09-11

- **Wybrano:** identyfikatory mieszkają w `registry/*.yaml`; tabele w markdown zostają jako
  forma dla człowieka, a `registry/check.py` sprawdza ich zgodność, sekcje w odsyłaczach
  i martwe linki. Bez zależności zewnętrznych.
- **Odrzucono:** generowanie tabel z YAML-a.
- **Dlaczego:** ta sama liczba była potrzebna w trzech miejscach naraz i kopie zaczęły się
  rozjeżdżać. Generator ma sens dopiero, gdy format tabel przestanie się zmieniać; sprawdzanie
  działa od pierwszego dnia.
- **Klucze po angielsku** (2026-09-25): rejestr czytają z kodu trzy implementacje, więc polskie
  klucze byłyby polszczyzną zaszytą w każdej z nich. Wartości, które są prozą, zostają po polsku.

### Role dokumentów pomocniczych

**Obowiązuje** · [`POJECIA.md`](POJECIA.md), [`COMPLIANCE.md`](COMPLIANCE.md) · 2026-09-11 – 2026-09-28

- **Rozdzielone:** norma zamraża się, esej pisze się raz, rejestr rośnie co tydzień — więc
  słownik i siła zobowiązań w `POJECIA.md`, status w nagłówku każdego rozdziału.
- **Punktów otwartych nie prowadzi się w specyfikacji** (2026-09-28). `OTWARTE.md` zbierał
  pozycje, które wisiały miesiącami, a rozdziały odsyłały do pozycji, których w nim już
  nie było. Sprzeczność idzie od razu do decyzji autora — bug, zmiana, odłożenie — a to,
  co odłożone, staje się zadaniem projektu. Rozdział opisuje tylko to, co ustalone.
- **`COMPLIANCE.md` nie powiela tabel typów.** Kolumna konformancji przy każdym elemencie typu
  jest kompletną listą wymagań dla tego typu — przepisana dałaby drugą kopię, która by się
  rozjechała. Lista zawiera tylko zdania normatywne rozsiane po prozie. Numeracja jest stała:
  raz nadany numer nie zmienia znaczenia i nie jest używany ponownie.
- **Porównań z Zigbee i Matter nie ma w rozdziałach normatywnych ani w `types/`.** Rozdział
  ma opisywać ten protokół, a nie tłumaczyć go przez inny. Osobny dokument porównawczy był,
  ale wypadł przy porządkowaniu dokumentacji (2026-09-28).
- **Mniej plików, nie więcej** (2026-09-28): usunięte `ROADMAP.md`, `REVIEW.md`,
  `CHANGELOG.md`, `archiwum/` i `bug.md`. Plan pracy żyje w zadaniach projektu, historia
  zmian w gicie, a zasady, które z nich zostały, w tym pliku.

### Typ endpointu powstaje, gdy jest potrzebny

**Obowiązuje** · [`types/`](types/) · 2026-09-28

- **Wybrano:** nowy typ endpointu powstaje wtedy, gdy jest **potrzebny do opisania
  urządzenia, które chcemy zbudować**.
- **Odrzucono:** uzupełnianie katalogu „na zapas" i z góry ustaloną liczbę typów.
- **Dlaczego:** typ napisany na zapas nie ma jak zostać sprawdzony i zastyga z błędami,
  których nikt nie zauważy, dopóki ktoś go nie użyje.
- **Skutek:** katalog nie ma docelowej liczby — narracja mówi o „kilkunastu", a dokładna
  liczba jest tylko w rejestrze.

### Rejestr decyzji pisany ręcznie

**Obowiązuje** · 2026-09-28

- **Wybrano:** ten plik pisze się ręcznie, w stałym kształcie.
- **Odrzucono:** generowanie z wiadomości commitów.
- **Dlaczego:** generowany plik starzał się po cichu (raz był nieaktualny o 40 commitów),
  mieszał decyzje z porządkami i trzymał uzasadnienia w miejscu, które znika przy resecie
  historii. Uzasadnienie ma żyć w pliku.

### „Magistrala", nie „linia"

**Obowiązuje** · [`POJECIA.md`](POJECIA.md) · 2026-09-28

- **Wybrano:** jedno słowo — **magistrala** — także tam, gdzie mowa o przebiegu kabla w domu.
- **Odrzucono:** „linię" jako świadomy synonim.
- **Dlaczego:** dwa słowa na jedną rzecz każą czytelnikowi zgadywać, czy chodzi o dwie
  rzeczy. Kod huba i tak mówi `bus`, a konfiguracja `buses:` — synonim żył tylko w prozie.
