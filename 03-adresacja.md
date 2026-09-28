# 03 · Adresacja

> **Stabilne.** Przestrzenie adresowe, grupy i procedura przyłączania rozstrzygnięte.

## 1. Poziomy adresowania

Żeby wskazać cokolwiek w instalacji, trzeba odpowiedzieć na trzy pytania:

```
   który węzeł        adres węzła       11 bitów      0x001 … 0x7FD
   która funkcja      endpoint           6 bitów      0 … 63
   co konkretnie      element            8 bitów      atrybut / komenda / zdarzenie
```

Pełny adres elementu to `węzeł.endpoint.element` — na przykład `0x2A.7.0x01` znaczy
„atrybut `0x01` na endpoincie 7 węzła 0x2A". Który to konkretnie atrybut, wynika z typu
endpointu, na którym siedzi
([`01-model-danych.md`](01-model-danych.md) §1.1).

Trzy przestrzenie są **rozłączne**: element `0x01` może być jednocześnie identyfikatorem
atrybutu, komendy i zdarzenia w tym samym typie. Rozróżnia je rodzaj interakcji,
nie numer ([`04-interakcje.md`](04-interakcje.md)).

**Numer magistrali nie występuje w adresie.** Nie musi — patrz §2.1.

---

## 2. Adresy węzłów

Adres ma **11 bitów** ([`05-mapowanie-can.md`](05-mapowanie-can.md) §1.2).

| Wartość | Znaczenie |
|---|---|
| `0x000` | **węzeł bez adresu** — stan węzła, nie adres w ramce (§5) |
| `0x001`–`0x7FD` | węzły, **2045 adresów** |
| `0x7FE` | **hub** |
| `0x7FF` | **rozgłoszenie** |

### 2.1 Adres jest niepowtarzalny w całej instalacji

Instalacja składa się z kilku magistral, ale **pula adresów jest jedna dla całego domu**.
Węzeł `0x02A` jest jeden, niezależnie od tego, do której magistrali jest podłączony.

Numer magistrali nie jest nigdzie przesyłany. Hub wie, na którym interfejsie widzi dany
węzeł, i to mu wystarcza do doręczenia — a skoro adresy się nie powtarzają, nikomu innemu
ta wiedza nie jest potrzebna.

Zysk jest jeden i zasadniczy: **sam adres wskazuje węzeł w całej instalacji**. Hub nie
potrzebuje pary „magistrala + adres" ani w swojej bazie, ani w regułach, ani w dzienniku,
a człowiek czytający log widzi `0x02A` i wie, o które urządzenie chodzi, bez dopytywania
o magistralę.

Nie chodzi natomiast o przekazywanie ramek — **hub ramek między magistralami nie przekazuje
w ogóle** (§4.3). Adresacja lokalna dla magistrali nie wymagałaby więc tłumaczenia adresów
w locie, tylko czegoś gorszego: każdy wpis w bazie huba i każda reguła musiałyby nieść
numer magistrali, a węzeł przełożony na inną magistralę zmieniałby klucz, pod którym jest
zapisany. Przy puli globalnej **przełożenie nie zmienia niczego** (§5.3).

Kosztem jest wspólny sufit **2045 węzłów na całą instalację**, niezależny od liczby
poprowadzonych magistral. Realny szacunek dla dużego domu jednorodzinnego to około stu
urządzeń, więc zapas jest dwudziestokrotny — sufit przestaje być czynnikiem
projektowym.

### 2.2 Tożsamością jest `Uid`, nie adres

Choć adres jest niepowtarzalny, **nie jest tożsamością**. Może się zmienić — przy
przeadresowaniu, po wymianie modułu, po odtworzeniu bazy huba z kopii.

| | Rola |
|---|---|
| `Uid` | **tożsamość** — pochodzi ze sprzętu, niepowtarzalna globalnie, nie zmienia się nigdy |
| adres | **droga** — jak dotrzeć do urządzenia w tej chwili |

Hub prowadzi odwzorowanie `Uid → adres` i **wszystkie swoje reguły, nazwy i konfiguracje
wiąże z `Uid`**. Reguła zapisana „na adres `0x2A`" rozsypie się przy pierwszym
przenumerowaniu; zapisana na `Uid` przeżyje wszystko poza wymianą sprzętu na nowy egzemplarz.

Adres wystarcza natomiast **hubowi** do doręczenia i **człowiekowi** do rozpoznania
urządzenia w dzienniku — i do niczego więcej nie jest potrzebny.

