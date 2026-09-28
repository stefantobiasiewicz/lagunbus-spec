# Pojęcia i konwencje

> **Stabilne.** Dokument pomocniczy — nie wprowadza rozstrzygnięć, tylko zbiera w jednym
> miejscu to, czym posługują się wszystkie rozdziały.

Ten plik odpowiada na pytania, których nie wypada zadawać w środku rozdziału: co dokładnie
znaczy „element", czym różni się `V` od `P` w tabeli atrybutów i czy „powinien" znaczy to
samo co „musi".

---

## 1. Słownik

### 1.1 Instalacja i sprzęt

| Pojęcie | Znaczenie |
|---|---|
| **Instalacja** | całość: wszystkie magistrale i wszystkie węzły jednego domu, zarządzane przez jeden hub |
| **Magistrala** | jeden odcinek CAN: zasilanie plus para różnicowa, z własnym zakończeniem. Instalacja ma ich kilka |
| **Węzeł** | jedno urządzenie fizyczne na magistrali, o jednym adresie |
| **Hub** | urządzenie zarządzające całą instalacją; jedyne, które widzi wszystkie magistrale naraz |
| **System nadrzędny** | to, czemu hub wystawia instalację na zewnątrz — Home Assistant lub podobny. Poza zakresem specyfikacji |
| **Adapter północny** | warstwa huba tłumacząca instalację na protokół systemu nadrzędnego. Nieustalony |
| **Operator** | człowiek konfigurujący instalację: nadaje nazwy, tworzy reguły, dodaje i usuwa urządzenia |

### 1.2 Model danych

| Pojęcie | Znaczenie |
|---|---|
| **Endpoint** | jedna funkcja węzła, numer `0`–`63`. Najmniejsza rzecz mająca osobną nazwę i osobny stan |
| **Endpoint systemowy** | numery `0`–`3`; ich typ wynika ze specyfikacji, nie z urządzenia |
| **Endpoint funkcjonalny** | numery od `4` w górę, bez przerw; to, co urządzenie faktycznie robi |
| **Typ endpointu** | nazwany kontrakt: zbiór atrybutów, komend i zdarzeń. W Zigbee i Matter nazywa się to klastrem |
| **Cecha** | opcjonalne rozszerzenie typu, zadeklarowane raz i niezmienne; włącza dodatkowe atrybuty i komendy |
| **Atrybut** | nazwana wartość — **stan**. Ma wartość bieżącą, da się odczytać |
| **Komenda** | żądanie akcji skierowane do endpointu |
| **Zdarzenie** | powiadomienie o **fakcie**. Nie ma wartości bieżącej, nie da się odczytać |
| **Element** | wspólna nazwa na atrybut, komendę albo zdarzenie — to, co wskazuje ostatnie osiem bitów identyfikatora ramki |
| **Deskryptor** | płaska lista `endpoint → typ + cechy + kanał`, odtwarzana odczytem atrybutów `0xF0`–`0xF2` i `0xF5` |
| **Kanał** | która rzecz fizyczna urządzenia; endpointy o tym samym `Channel` opisują to samo. Lokalny dla węzła |
| **`Purpose`** | czym endpoint jest dla mieszkańca. Nie zmienia zachowania typu, niesie samą intencję |
| **Model** | para `VendorId` + `DeviceType`: czym urządzenie jest. Odrębne od tego, co potrafi |
| **Wartość „brak"** | zarezerwowana wartość każdego typu liczbowego, znacząca „nie wiem". Nigdy nie zero |

### 1.3 Adresowanie i ruch

| Pojęcie | Znaczenie |
|---|---|
| **`Uid`** | tożsamość węzła: pochodzi ze sprzętu, nie zmienia się nigdy, jest za długi na jedną ramkę |
| **`ShortId`** | 32-bitowy skrót `Uid` (CRC-32); mieści się wszędzie, służy do odróżniania węzłów |
| **Adres** | 11 bitów, **droga** do węzła w tej chwili. Nie jest tożsamością |
| **`NodeClass`** | pilność ruchu węzła: `CONTROL`, `SENSOR` albo `UNSPECIFIED`. Wybiera blok adresowy przy przyłączaniu i **nie jest atrybutem** |
| **Grupa** | numer `0x001`–`0x7FF`; adres zbiorczy i zarazem zakres sceny. Przynależność prowadzi tablica na `ep2` |
| **Scena** | zapamiętany stan wyjść, kluczowany parą `(grupa, numer)`. Istnieje dla jednoczesności |
| **Rozgłoszenie** | adres `0x7FF`; wyłącznie jako odbiorca w ramkach od huba |
| **Transakcja** | żądanie i odpowiedź tworzące parę, skojarzone przez `Tid` |
| **`Tid`** | trzybitowy identyfikator transakcji, niepowtarzalny wśród żądań nierozstrzygniętych do jednego węzła |
| **Raport** | niezamawiana wiadomość węzła o wartości atrybutu |
| **Rodzaj wiadomości** | cztery najstarsze bity identyfikatora ramki; **jest zarazem priorytetem** |
| **Segment** | kawałek wartości, która nie mieści się w jednej ramce. Nie jest osobną interakcją — odczyt pozostaje odczytem |
| **Zapytanie** | jedyna transakcja, którą zaczyna węzeł: „podaj wartość tego mojego atrybutu". Opcjonalna |
| **Wejście** | atrybut zapisywalny i ulotny, którego węzeł sam nie zmierzy — wypełnia go hub. Typ wymienia swoje wejścia z numerami bitów `QueryEnabled` |

---

## 2. Notacja tabel

### 2.1 Konformancja

