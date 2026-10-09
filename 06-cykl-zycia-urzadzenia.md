# 06 · Cykl życia urządzenia

> **Stabilne.** Procedury ustalone i wykonalne w całości.

Od wyjęcia z pudełka do usunięcia z instalacji. Rozdział opisuje, co dzieje się między
hubem a węzłem; **powiązania sterujące** — czyli reguły łączące klawisz z przekaźnikiem —
są osobnym tematem i osobnym dokumentem.

Uszkodzony moduł wymienia się przez **usunięcie starego i dodanie nowego**. Zachowanie
ciągłości konfiguracji przy wymianie nie jest w tej wersji przewidziane
([`DECYZJE.md`](DECYZJE.md) — „Wymiana urządzenia poza zakresem v1").

---

## 1. Stany

### 1.1 Po stronie węzła

Węzeł zna tylko dwa stany i nie wie nic o tym, co hub o nim myśli:

| Stan | Warunek | Co robi |
|---|---|---|
| **BEZ ADRESU** | `Device.Address = 0x000` | rozgłasza `ZGŁOSZENIE` z narastającą zwłoką, sygnalizuje to widocznie |
| **PRACUJĄCY** | adres nadany | emituje `Booted`, potem raporty i zdarzenia, odpowiada na żądania |

Prostota jest zamierzona. Węzeł nie śledzi, czy hub żyje, nie zna pojęcia „usunięty
z instalacji" i nie ma stanu pośredniego, w którym częściowo działa.

### 1.2 Po stronie huba

Hub prowadzi stan **dla każdego `ShortId`**, jaki kiedykolwiek zobaczył:

| Stan | Znaczenie |
|---|---|
| **NIEZNANY** | nigdy niewidziany |
| **OCZEKUJĄCY** | zgłosił się, ale tryb przyjmowania jest wyłączony (§2.1), albo pracuje pod adresem, którego hub nie zna (§2.3) |
| **PRZYŁĄCZONY** | ma adres; model jeszcze nieodczytany |
| **GOTOWY** | model odczytany, urządzenie użyteczne |
| **NIEOBECNY** | znany i przyłączony, ale milczy (§5) |
| **ZABLOKOWANY** | operator kazał go nie obsługiwać; hub go zna i trzyma jego adres (§8) |

---

## 2. Dodanie nowego urządzenia

### 2.1 Tryb przyjmowania

Hub ma przełącznik **przyjmowania nowych urządzeń**. Reguła jest asymetryczna i to jest
w niej najważniejsze:

| Kto się zgłasza | Tryb wyłączony | Tryb włączony |
|---|---|---|
| `ShortId` **znany** hubowi | **przydziel** adres, który miał | przydziel |
| `ShortId` **nieznany** | zapisz jako `OCZEKUJĄCY`, nie przydzielaj | przydziel |

Znane urządzenie dostaje swój adres **zawsze i bez pytania**. Dzięki temu wymiana
bezpiecznika, przywrócenie ustawień fabrycznych czy odłączenie modułu na czas remontu
nie wymagają żadnej ceremonii — instalacja wstaje sama.
Jedynym wyjątkiem jest urządzenie, które operator zablokował (§8).

Tryb chroni wyłącznie przed tym, żeby **nieznane** urządzenie samo weszło do instalacji.
Nie jest to zabezpieczenie przed napastnikiem — magistrala biegnie w ścianie i kto ma do
niej dostęp, ma większe możliwości. Jest to zabezpieczenie przed bałaganem: modułem
testowym wpiętym na chwilę, pomyłką montażową, urządzeniem podłączonym pod zły odcinek.

Tryb **wygasa samoczynnie** po piętnastu minutach. Otwarty na stałe nie chroni przed niczym.

Węzeł `OCZEKUJĄCY` nie wymaga ponownego uruchomienia: zgłasza się bez końca, więc po
włączeniu trybu zostanie przyjęty w ciągu najwyżej minuty.

### 2.2 Przebieg

```
1.  montaż, podłączenie do magistrali, załączenie zasilania

2.  ZGŁOSZENIE  →  PRZYDZIAŁ                      03-adresacja §5
    zgłoszenie niesie NodeClass — blok adresowy

3.  węzeł zapisuje adres trwale, emituje Booted
    Booted niesie resetReason i firmwareVersion

4.  hub odczytuje tożsamość z ep0:
        Uid, DeviceType, ProtocolVersion,
        HardwareVersion, EndpointCount

5.  hub enumeruje endpointy                       §3

6.  hub zapisuje model w bazie pod Uid            stan GOTOWY

7.  operator nadaje nazwę, przypisuje do pomieszczenia

8.  operator tworzy reguły sterowania
```

Kroki 1–6 dzieją się same. Dopiero 7 i 8 wymagają człowieka.

### 2.3 Węzeł z adresem, którego hub nie zna

Węzeł z adresem w pamięci trwałej nie bierze udziału w przyłączaniu
([`03-adresacja.md`](03-adresacja.md) §5.1). Jeśli hub tego adresu nie zna — bo baza została
utracona albo odtworzona ze starej kopii, bo węzeł był wycofany, a `FactoryReset` do niego
nie dotarł, albo bo wpięto moduł używany gdzie indziej — przyłączanie go nie przyprowadzi.

Hub rozpoznaje taki węzeł sam:

```
1.  ramka węzła spod adresu, którego nie ma w bazie huba
        dowolna: raport, zdarzenie, Booted — nie tylko Booted,
        bo hub zwykle wstaje po węzłach i ich Booted przepada

2.  ODCZYT Device.Uid i Device.ShortId spod tego adresu      raz na adres

3.  Uid albo ShortId znany hubowi pod innym adresem
                       → sprzeczność bazy z magistralą, usterka dla człowieka
    Uid w konfiguracji huba, niezablokowany
                       → enumeracja pod obecnym adresem, GOTOWY      bez operatora
    Uid w konfiguracji huba, zablokowany
                       → ZABLOKOWANY (§8)
    oba nieznane       → węzeł OCZEKUJĄCY, pod tym adresem

4.  operator, dla OCZEKUJĄCEGO:
        przyjmij                          → enumeracja pod obecnym adresem, GOTOWY
        przywróć ustawienia fabryczne     → FactoryReset, węzeł wraca do przyłączania
```

Obowiązkowe raporty `Diagnostics` (§5) sprawiają, że hub zobaczy każdy taki węzeł w ciągu
jednego okresu raportowania — bez odpytywania wszystkich po starcie
([`07-hub.md`](07-hub.md) §5.1). Kosztem są dwa odczyty na nieznany adres.

`ShortId` hub **odczytuje**, a nie wylicza z `Uid`: wyliczenie zakłada, że węzeł liczy go tak
samo, a to jest właśnie ten rodzaj zgodności, której nikt nie sprawdza, dopóki się nie
rozjedzie.

**Nieznany węzeł nie wchodzi sam, także przy włączonym trybie przyjmowania.** Tryb dotyczy
węzłów, które się zgłaszają, czyli węzłów bez adresu. Węzeł z cudzym adresem przyniósł
konfigurację, o której hub nic nie wie, i decyzja o nim należy do człowieka.

**Węzeł, którego `Uid` hub ma w swojej konfiguracji, nie jest nieznany.** Wpis w
konfiguracji — nazwa, pomieszczenie, powiązania, choćby samo `Uid` — to decyzja operatora
podjęta wcześniej; pytanie go drugi raz niczego nie chroni. Taki węzeł przechodzi
enumerację pod adresem, spod którego nadaje, i staje się `GOTOWY`. Zdarza się to, gdy
konfiguracja huba wie mniej niż magistrala: odtworzona ze starej kopii, sprzed
przyłączenia węzła albo uruchomiona od nowa z tymi samymi wpisami. Węzeł zablokowany
zostaje `ZABLOKOWANY` (§8).

Działa to tylko dla węzła **z adresem**. Węzeł bez adresu zgłasza się samym `ShortId`,
a `ShortId` hub czyta, nie wylicza (wyżej) — więc z konfiguracji go nie rozpozna, dopóki
nie zna jego `ShortId`. Taki węzeł wraca przez tryb przyjmowania. Przyjęcie
pod adresem, który w bazie huba należy do innego urządzenia, nie jest możliwe — wtedy
zostaje reset fabryczny.

**Urządzenie używane przywraca się do ustawień fabrycznych przed podłączeniem.** Jest to
zasada montażowa, a jej mechanizmem jest przycisk serwisowy, który ma każde urządzenie
([`types/0x0001-device.md`](types/0x0001-device.md) §5.4). Wychwycenie przez hub działa tylko wtedy, gdy adres
przyniesiony przez moduł jest na tym kablu wolny; gdy jest zajęty, dwa węzły nadają spod
jednego adresu i nie da się ich rozróżnić ([`03-adresacja.md`](03-adresacja.md) §6).

---

## 3. Rozpoznanie i enumeracja

### 3.1 Co hub odczytuje

```
ep0    Device.Uid, DeviceType, ProtocolVersion,
       HardwareVersion, EndpointCount

ep4 … ep(3 + EndpointCount):
       0xF0  TypeId          jaki typ ma ten endpoint
       0xF1  TypeRevision    rewizja kontraktu
       0xF2  Features        w jakim wariancie
       0xF5  Channel         do której rzeczy fizycznej należy
```

Cztery transakcje na endpoint. Urządzenie z ośmioma endpointami to 34 odczyty, około
35 ms. Jednorazowo — bez znaczenia.

`Channel` jest odczytywany zawsze, także z urządzeń jednokanałowych. Hub nie wie z góry,
czy relacja wystąpi, a odczyt warunkowy oszczędziłby jedną transakcję kosztem gałęzi
w procedurze, która wykonuje się raz w życiu urządzenia.

### 3.2 Endpointy funkcjonalne są ciągłe

> **Endpointy funkcjonalne numeruje się od `4` bez przerw.**
> `EndpointCount` mówi, ile ich jest.

Bez tej zasady hub musiałby odpytywać wszystkie sześćdziesiąt możliwych numerów
i rozpoznawać nieobecne po kodzie `UNSUPPORTED_ENDPOINT` — sześćdziesiąt transakcji
zamiast kilkunastu, przy każdym nowym urządzeniu.

> **Endpointy funkcjonalne numeruje się w porządku fizycznym urządzenia** — od góry do
> dołu, od lewej do prawej, od pierwszego zacisku.

Kosztuje to zero bajtów i zero odczytów, a rozstrzyga pytanie, którego `Channel` ani
`Purpose` nie rozstrzygają: **który z trzech identycznych klawiszy jest górny**. Instalator
patrzący na listę endpointów widzi ją w tej samej kolejności, w której patrzy na
urządzenie. Bez tej reguły kolejność byłaby przypadkowa i każdy panel wymagałby
sprawdzenia metodą prób.

Wariant sprzętowy bez jakiegoś podzespołu — panel, w którym nie zamontowano czujnika
temperatury — **nie zostawia dziury**. Endpoint istnieje i jest widoczny, tylko ma
atrybut wspólny `0xF3 Enabled` ustawiony na `0`. Hub widzi wtedy dokładnie, czego
urządzenie nie ma, zamiast zgadywać z braku odpowiedzi.

### 3.3 Kiedy enumerować ponownie

Hub buforuje model pod `Uid`. Ponowna enumeracja następuje, gdy **zmieniła się wersja
firmware** — bo tylko aktualizacja może dołożyć endpoint albo podnieść rewizję typu.

Nie kosztuje to ani jednej dodatkowej ramki: **`Booted` niesie `firmwareVersion`**, więc
hub porównuje ją z zapamiętaną przy każdym starcie węzła i decyduje bez odpytywania.

Operator może wymusić enumerację ręcznie — przydaje się, gdy baza huba została odtworzona
z niepełnej kopii.

---

## 4. Zmiana adresu przez hub

### 4.1 Dwie drogi, dwa zastosowania

| | Kiedy | Mechanizm |
|---|---|---|
| `PRZYDZIAŁ` | węzeł **nie ma** adresu | ramka przyłączania, adresowana po `ShortId` |
| zapis `Device.Address` | węzeł **ma** adres | zwykły `ZAPIS` |

Druga droga służy porządkowaniu — przesunięciu węzła do właściwego bloku adresowego, gdy
adres nadany przy przyłączaniu okazał się nie z tego zakresu, co trzeba
([`03-adresacja.md`](03-adresacja.md) §2.3).

Odkąd zgłoszenie niesie `NodeClass`, dzieje się to w dwóch sytuacjach i obie są rzadkie:
węzeł zadeklarował klasę `UNSPECIFIED`, albo zadeklarował ją niezgodnie z tym, co pokazał
deskryptor. Droga zostaje mimo to obowiązkowa — klasa jest wskazówką, a hub musi umieć
poprawić wskazówkę, która okazała się nietrafiona.

### 4.2 Przebieg

```
1.  hub sprawdza we własnej bazie, że nowy adres jest wolny

2.  ZAPIS  Device.Address = nowy

3.  węzeł zapisuje adres trwale,
    odpowiada jeszcze SPOD STAREGO adresu,
    wszystko po odpowiedzi nadaje spod nowego

4.  hub potwierdza: ODCZYT Device.Uid spod NOWEGO adresu
```

Krok 4 nie jest formalnością. Zapis atrybutu trwałego trafia do pamięci **przed**
odpowiedzią ([`04-interakcje.md`](04-interakcje.md) §4.1), więc węzeł nigdy nie zostaje
w stanie nieokreślonym — ale **odpowiedź może zaginąć**, a wtedy hub nie wie, po której
stronie zmiany jest węzeł.

### 4.3 Odzyskiwanie po zgubionej odpowiedzi

```
odczytaj Device.Uid spod NOWEGO adresu
    ├── zgodny Uid    → zmiana zaszła, zaktualizuj bazę
    └── cisza
            odczytaj Device.Uid spod STAREGO adresu
                ├── zgodny Uid  → zmiana nie zaszła, powtórz zapis
                └── cisza       → węzeł nieobecny, stan nieznany;
                                  nie zwalniaj żadnego z adresów
```

Ostatni przypadek wymaga uwagi: dopóki nie wiadomo, pod którym adresem siedzi węzeł,
**żadnego z dwóch nie wolno przydzielić komu innemu**. Inaczej po powrocie zasilania
powstanie konflikt adresów ([`03-adresacja.md`](03-adresacja.md) §6).

---

## 5. Nieobecność

Hub uznaje węzeł za nieobecnego, gdy ten przestaje się odzywać. Warto zacząć od
stwierdzenia, które upraszcza całą resztę:

> **Węzłów milczących nie ma.**

[`Diagnostics`](types/0x0002-diagnostics.md) siedzi na `ep1` w każdym węźle bez wyjątku
i ma **trzy atrybuty raportowane obowiązkowo** — `TxErrorCount`, `RxErrorCount` i
`BusState` — z domyślnym `ReportInterval` 300 s
([`types/0x0002-diagnostics.md`](types/0x0002-diagnostics.md) §5.4).

Panel klawiszowy, którego nikt nie dotknął od tygodnia, odzywa się więc mimo to co pięć
minut — i to bez żadnego mechanizmu dołożonego specjalnie po to. **Nasłuchiwanie wystarcza
w przypadku normalnym, a odpytywanie jest wyjątkiem, nie regułą.**

### 5.1 Po jakim czasie hub sięga po odpytanie

Próg nie jest stałą globalną — wynika z konfiguracji samego węzła:

> **Hub odpytuje węzeł, od którego nic nie przyszło przez dwa razy tyle, ile wynosi
> najkrótszy niezerowy `ReportInterval` wśród jego endpointów.**

Dwa pominięte raporty, nie jeden: pojedynczy ginie przy zajętej magistrali i nie znaczy
nic. Dwa z rzędu znaczą już coś.

Przy ustawieniach domyślnych daje to dziesięć minut ciszy. Instalacja, która chce wiedzieć
szybciej, **obniża `ReportInterval`** — i to jest cała regulacja, jakiej ten mechanizm
potrzebuje. Osobnego pokrętła „częstotliwość nadzoru" nie ma i nie będzie, bo byłoby drugim
sposobem ustawiania tej samej rzeczy.

Dwa przypadki wymagają dopowiedzenia:

- **Węzeł z wyłączonym raportowaniem cyklicznym** we wszystkich endpointach
  (`ReportInterval = 0`) jest jedynym bez wyliczalnego progu. Obowiązuje dla niego
  **300 s**, czyli tyle, ile wynosi wartość domyślna.
- **Endpointów wyłączonych atrybutem `Enabled`** hub do wyliczenia nie bierze. Sam je
  uciszył, więc ich milczenie niczego nie dowodzi.

### 5.2 Odpytanie i stan `NIEOBECNY`

Hub odczytuje z węzła `Device.Uptime`. Jedna transakcja, żadnego nowego mechanizmu
w protokole.

**Trzy nieudane próby z rzędu, w odstępach 10 s, oznaczają stan `NIEOBECNY`.** Odstęp jest
tam po to, żeby węzeł, który akurat się restartuje, zdążył wrócić — restart trwa ułamek
sekundy, ale odtworzenie konfiguracji i przyłączenie do magistrali już nie
([`types/0x0001-device.md`](types/0x0001-device.md) §5.1). Powrót jakiejkolwiek wiadomości
od tego węzła natychmiast wyprowadza go ze stanu `NIEOBECNY`.

`Device.Uptime` jest tu wygodny podwójnie: mówi nie tylko, że węzeł żyje, lecz także
**czy przetrwał od ostatniego sprawdzenia**. Uptime niższy niż poprzednio oznacza restart,
którego hub nie zauważył — bo zgubił `Booted`.

### 5.3 Ile to kosztuje

Odpytywanie nie kosztuje nic, bo w instalacji zdrowej nie zachodzi.

Kosztuje natomiast to, co je zastąpiło — i ten rachunek warto mieć zapisany: sto węzłów,
po trzy raporty `Diagnostics` co 300 s, to **jedna ramka na sekundę**, czyli poniżej
jednej dziesiątej procenta przepustowości ([`05-mapowanie-can.md`](05-mapowanie-can.md) §7).

Jest to zarazem odpowiedź na pytanie, czy `Device` potrzebuje własnego atrybutu
raportowanego cyklicznie — **nie potrzebuje**. Trzy takie atrybuty już są, są obowiązkowe
i są w każdym węźle. Czwarty byłby drugim tętnem obok pierwszego.

---

## 6. Usunięcie z instalacji

Usunięcie jest **operacją po stronie huba** — węzeł nie zna takiego pojęcia. Hub
**zapomina** urządzenie: nie zostaje po nim żaden stan, także pod jego `ShortId`. Wraca
tylko przez tryb przyjmowania, jak każde nieznane.

Operator wybiera jeden z dwóch trybów.

### 6.1 Usunięcie zwykłe

```
1.  hub wysyła FactoryReset i czeka na odpowiedź
        (Device, komenda 0x02, argument 0x4C41474E)

2.  węzeł potwierdził:  hub zwalnia adres do puli i zapomina ShortId
    węzeł milczy albo odmawia:  nic się nie zmienia, operator dostaje błąd
```

Potwierdzenie jest warunkiem, bo tylko ono mówi, że węzeł naprawdę stracił adres. Po
nim adres jest wolny także na magistrali — hub może go przydzielić od razu, choćby temu
samemu urządzeniu przyjętemu ponownie.

### 6.2 Usunięcie wymuszone

```
1.  hub wysyła FactoryReset i nie czeka na odpowiedź

2.  hub zapomina ShortId
```

Do usuwania modułu, który już nie odpowie — uszkodzonego albo zdemontowanego, a wciąż
widniejącego w hubie.

Skutek jest taki, że **fizycznie podłączony węzeł może nadal pracować pod swoim adresem**,
choć hub już go nie zna — gdy reset do niego nie dotarł. Adresu nie dostanie wtedy nikt
inny, bo hub nie przydziela adresu, który słyszy ([`03-adresacja.md`](03-adresacja.md) §6),
a sam węzeł wróci do operatora jako `OCZEKUJĄCY` (§2.3). Jeżeli potwierdzenie resetu
przyjdzie mimo wszystko, hub traktuje adres jak po usunięciu zwykłym.

---

## 7. Przywrócenie ustawień fabrycznych

`FactoryReset` zeruje wszystkie atrybuty konfiguracyjne wszystkich typów, **łącznie
z adresem**. Nie zmienia `Uid`, `DeviceType` ani wersji
([`types/0x0001-device.md`](types/0x0001-device.md) §3.3).

Po resecie węzeł wraca do stanu **BEZ ADRESU** i zaczyna się zgłaszać. Ponieważ jego
`ShortId` jest hubowi znany, **dostaje swój adres z powrotem automatycznie** — tryb
przyjmowania nie jest potrzebny.

Jest to celowe. Reset fabryczny służy naprawie węzła, który zgłupiał, a nie usuwaniu go
z instalacji; do usuwania służy §6. Po odzyskaniu adresu hub odtwarza konfigurację
z kopii i urządzenie wraca do pracy bez udziału człowieka.

---

## 8. Zablokowanie

Operator może kazać hubowi **nie obsługiwać** urządzenia, które fizycznie jest
w instalacji — modułu testowego, uszkodzonego, który zaśmieca magistralę zdarzeniami,
urządzenia czekającego na naprawę. Zablokowanie, tak jak usunięcie, jest operacją po
stronie huba: węzeł o nim nie wie i niczego od huba nie dostaje.

Hub rozpoznaje zablokowane urządzenie po `Uid` i trzyma blokadę w swojej konfiguracji,
więc przeżywa ona restart huba. Wobec węzła `ZABLOKOWANY`:

| | |
|---|---|
| przyłączanie | hub **nie przydziela** mu adresu, także przy włączonym trybie przyjmowania |
| enumeracja, uzgadnianie | nie zachodzą |
| zdarzenia i raporty | nie wyzwalają powiązań; żadne powiązanie nie ma go za cel |
| adres | pozostaje zajęty — węzeł na nim pracuje |
| ruch od huba | żadnego, poza odczytem tożsamości potrzebnym, by go rozpoznać (§2.3) |

Węzeł, który zgłasza się bez adresu, podaje tylko `ShortId`; hub rozpozna w nim urządzenie
zablokowane dopiero po odczycie `Uid`, czyli gdy węzeł już ma adres.

Odblokowany węzeł z adresem przechodzi enumerację i staje się `GOTOWY`; bez adresu
przyłącza się zwykłą drogą (§2).