### 2.3 Numerowanie blokami

Arbitraż na magistrali wygrywa niższym identyfikatorem, a adres siedzi w jego górnej
części — **sposób numerowania jest więc mechanizmem priorytetu**, i to jedynym, jakiego
potrzebujemy poza rodzajem wiadomości.

| Zakres | Przeznaczenie |
|---|---|
| `0x001`–`0x0FF` | urządzenia wymagające reakcji: klawisze, wyjścia sterujące |
| `0x100`–`0x3FF` | czujniki raportujące cyklicznie |
| `0x400`–`0x7FD` | rezerwa i rozbudowa |

Klawisz wyprzedza wtedy czujnik temperatury zawsze, bez żadnego dodatkowego pola w ramce.
Mechanikę arbitrażu opisuje [`05-mapowanie-can.md`](05-mapowanie-can.md) §2.

**Blok wybiera się raz, przy przyłączaniu, i węzeł zostaje w nim na całe życie.** Hub nie ma
wtedy jak niczego z węzła odczytać, bo do odczytu potrzebny jest adres — dlatego węzeł podaje
w zgłoszeniu `NodeClass`, jedno pole mówiące wyłącznie, do którego z tych bloków należy
([`05-mapowanie-can.md`](05-mapowanie-can.md) §4.1):

| `NodeClass` | Blok |
|---|---|
| `1` `CONTROL` | `0x001`–`0x0FF` |
| `2` `SENSOR` | `0x100`–`0x3FF` |
| `0` `UNSPECIFIED` | rezerwa `0x400`–`0x7FD`, do przesunięcia po enumeracji |

Klasa **nie opisuje urządzenia** — opisuje wyłącznie pilność jego ruchu. Czym urządzenie
jest i co potrafi, hub dowiaduje się dopiero z deskryptora, już spod nadanego adresu.

### 2.4 Hub

Hub ma adres dobrze znany `0x7FE` i występuje pod nim **na każdej magistrali**. Jest jeden
logicznie, choć fizycznie ma kilka interfejsów.

Stały adres oznacza, że węzeł nie musi go skądkolwiek poznawać — od pierwszej sekundy po
starcie wie, dokąd wysłać zgłoszenie.

### 2.5 Rozgłoszenie

Adres `0x7FF` występuje wyłącznie jako **odbiorca w ramkach od huba** i oznacza wszystkie
węzły na tej magistrali, na której ramka się pojawiła.

Nie dotyczy raportów ani zdarzeń — te niosą adres **nadawcy** i z natury nie wskazują
odbiorcy ([`04-interakcje.md`](04-interakcje.md) §1). Nie ma więc czegoś takiego jak
„raport rozgłoszeniowy": raport po prostu nie mówi, do kogo jest.

**Rozgłoszeniem nie wolno wysyłać zapisów ani komend.** Komenda bez wskazanego adresata
jest nieodróżnialna od pomyłki, a jej skutków nie da się cofnąć. Rozgłoszenie służy
zapytaniom obejmującym całą magistralę — na przykład żądaniu, by wszystkie węzły zgłosiły
swoją obecność.

---

## 3. Adresowanie zbiorcze

### 3.1 Grupy

Numer grupy to `0x001`–`0x7FF`, czyli **2047 grup** — o dwie więcej, niż instalacja może
mieć węzłów. Grupa jedzie w tym samym polu ramki co adres węzła, ale **nie dzieli z nim
przestrzeni**: pole `ADRES` interpretuje się zależnie od rodzaju wiadomości
([`05-mapowanie-can.md`](05-mapowanie-can.md) §2), więc grupa `0x2A` i węzeł `0x2A` nie
mają ze sobą nic wspólnego.

Przynależność prowadzi osobna tablica w węźle, na endpoincie `2`
([`types/0x0004-groups.md`](types/0x0004-groups.md)). Liczba grup przypadających na jeden
endpoint nie jest ograniczona przez specyfikację — ogranicza ją pojemność tablicy, którą
każdy węzeł deklaruje sam w `GroupCapacity`.

Numery grup, tak jak adresy węzłów, **znaczą to samo w całej instalacji**. Grupa 7 to ta
sama grupa na każdej magistrali.

Numer grupy pełni **dwie role naraz**: jest adresem zbiorczym dla komend i zarazem
zakresem sceny — scena jest kluczowana parą `(grupa, numer)`
([`types/0x0003-scenes.md`](types/0x0003-scenes.md) §2). Grupa `0` nie jest przy tym
adresem i nie pojawia się w żadnej ramce; służy wyłącznie jako zakres sceny obejmującej
cały węzeł.

