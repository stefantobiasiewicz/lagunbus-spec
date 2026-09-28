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
| **OCZEKUJĄCY** | zgłosił się, ale tryb przyjmowania jest wyłączony (§2.1) |
| **PRZYŁĄCZONY** | ma adres; model jeszcze nieodczytany |
| **GOTOWY** | model odczytany, urządzenie użyteczne |
| **NIEOBECNY** | znany i przyłączony, ale milczy (§5) |
| **WYCOFANY** | usunięty przez operatora; adres zwolniony (§7) |

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

Usunięcie jest **operacją po stronie huba** — węzeł nie zna takiego pojęcia.

```
1.  hub wysyła FactoryReset, o ile węzeł odpowiada
        (Device, komenda 0x02, argument 0x4C41474E)

2.  hub zwalnia adres do puli

3.  hub oznacza ShortId jako WYCOFANY
```

Krok 1 nie zawsze się powiedzie — moduł bywa usuwany właśnie dlatego, że jest uszkodzony
albo już zdemontowany. Wtedy hub pomija go i przechodzi dalej.

Skutek jest taki, że **fizycznie podłączony węzeł może nadal pracować pod swoim adresem**,
choć hub już go nie zna. Nie przeszkadza to nikomu do chwili, w której ten adres zostanie
komuś przydzielony — i wtedy zadziała wykrywanie konfliktu. Dlatego stan `WYCOFANY`
zostaje w bazie: hub wie, że ten `ShortId` może się jeszcze odezwać, i traktuje go jak
nieznany, czyli wymagający trybu przyjmowania.

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
