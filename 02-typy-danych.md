# 02 · Typy danych

> **Stabilne.** Skale są w praktyce zamrożone: zmiana skali istniejącej wielkości jest
> zmianą niezgodną wstecz (§6).

## 1. Dwie zasady

**Wszystkie pola wielobajtowe są little-endian.** Zarówno typowe mikrokontrolery, jak
i komputer huba są little-endian, więc na ścieżce krytycznej nie ma ani jednej zamiany
bajtów. To świadome odejście od automotive'owej konwencji Motorola/big-endian, spotykanej
w innych protokołach na CAN.

**Nie ma liczb zmiennoprzecinkowych.** Każda wielkość fizyczna jest liczbą całkowitą
o ustalonej skali. Powody:

- węzły to małe mikrokontrolery, zwykle bez jednostki zmiennoprzecinkowej; emulacja
  kosztuje pamięć programu i czas procesora, a jednego i drugiego jest niewiele,
- wartości całkowite porównują się dokładnie, więc histereza i progi działają
  przewidywalnie — `0.1 + 0.2 != 0.3` nie jest problemem, którego chcemy w termostacie,
- serializacja jest jednoznaczna, bez pytań o kolejność bajtów w mantysie.

Temperatura 21,50 °C jedzie jako `2150` typu `i16` przy skali 0,01 °C.

---

## 2. Typy podstawowe

| Typ | Rozmiar | Zakres | Wartość „brak" |
|---|---|---|---|
| `bool` | 1 B | `0` fałsz, `1` prawda | `0xFF` |
| `u8` | 1 B | 0 … 254 | `0xFF` |
| `u16` | 2 B | 0 … 65534 | `0xFFFF` |
| `u32` | 4 B | 0 … 4294967294 | `0xFFFFFFFF` |
| `i8` | 1 B | −127 … 127 | `0x80` |
| `i16` | 2 B | −32767 … 32767 | `0x8000` |
| `i32` | 4 B | −2147483647 … 2147483647 | `0x80000000` |
| `enum8` | 1 B | wyliczenie | `0xFF` |
| `enum16` | 2 B | wyliczenie | `0xFFFF` |
| `map8` | 1 B | pole bitowe | — |
| `map16` | 2 B | pole bitowe | — |
| `map32` | 4 B | pole bitowe | — |
| `string` | zmienny | UTF-8, prefiks długości `u8` | długość `0` |
| `blob` | zmienny | dane binarne, prefiks długości `u16` | długość `0` |

### 2.1 Wartość „brak"

Każdy typ liczbowy rezerwuje jedną wartość na oznaczenie **braku odczytu**: czujnik
się nie zainicjalizował, uległ awarii albo wartość nie jest jeszcze znana.

To dlatego zakresy są o jeden krótsze, niż wynikałoby z rozmiaru: `u16` sięga 65534,
a nie 65535. Ta jedna utracona wartość jest tania, a alternatywa — raportowanie zera
jako „nie wiem" — prowadzi do termostatu grzejącego pokój do −273 °C.

Pola bitowe nie mają wartości „brak": brak ustawionych bitów jest poprawnym stanem.

### 2.2 Łańcuchy znaków

Kodowanie UTF-8, więc polskie znaki działają. Łańcuchy **nigdy nie mieszczą się
w pojedynczej ramce** — przesyła się je w segmentach
([`05-mapowanie-can.md`](05-mapowanie-can.md) §6).

Jest to reguła, a nie rachunek: **łańcuch jedzie w segmentach zawsze, także pusty albo tak
krótki, że zmieściłby się obok nagłówka.** O sposobie przesłania decyduje wtedy typ
atrybutu, a nie długość wartości, więc obie strony mają jedną ścieżkę dla łańcuchów
i sprawdzają ją przy każdym przesłaniu, a nie tylko przy długich tekstach.

Działa to w obie strony: **wartość o stałej długości nigdy nie jedzie w segmentach.** Zapis
długi atrybutu liczbowego węzeł odrzuca kodem `INVALID_VALUE` — tak samo jak zwykły zapis
łańcucha.

Występują w dwóch rodzajach atrybutów:

- **opisujących sam sprzęt**: `VendorName` i `ModelName`
  ([`types/0x0001-device.md`](types/0x0001-device.md) §2.7). Są to nazwy fabryczne, nadane
  przez autora urządzenia, których użytkownik nie zmienia;
- **niosących treść do pokazania**: `Text` pola wyświetlacza
  ([`types/0x0022-display.md`](types/0x0022-display.md) §5.3). Jest ulotny, zapisuje go
  hub i nie przeżywa restartu węzła — to treść chwili, a nie nazwa.

Nazwy nadawane przez użytkownika („Salon, ściana wschodnia") **nie są przechowywane
w węźle** — także w polu wyświetlacza, które mogłoby je pokazywać: to hub zapisuje tam tekst
ze swojej bazy, a węzeł go nie pamięta. Mieszkają w bazie huba, kluczowane numerem `Uid`. Pamięć węzła jest zasobem
rzadkim, a tekst i tak trzeba backupować razem z resztą konfiguracji — przechowywanie go
po obu stronach byłoby marnotrawstwem.

Rozróżnienie jest warte uwagi, bo obie rzeczy są napisami i łatwo je pomylić: **jedna mówi,
czym urządzenie jest z fabryki, druga — czym jest dla mieszkańca.** Pierwsza mieszka
w węźle i nie zmienia się nigdy; druga mieszka w hubie i zmienia się przy pierwszym
przemeblowaniu.

---

## 3. Wielkości fizyczne i ich skale

Skala jest **właściwością wielkości, nie atrybutu**. Każda temperatura w całej
specyfikacji jest `i16` o skali 0,01 °C — bez wyjątków i bez negocjacji.

| Wielkość | Typ | Skala | Zakres praktyczny | Jednostka |
|---|---|---|---|---|
| `TEMPERATURE` | `i16` | 0,01 °C | −327,67 … 327,67 | `°C` |
| `HUMIDITY` | `u16` | 0,01 % | 0 … 100,00 | `%` |
| `ILLUMINANCE` | `u32` | 0,01 lx | 0 … 42 949 672 | `lx` |
| `CO2` | `u16` | 1 ppm | 0 … 65 534 | `ppm` |
| `VOC` | `u16` | 1 ppb | 0 … 65 534 | `ppb` |
| `PM25` | `u16` | 0,1 µg/m³ | 0 … 6 553 | `µg/m³` |
| `PRESSURE` | `u32` | 0,01 hPa | 0 … 42 949 672 | `hPa` |
| `FLOW` | `u32` | 0,001 l/min | 0 … 4 294 967 | `L/min` |
| `SOIL_MOISTURE` | `u16` | 0,01 % | 0 … 100,00 | `%` |
| `VOLTAGE` | `u32` | 0,001 V | 0 … 4 294 967 | `V` |
| `CURRENT` | `i32` | 0,001 A | ±2 147 483 | `A` |
| `POWER` | `i32` | 0,1 W | ±214 748 364 | `W` |
| `ENERGY` | `u32` | 1 Wh | 0 … 4,29 GWh | `Wh` |
| `DISTANCE` | `u32` | 1 mm | 0 … 4 294 km | `mm` |
| `ANGLE` | `i16` | 0,1 ° | −3276,7 … 3276,7 | `°` |

`CURRENT` i `POWER` są ze znakiem, bo instalacja z fotowoltaiką oddaje energię do sieci.

Wielkości **kumulacyjne** — te, które tylko rosną — nie należą do tej tabeli. Obsługuje je
typ [`Meter`](types/0x0031-meter.md), a kierunek jest w nim **atrybutem, nie osobnym
endpointem**: energia pobrana i oddana to dwie wartości jednego licznika.

| Wielkość | Typ | Skala | Jednostka |
|---|---|---|---|
| `ENERGY` | `u32` | 1 Wh | `Wh` |
| `VOLUME` | `u32` | 1 L | `L` |

Przy 32 bitach i skali 1 Wh licznik przepełni się po 4,29 GWh, czyli po jakichś
ośmiuset latach zużycia typowego domu. To nie wymaga obsługi przepełnienia.

### 3.1 Wielkości bezwymiarowe

| Wielkość | Typ | Zakres | Uwagi |
|---|---|---|---|
| **Poziom** | `u16` | 0 … 1000 ‰ | jasność, moc, otwarcie zaworu |
| **Pozycja** | `u16` | 0 … 1000 ‰ | 0 = zamknięte, 1000 = otwarte |
| **Składowa barwy** | `u8` | 0 … 255 | składowe R, G, B, W |
| **Temperatura barwowa** | `u16` | 1 … 65534 mired | 153 ≈ 6500 K, 500 ≈ 2000 K |

Poziom w promilach, a nie w procentach, bo tysiąc kroków to sensowna rozdzielczość
ściemniania przy dolnych 5% skali, gdzie oko jest najczulsze. System nadrzędny dostaje
z tego procenty przez zwykłe dzielenie.

### 3.2 Czas

| Zastosowanie | Typ | Jednostka |
|---|---|---|
| Krótkie odcinki (debounce, przejście, impuls) | `u16` | ms |
| Odstępy raportowania, opóźnienia | `u16` | s |
| Czas pracy od startu | `u32` | s |
| Czas kalendarzowy | `u32` | sekundy uniksowe UTC |

Strefa czasowa i czas letni są sprawą huba. Węzeł zna wyłącznie UTC — i to tylko
wtedy, gdy w ogóle potrzebuje czasu do wyświetlacza albo znaczników w logu.

**Żadna funkcja sterująca nie może zależeć od czasu kalendarzowego**, bo czas dryfuje
między synchronizacjami i po restarcie węzła znika.

---

## 4. Wyliczenia i pola bitowe

Wyliczenia definiuje typ, który ich używa; wartość `0` znaczy zawsze stan
domyślny albo neutralny.

Pola bitowe zawsze deklarują **wszystkie** bity, także nieużywane — te są oznaczone
jako zarezerwowane, muszą być nadawane jako `0` i ignorowane przy odbiorze. Dzięki
temu późniejsze dołożenie bitu jest zmianą wsteczną zgodną.

```
Features typu Output  (map16)
  bit 0   LEVEL
  bit 1   COLOR_RGB
  bit 2   COLOR_CCT
  bit 3–15  zarezerwowane, nadawaj 0
```

---

## 5. Tablice

Atrybut może być tablicą wartości stałego typu, zapisywaną jako `typ[n]`. Indeksuje
się od zera, a rozmiar jest stały i wynika z definicji atrybutu.

Tablica musi zmieścić się w jednej ramce, bo **zapis atrybutu jest z definicji operacją
na całości**. Zostaje na to siedem bajtów ([`05-mapowanie-can.md`](05-mapowanie-can.md)
§5.2), czyli siedem pozycji `u8` albo trzy `u16`.

Żaden typ nie korzysta dziś z tablicy stałej. Ostatnim kandydatem była przynależność do
grup i właśnie na tym ograniczeniu poległa: przy grupach numerowanych `u16` zmieściłyby się
trzy, czyli mniej, niż potrzeba ([`types/0x0004-groups.md`](types/0x0004-groups.md) §5.1).

Tablice o zmiennej długości — przynależność do grup, zawartość sceny — **nie są
atrybutami**. Obsługuje je typ wyspecjalizowany, z komendami dodawania, usuwania
i wyliczania pozycji: takiej tablicy nie chcemy przepisywać w całości przy każdej zmianie,
a zwykle nawet nie da się.

---

## 6. Zasady rozwoju

- Nowe wartości wyliczeń i nowe bity w polach bitowych — **zmiana wsteczna zgodna**,
  bo stare implementacje ignorują nieznane. Podnosi rewizję typu.
- Zmiana skali istniejącej wielkości, typu atrybutu albo znaczenia bitu — **zmiana
  niezgodna**. Nie da się jej przeprowadzić rewizją: wymaga **nowego identyfikatora typu**
  ([`08-wersjonowanie.md`](08-wersjonowanie.md) §3).

Powód jest prosty i nie do obejścia: węzeł w puszce podtynkowej **nie zostanie
zaktualizowany**. Reguła „podnieś rewizję i zaktualizuj wszystkie węzły" byłaby obietnicą,
której nikt nie spełni.

Skala raz ustalona jest ustalona na zawsze. Dlatego lepiej od razu wziąć zapas:
temperatura w setnych stopnia, choć żaden czujnik w tym domu nie będzie tak dokładny.