Komenda skierowana do grupy dociera do każdego endpointu należącego do niej **na tej
magistrali, na której została nadana**. Grupa rozciągnięta na kilka magistral wymaga więc,
by hub nadał komendę osobno na każdej z nich — ale z punktu widzenia magistrali nadal
jest to jedna ramka i oszczędność zostaje tam, gdzie ma znaczenie.

Grupy istnieją wyłącznie dla oszczędności. „Zgaś wszystkie światła" w domu z trzydziestoma
obwodami to jedna ramka zamiast trzydziestu — a trzydzieści ramek to nie tylko ruch, lecz
także **widoczne, nierówne gaśnięcie**, bo między pierwszą a ostatnią mija kilkanaście
milisekund.

Grupa jest właściwością **endpointu**, nie węzła. Ośmiokanałowy moduł przekaźnikowy może
mieć cztery kanały w grupie „parter" i cztery w grupie „piętro", a każdy z nich dodatkowo
w grupie „wszystkie światła".

### 3.2 Co wolno wysłać do grupy

Wyłącznie **komendy**. Odczyt skierowany do grupy wywołałby lawinę odpowiedzi
zderzających się na magistrali, a zapis atrybutu do grupy nie ma sensu, skoro to samo
osiąga się komendą.

Komenda grupowa jest **niepotwierdzana**. Nie ma sposobu, by trzydzieści węzłów
potwierdziło jedną ramkę, nie zajmując magistrali na dłużej, niż zajęłoby trzydzieści
osobnych komend. Skutek widać w raportach stanu, które i tak przyjdą.

Wynika stąd praktyczna zasada: **grupy służą wygaszaniu i scenom, nie sterowaniu
wymagającemu pewności.** Pojedyncze światło przełącza się komendą adresowaną.

---

## 4. Granica magistrali

### 4.1 Ramka nie opuszcza swojej magistrali

**Dwa węzły na różnych magistralach nie porozmawiają bezpośrednio. Nigdy.** Nie jest to
ograniczenie protokołu ani adresacji — magistrale są fizycznie rozdzielone i jedynym
urządzeniem widzącym obie jest hub.

Jest to zresztą jeden z powodów, dla których **urządzenia nie rozmawiają ze sobą wcale**
([`00-wprowadzenie.md`](00-wprowadzenie.md) § Kierunek ruchu): mechanizm działający tylko
w obrębie jednej magistrali byłby mechanizmem, którego nie da się polecić.

Cały ruch sterujący przechodzi więc przez hub, a granica magistrali **nie jest granicą
niczego, co widać z zewnątrz**. Klawisz na pierwszej magistrali steruje przekaźnikiem na
trzeciej dokładnie tak samo, jak sąsiadem z tej samej puszki.

### 4.2 Jak dzielić instalację na magistrale

Skoro podział nie wpływa na to, co czym może sterować, decydują o nim trzy inne rzeczy:

| Czynnik | Waga |
|---|---|
| **Długość i topologia kabla** | rozstrzygająca — to fizyka magistrali |
| **Domena awarii** | ważna — patrz niżej |
| Obciążenie magistrali | pomijalna przy tej skali ruchu ([`05-mapowanie-can.md`](05-mapowanie-can.md) §6) |

**Domena awarii** zasługuje na uwagę, bo jest jedynym czynnikiem, o którym łatwo
zapomnieć. Uszkodzenie magistrali wyłącza wszystko, co na niej siedzi — i warto, żeby to
„wszystko" dało się opisać jednym zdaniem.

> **Trzymaj na jednej magistrali urządzenia, które obsługują tę samą część domu.**

Awaria daje wtedy komunikat zrozumiały dla mieszkańca: „piętro przestało działać". Przy
podziale, w którym klawisze są na jednej magistrali, a przekaźniki na drugiej, ta sama awaria
daje objaw znacznie gorszy: **wszystkie klawisze w domu przestają działać, ale światła
nadal reagują na aplikację** — co wygląda na awarię czegoś zupełnie innego.

Ta sama reguła bywa uzasadniana potrzebą parowania urządzeń w obrębie magistrali. **U nas ten
powód nie obowiązuje** — parowania bezpośredniego nie ma. Zostaje powód czytelności
awarii, który jest słabszy, ale nadal prawdziwy.

### 4.3 Hub jest aktorem, nie repeaterem

