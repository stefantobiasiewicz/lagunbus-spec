# Typ endpointu `0x0004` · Groups

> **Stabilne.** Model i komendy ustalone. Minimalna pojemność tablicy może jeszcze wzrosnąć.

**Rewizja 1** · przynależność endpointów do grup

Siedzi zawsze na **endpoincie 2** i prowadzi jedną rzecz: tablicę mówiącą, które endpointy
węzła należą do których grup.

Grupa jest adresem zbiorczym — jedna ramka dociera do wszystkich endpointów, które do niej
należą ([`../03-adresacja.md`](../03-adresacja.md) §3). Ten typ nie robi nic poza
zarządzaniem przynależnością; sam nie przyjmuje komend grupowych i nie ma stanu, który
dałoby się nimi zmienić.

---

## 1. Cechy

**Brak.** Węzeł różni się pojemnością tablicy, a to atrybut (`GroupCapacity`), nie cecha.

---

## 2. Atrybuty

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | `GroupCapacity` | `u8` | RO | P | nie | M | 0–255 | — |
| `0x01` | `GroupCount` | `u8` | RO | P | tak | M | 0–`GroupCapacity` | `0` |

`GroupCapacity` liczy **wpisy**, czyli pary `(endpoint, grupa)`. Ośmiokanałowy moduł,
w którym każdy kanał należy do trzech grup, potrzebuje dwudziestu czterech wpisów.

Wartość `0` jest dopuszczalna i znaczy, że węzeł **nie obsługuje grup w ogóle**. Jest to
poprawne dla urządzenia zbudowanego z samych klawiszy i czujników: grupa służy doręczaniu
komend, a taki węzeł żadnych nie przyjmuje.

Zalecane minimum dla węzła z wyjściami to **osiem wpisów**, a rozsądne — cztery na każde
wyjście.

---

## 3. Komendy

| ID | Nazwa | Argumenty | Odpowiedź | Konf. |
|---|---|---|---|---|
| `0x00` | `AddGroup` | `endpoint: u8`, `group: u16` | wynik | M |
| `0x01` | `RemoveGroup` | `endpoint: u8`, `group: u16` | wynik | M |
| `0x02` | `RemoveAllGroups` | `endpoint: u8` | wynik | M |
| `0x03` | `GetMembership` | `endpoint: u8` | `count: u8`, `groups: u16[…]` — w segmentach | M |

Docelowy endpoint jedzie **w ładunku**, bo pole `ENDPOINT` identyfikatora ramki wskazuje
ten endpoint — czyli `2` ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §1).

| Sytuacja | Wynik |
|---|---|
| `endpoint` nie istnieje albo nie przyjmuje komend | `UNSUPPORTED_ENDPOINT` |
| `group = 0` lub `group > 0x7FF` | `INVALID_VALUE` |
| tablica pełna | `INSUFFICIENT_SPACE` |
| `RemoveGroup` dla przynależności, której nie ma | `INVALID_STATE` |
| zapis do pamięci trwałej się nie powiódł | `FAILURE` |

`AddGroup` dla przynależności, która już istnieje, kończy się `OK` i nie zmienia niczego.
Powtórzenie komendy nie jest błędem ([`../04-interakcje.md`](../04-interakcje.md) §2.2).

### 3.1 `GetMembership` odpowiada w segmentach

Lista bywa dłuższa niż ramka — przy endpoincie należącym do wielu grup to setki bajtów.
Obowiązuje wtedy zwykła reguła: **wartość, która się mieści, przychodzi w odpowiedzi;
dłuższa — w segmentach** ([`../04-interakcje.md`](../04-interakcje.md) §9). Endpoint w dwóch
grupach odpowie jedną ramką, endpoint w stu — segmentami.

Układ jest w obu przypadkach ten sam:

```
ODPOWIEDŹ   [0] nagłówek z kodem SEGMENTED
segmenty    [0] count            całkowita liczba grup tego endpointu
            [1..] numery grup, po dwa bajty, little-endian
```

Endpoint może należeć do tylu grup, na ile starczy `GroupCapacity` — **żaden limit nie
wynika z rozmiaru ramki**. Hub zadaje jedno pytanie i dostaje całą listę.

Poprzednia rewizja tego typu stronicowała odpowiedź ręcznie, po trzy numery, z argumentem
`from`. Mechanizm działał, ale mylił: trzy numery na odpowiedź zbyt łatwo czytało się jako
trzy grupy na endpoint. Segmentowanie usuwa jedno i drugie.

---

## 4. Zdarzenia

**Brak.** Zmiana przynależności pochodzi od huba, więc hub o niej wie. `GroupCount` jest
raportowany i to wystarcza, by zauważyć zmianę wprowadzoną przez kogoś innego.

---

## 5. Zachowanie

### 5.1 Dlaczego tablica, a nie atrybut