| Zapis | Znaczenie |
|---|---|
| `M` | obowiązkowy — implementacja **musi** go mieć |
| `O` | opcjonalny — **może** go mieć |
| `[CECHA]` | obowiązkowy wtedy i tylko wtedy, gdy zadeklarowano tę cechę |
| `!` | zabroniony w tym kontekście |

Urządzenie deklarujące typ musi zaimplementować **wszystkie** jego elementy oznaczone `M`.
Brak choćby jednego oznacza, że nie wolno deklarować tego typu.

### 2.2 Dostęp

| Zapis | Znaczenie |
|---|---|
| `RO` | tylko odczyt; zapis kończy się `READ_ONLY` |
| `RW` | odczyt i zapis |
| `WO` | tylko zapis; odczyt kończy się `WRITE_ONLY` |

### 2.3 Trwałość

| Zapis | Znaczenie |
|---|---|
| `V` | ulotny — RAM, przepada przy restarcie |
| `P` | trwały — pamięć nieulotna, przeżywa restart; zapis kończy się **przed** odpowiedzią |
| `—` | pojęcie nie ma zastosowania, np. licznik czasu pracy |

### 2.4 Pozostałe kolumny

**Rap.** — czy atrybut podlega automatycznemu raportowaniu
([`01-model-danych.md`](01-model-danych.md) §6). **Zakres** — dopuszczalne wartości; zapis
poza nim kończy się `INVALID_VALUE`. **Domyśl.** — wartość po `FactoryReset`.

### 2.5 Zapis liczb i typów

- Liczby szesnastkowe z przedrostkiem `0x`, z zachowaniem szerokości pola: adres węzła
  zawsze trzycyfrowo (`0x02A`), identyfikator typu czterocyfrowo (`0x0020`).
- Typy danych zapisujemy skrótem: `u8`, `i16`, `u32`, `bool`, `enum8`, `map16`, `string`,
  `blob`; tablica to `typ[n]` ([`02-typy-danych.md`](02-typy-danych.md) §2).
- `⟨Q⟩` oznacza typ wynikający z wielkości mierzonej, a nie z definicji atrybutu.
- Poziomy i pozycje w **promilach** (`‰`), zakres `0`–`1000`.
- Czas w nawiasie kwadratowym przy argumencie: `duration: u16` [ms].

---

## 3. Siła zobowiązań

Specyfikacja jest pisana prozą, nie listą punktów `SHALL`. Trzy sformułowania mają jednak
znaczenie ustalone i nie są wymienne:

| Sformułowanie | Znaczy |
|---|---|
| **musi**, **ma**, **nie wolno**, forma dokonana („węzeł zapisuje") | **wymaganie**. Implementacja, która tego nie robi, jest niezgodna |
| **powinien**, **warto**, **zaleca się** | **zalecenie**. Odstępstwo jest dopuszczalne, jeśli autor wie, co robi |
| **może**, **wolno**, **dopuszczalne** | **dozwolenie**. Obie decyzje są zgodne ze specyfikacją |

Zdania w cytacie blokowym są **zawsze wymaganiami**:

> Tak wygląda wymaganie, którego nie da się przeoczyć.

Zdania zaczynające się od „Powód", „Dlaczego" albo „Jest to decyzja" są **uzasadnieniem**
i nie zawierają wymagań. Można je pominąć przy implementowaniu i nie można przy zmienianiu.

---

## 4. Gdzie co wolno rozstrzygać

Trzy reguły redakcyjne obowiązujące w całej specyfikacji:

1. **Zdania normatywne o ramce są wyłącznie w [`05-mapowanie-can.md`](05-mapowanie-can.md).**
   W rozdziałach 01–04 i w `types/` CAN pojawia się tylko jako uzasadnienie
   ([`00-wprowadzenie.md`](00-wprowadzenie.md) § Warstwy).
2. **Identyfikatory rozstrzyga [`registry/`](registry/).** Tabela w markdown, która nie
   zgadza się z rejestrem, jest błędna.
3. **Rozdział opisuje wyłącznie to, co ustalone.** Bez przypisów „do rozstrzygnięcia"
   i bez list punktów otwartych. Sprzeczność albo brak znaleziony przy implementacji
   trafia od razu do autora specyfikacji, który decyduje, co z nim zrobić; odłożone
   prowadzi się jako zadanie projektu, poza specyfikacją.
3a. **Wymaganie testowalne trafia do [`COMPLIANCE.md`](COMPLIANCE.md)** z własnym numerem —
   ale tylko wtedy, gdy nie wynika wprost z kolumny `Konf.` w tabeli typu. Tabele są
   źródłem prawdy dla swoich typów i nie powiela się ich.
4. **Znaczenie danych wyprowadza się wyłącznie z deskryptora odczytanego z węzła.** Rejestr
   modeli mówi, czym urządzenie jest — nigdy, co potrafi
   ([`types/0x0001-device.md`](types/0x0001-device.md) §2.6). Katalog, bez którego hub nie
   umie poprawnie pokazać danych, jest bazą konwerterów.
5. **Porównania z Zigbee i Matter nie należą do rozdziałów normatywnych ani do `types/`.**
   Rozdział ma opisywać ten protokół, nie tłumaczyć go przez inny — czytelnik, który nie zna
   Matter, nie powinien być stratny. Wyjątkiem jest
   [`00-wprowadzenie.md`](00-wprowadzenie.md) i [`README.md`](README.md), gdzie mowa o tym,
   **skąd wzięliśmy model i dlaczego nie użyliśmy gotowego** — to jest pozycjonowanie
   projektu, a nie objaśnianie jego działania.