Hub **nie powtarza ramek między magistralami**. Odbiera zdarzenie z pierwszej magistrali,
sprawdza swoje powiązania ([`07-hub.md`](07-hub.md) §3) i **nadaje własną komendę**
na drugiej. Jest to inna ramka,
w której hub jest nadawcą.

Rozróżnienie ma znaczenie praktyczne: w podglądzie magistrali nigdy nie zobaczysz ramki,
której nadawcą jest węzeł z innej magistrali. Wszystko, co przychodzi z zewnątrz, przychodzi
od huba i jest jako takie oznaczone.

Opóźnienie takiego przeskoku to kilka milisekund — odbiór, dopasowanie powiązania,
nadanie. Jest identyczne dla pary w obrębie jednej magistrali i dla pary rozrzuconej po dwóch,
bo w obu przypadkach ścieżka prowadzi przez hub.

---

## 5. Przyłączanie węzła

Nowy węzeł nie zna swojego adresu. Wie jedynie, kim jest — zna własny `Uid` i wyliczony
z niego `ShortId` ([`types/0x0001-device.md`](types/0x0001-device.md) §2.1).

### 5.1 Zgłasza się tylko węzeł bez adresu

Węzeł, który ma adres w pamięci trwałej, **nie bierze udziału w przyłączaniu**. Startuje,
emituje `Booted` i pracuje.

Ma to zasadnicze znaczenie dla obciążenia: sytuacja, w której kilkadziesiąt urządzeń
zgłasza się jednocześnie, zdarza się **wyłącznie przy pierwszym uruchomieniu instalacji
albo po masowym przywróceniu ustawień fabrycznych**. Zwykły powrót zasilania po awarii
jej nie wywołuje.

### 5.2 Ramki przyłączania mają własny format identyfikatora

Są to **jedyne dwie ramki w całej specyfikacji, które nie niosą adresu węzła** — bo węzeł
go jeszcze nie ma, a węzła bez adresu nie da się zaadresować.

Zamiast adresu **identyfikator ramki zgłoszeniowej jest wyprowadzony z `ShortId`**.
Nie jest to szczegół kosmetyczny, tylko warunek działania całego mechanizmu — patrz §5.4.

### 5.3 Przebieg

```
Faza 1 — start
    adres w pamięci trwałej?
      TAK → emituj Booted, pracuj normalnie.          KONIEC
      NIE → faza 2

Faza 2 — zgłoszenie
    odczekaj losową zwłokę
    nadaj ZGŁOSZENIE
        identyfikator ramki ← wyprowadzony z ShortId
        treść               ← pełny ShortId, NodeClass
    czekaj na PRZYDZIAŁ do 500 ms

Faza 3 — przydział
    hub sprawdza ShortId w swojej bazie:
        znany     → adres, który ten węzeł miał wcześniej
        nieznany  → pierwszy wolny z BLOKU wskazanego przez NodeClass (§2.3)
    hub nadaje PRZYDZIAŁ na tej samej magistrali:
        treść ← ShortId, przydzielony adres (11 b)
    przyjmuje go wyłącznie węzeł o zgodnym ShortId

Faza 4 — zamknięcie
    węzeł zapisuje adres w pamięci trwałej
    emituje Booted spod nowego adresu
    hub widzi Booted → wpis potwierdzony

    brak PRZYDZIAŁU → wróć do fazy 2
```

Węzeł przełożony na inną magistralę **zachowuje adres** — pula jest wspólna, więc nie ma
powodu go zmieniać.

### 5.4 Dlaczego identyfikator musi zawierać `ShortId`

Arbitraż na magistrali jest bezkolizyjny **tylko wtedy, gdy identyfikatory ramek się
różnią**. Gdyby wszystkie nieprzydzielone węzły nadawały zgłoszenie z jednym, wspólnym
identyfikatorem, różniąc się wyłącznie treścią, zderzałyby się destrukcyjnie i blokowały
magistralę nawzajem.

Wyprowadzenie identyfikatora z `ShortId` sprawia, że każdy węzeł nadaje inny — arbitraż
ustawia je w kolejkę sprzętowo, bez udziału oprogramowania.

Mechanizm i rachunek prawdopodobieństwa kolizji opisuje
[`05-mapowanie-can.md`](05-mapowanie-can.md) §4.2.

### 5.5 Czterdzieści urządzeń naraz

Zgłoszenie i przydział to dwie ramki, razem około milisekundy czasu magistrali plus
obsługa w hubie. Czterdzieści węzłów to więc **poniżej stu milisekund transmisji**.