Przynależność była pierwotnie atrybutem wspólnym `0xF4` typu `u8[4]` — czterema slotami
na endpoint. Nie dało się tego utrzymać przy poszerzeniu grup do 2047.

Zapis atrybutu jest **operacją na całości** i musi zmieścić się w jednej ramce. Zostaje na
to siedem bajtów, więc tablica `u16` ma miejsce na **trzy** wpisy — mniej, niż było.
Ograniczenie znika dopiero wtedy, gdy przestajemy przepisywać całość:

| Postać | Ile wpisów | |
|---|---|---|
| atrybut `u8[n]`, grupy do 255 | 7 | odrzucone — za mało grup |
| atrybut `u16[n]`, grupy do 2047 | 3 | odrzucone — **mniej wpisów, niż było** |
| tablica zarządzana komendami | **255** | ← **obowiązuje** |

Reguła, która to przesądza, stoi w specyfikacji od początku
([`../02-typy-danych.md`](../02-typy-danych.md) §5): tablice o zmiennej długości nie są
atrybutami. `Groups` jako `u8[4]` było wyjątkiem, który uchodził tylko dlatego, że był
malutki.

### 5.2 Tablica jest wspólna dla węzła

Wpis to para `(endpoint, grupa)`. Tablica jest jedna na węzeł, a `GroupCapacity` ogranicza
sumę wpisów — nie liczbę grup na endpoint. Dzięki temu moduł, w którym jedno wyjście
potrzebuje ośmiu grup, a pozostałe po jednej, nie marnuje pamięci na równy przydział.

Kolejność wpisów nie jest określona i węzeł może ją zmieniać — hub nie powinien na niej
niczego opierać. Nie ma to praktycznych skutków, bo `GetMembership` zwraca całą listę naraz
i hub i tak widzi ją w komplecie.

### 5.3 Filtrowanie sprzętowe ma granicę

Węzeł należący do kilku grup ustawia po jednym filtrze akceptacji na grupę i procesor budzi
się wyłącznie do ruchu, który go dotyczy
([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §3).

**Przy większej liczbie grup to przestaje działać.** Typowy kontroler ma kilkanaście banków
filtrów, nie dwieście — węzeł z trzydziestoma grupami musi przyjmować **wszystkie** ramki
rodzaju `KOMENDA_GRUPOWA` i odsiewać je programowo.

Jest to dopuszczalne, ale ma cenę: procesor budzi się do każdej komendy grupowej w całej
instalacji, także takiej, która go nie dotyczy. Przy obciążeniu magistrali poniżej procenta
jest to bez znaczenia; przy projektowaniu węzła zasilanego bateryjnie — nie byłoby, ale
takich w tej specyfikacji nie ma.

> **Zalecenie:** trzymaj liczbę grup na węzeł w granicach kilkunastu, jeśli chcesz zostać
> przy filtrowaniu sprzętowym.

### 5.4 Numer grupy znaczy dwie rzeczy

Ten sam numer jest **adresem zbiorczym** dla komend i **zakresem sceny**
([`0x0003-scenes.md`](0x0003-scenes.md) §2). Usunięcie endpointu z grupy wyjmuje go więc
także ze scen tej grupy — przestaje być przez nie obejmowany, choć same sceny zostają.

Węzeł **nie usuwa scen** przy `RemoveGroup` ani `RemoveAllGroups`. Scena grupy, do której
nie należy już żadne wyjście, jest wpisem martwym, ale nieszkodliwym; kasuje ją dopiero
`Scenes.RemoveAll` albo `FactoryReset`.

### 5.5 Endpoint wyłączony

Endpoint z atrybutem wspólnym `0xF3 Enabled = 0` **zachowuje przynależność**, ale nie
reaguje na komendy grupowe — tak samo jak nie reaguje na adresowane
([`../01-model-danych.md`](../01-model-danych.md) §4). Przynależność jest konfiguracją,
a nie stanem pracy, więc wyłączenie i włączenie endpointu jej nie gubi.

### 5.6 Trwałość

Tablica mieszka w pamięci trwałej i przeżywa restart. `FactoryReset` kasuje ją w całości
([`0x0001-device.md`](0x0001-device.md) §3.3).

---

## 6. Reprezentacja poza magistralą

`Groups` nie jest funkcją urządzenia i użytkownik nie obsługuje go wprost — obsługuje
skutek, czyli to, że kilka lamp gaśnie razem.

Zalecenie niezależne od adaptera: **hub powinien prowadzić własny obraz przynależności**
i traktować tablicę w węźle jako jej odwzorowanie, nie jako źródło. Powód jest ten sam co
przy scenach: nazwa grupy („parter", „salon") mieszka w hubie, a węzeł zna wyłącznie numer
([`../02-typy-danych.md`](../02-typy-danych.md) §2.2). Hub, który zgubi swój obraz, odzyska
z węzłów liczby — ale nie dowie się, co one znaczyły.