Arbitraż ustawia je w kolejkę sam, bez żadnego mechanizmu wyższego poziomu. Całość kończy
się w kilka sekund, a czas ten jest zdominowany przez rozrzut losowej zwłoki, nie przez
przesyłanie.

### 5.6 Zwłoka i powtórzenia

Węzeł nie zgłasza się natychmiast po starcie, tylko po zwłoce losowanej z przedziału
rosnącego z każdą nieudaną próbą:

| Próba | Przedział zwłoki |
|---|---|
| 1–5 | 0 … 2 s |
| 6–10 | 0 … 10 s |
| dalej | 0 … 60 s, **bez końca** |

Rosnący przedział chroni magistralę w przypadku, gdy huba w ogóle nie ma. Przy górnym
progu czterdzieści węzłów generuje mniej niż jedną ramkę na sekundę z całej instalacji —
ruch pomijalny.

Węzeł, który nie może dostać adresu, ma **próbować bez końca**. Hub może być wyłączony
przez tydzień i po włączeniu instalacja ma wstać sama, bez obchodzenia domu z drabiną.

Węzeł bez adresu powinien to sygnalizować w sposób widoczny dla człowieka. Jest to
najczęstsza usterka montażowa i najłatwiejsza do zdiagnozowania na miejscu.

---

## 6. Konflikt adresów

Dwa węzły o tym samym adresie to stan, w którym instalacja przestaje być diagnozowalna:
odpowiedzi mieszają się, a raporty stanu przeczą sobie nawzajem. Przy adresacji globalnej
**konfliktem jest to także wtedy, gdy węzły siedzą na różnych magistralach** — nie
przeszkadzają sobie na ramkach, ale hub nie ma jak ich rozróżnić.

Konflikt nie powinien powstać, bo adresy nadaje wyłącznie hub. Powstaje jednak przy
nieostrożnym odtworzeniu kopii bazy albo ręcznym ustawieniu adresu.

**Wykrycie na magistrali.** Węzeł, który po starcie zobaczy ruch nadany spod własnego
adresu, a którego sam nie wysłał, uznaje to za konflikt. Wtedy:

1. przestaje nadawać,
2. zeruje `Address` do `0x000`,
3. wraca do procedury przyłączania.

Ustępuje więc ten, kto wykrył konflikt później. Jest to arbitralne, ale rozstrzygające —
a rozstrzygnięcie jakiekolwiek jest lepsze niż dwa węzły uparcie nadające spod jednego
adresu.

**Wykrycie przez hub.** Ruch spod adresu, który hub przypisał węzłowi na **innej
magistrali**, oznacza konflikt — a **tylko hub jest w stanie wykryć ten przypadek**, bo
węzły na osobnych magistralach nigdy się nie usłyszą i wykrycie na magistrali ich nie
uratuje.

Rozpoznaje się to po **interfejsie, którym ramka przyszła**, i nic więcej nie jest do tego
potrzebne: adres jest niepowtarzalny w całej instalacji (§2.1), więc ten sam adres na dwóch
interfejsach **sam w sobie** jest konfliktem. Numer magistrali hub ma przy każdej odebranej
ramce, bo to on trzyma gniazda.

> **Nota implementacyjna.** Nie należy opierać tego na zawartości `Booted` — to zdarzenie
> niesie wyłącznie `resetReason` i `firmwareVersion`
> ([`types/0x0001-device.md`](types/0x0001-device.md) §4) i nie zawiera `ShortId`. Hub,
> który szukałby w nim tożsamości nadawcy, nie znajdzie jej i regułę zostawi martwą.

Hub powinien zgłosić to jako usterkę wymagającą uwagi człowieka; sam z siebie nie potrafi
rozstrzygnąć, który z węzłów jest tym właściwym.

---

## 7. Trwałość

`Address` jest zapisany w pamięci trwałej węzła. Po zaniku zasilania węzeł wraca na
magistralę pod tym samym numerem, bez udziału huba.

Ma to znaczenie wykraczające poza wygodę: **instalacja musi wstawać po awarii zasilania
w kolejności dowolnej.** Gdyby adresy zależały od huba, każde włączenie prądu wymagałoby,
by hub wstał pierwszy i zdążył obsłużyć wszystkich, zanim cokolwiek zacznie działać.

Węzeł nie zapisuje natomiast **numeru magistrali** — nie zna go i nie ma po co. Wie tylko,
jaki ma adres; to, na którym końcu kabla siedzi, jest wiedzą huba.
