# Wymagania zgodności

> **Dotyczy kontraktu w wersji `v0.1`, przed zamrożeniem.** Lista jest normatywna:
> implementacja, która nie spełnia wymagania oznaczonego `M`, **nie jest zgodna
> z LagunBusem** i nie wolno jej tak nazywać.
>
> Numeru `ProtocolVersion` lista jeszcze nie deklaruje, bo **v1 nie jest zamrożone**
> ([`08-wersjonowanie.md`](08-wersjonowanie.md) §7). Do tego czasu wymagania mogą się
> zmieniać razem ze specyfikacją; po zamrożeniu numer tu wpisany staje się częścią
> kontraktu.

Ten dokument istnieje po to, żeby autor urządzenia mógł sprawdzić swoją pracę **zanim
wepnie ją do magistrali**. Bez niego jedyną metodą jest podłączenie i debugowanie cudzego
huba — a to działa tylko wtedy, gdy autor ma numer telefonu do autora huba.

## Jak to czytać

| Oznaczenie | Znaczy |
|---|---|
| `M` | obowiązkowe — bez tego implementacja jest niezgodna |
| `O` | opcjonalne — wolno nie mieć, ale jeśli jest, musi działać tak |
| `[CECHA]` | obowiązkowe wtedy i tylko wtedy, gdy cecha jest zadeklarowana |
| `[CECHA, CECHA]` | obowiązkowe, gdy zadeklarowana jest **którakolwiek** z wymienionych |
| `O [CECHA]` | opcjonalne, ale dopuszczalne tylko przy zadeklarowanej cesze |

Numeracja jest **stała**: raz nadany numer nie zmienia znaczenia i nie jest używany
ponownie. Wymaganie wycofane zostaje na liście z adnotacją.

## Czego tu nie ma

**Wymagań wynikających wprost z tabel w [`types/`](types/).** Każdy typ endpointu ma
w swojej specyfikacji kolumnę `Konf.` przy każdym atrybucie, komendzie i zdarzeniu — i to
jest lista wymagań dla tego typu, kompletna i aktualna.

Powtarzanie jej tutaj byłoby drugą kopią, która by się rozjechała. Zamiast tego obowiązuje
reguła:

> **`LB-TYPE-001` `M`** — Endpoint deklarujący typ implementuje **wszystkie** jego elementy
> oznaczone `M` oraz wszystkie oznaczone `[CECHA]` dla cech, które zadeklarował. Brak
> choćby jednego oznacza, że tego typu **nie wolno deklarować**. Elementu oznaczonego
> `O [CECHA]` nie wolno mieć bez tej cechy.

---

## LB-CAN — ramka

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-CAN-001` | `M` | Identyfikator rozszerzony 29-bitowy, ładunek do 8 bajtów, CAN 2.0B | [`05`](05-mapowanie-can.md) §1 |
| `LB-CAN-002` | `M` | Układ pól: `RODZAJ` 4 b, `ADRES` 11 b, `ENDPOINT` 6 b, `ELEMENT` 8 b | [`05`](05-mapowanie-can.md) §1 |
| `LB-CAN-003` | `M` | Pola wielobajtowe **little-endian**, bez wyjątków | [`02`](02-typy-danych.md) §1 |
| `LB-CAN-004` | `M` | Nadawanie wyłącznie rodzajów przypisanych; wartości rezerwowych nie używać | [`05`](05-mapowanie-can.md) §2 |
| `LB-CAN-005` | `M` | Ramkę o **nieznanym rodzaju** odbiorca ignoruje: nie odpowiada i nie zgłasza błędu | [`08`](08-wersjonowanie.md) §4 |
| `LB-CAN-006` | `M` | Bity oznaczone jako zarezerwowane nadawane jako `0` i ignorowane przy odbiorze | [`02`](02-typy-danych.md) §4 |
| `LB-CAN-007` | `M` | Segmenty jednej wartości numerowane od `0`; segment `0` unieważnia poprzednie | [`05`](05-mapowanie-can.md) §6.5 |
| `LB-CAN-008` | `M` | Wartość porzucana w całości przy dziurze w numeracji albo ciszy dłuższej niż 100 ms | [`05`](05-mapowanie-can.md) §6.6 |

---

## LB-NODE — każdy węzeł

### Tożsamość i adres

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-001` | `M` | Endpoint `0` typu `Device`, endpoint `1` typu `Diagnostics`, endpoint `2` typu `Groups` | [`01`](01-model-danych.md) §1.2 |
| `LB-NODE-002` | `M` | Endpoint `3` typu `Scenes` **wtedy i tylko wtedy**, gdy węzeł ma choć jedno wyjście | [`01`](01-model-danych.md) §1.2 |
| `LB-NODE-003` | `M` | Endpointy funkcjonalne numerowane od `4` **bez przerw**, w porządku fizycznym urządzenia | [`06`](06-cykl-zycia-urzadzenia.md) §3.2 |
| `LB-NODE-004` | `M` | `Uid` niezmienny przez całe życie urządzenia, w tym po `FactoryReset` | [`types/Device`](types/0x0001-device.md) §3.3 |
| `LB-NODE-005` | `M` | `Address` w pamięci trwałej; po zaniku zasilania węzeł wraca pod tym samym adresem | [`03`](03-adresacja.md) §7 |
| `LB-NODE-006` | `M` | Węzeł bez adresu zgłasza się **bez końca**, z rosnącą zwłoką wg tabeli | [`03`](03-adresacja.md) §5.6 |
| `LB-NODE-007` | `M` | Węzeł bez adresu sygnalizuje to w sposób widoczny dla człowieka | [`03`](03-adresacja.md) §5.6 |
| `LB-NODE-008` | — | ~~Wykrycie ruchu spod własnego adresu → zerowanie adresu i powrót do przyłączania~~ **wycofane 2026-09-29**: reguła symetryczna, rozstrzygała źle albo wcale; węzły konfliktu nie wykrywają | [`03`](03-adresacja.md) §6 |
| `LB-NODE-009` | `M` | `ZGŁOSZENIE` niesie `NodeClass`; węzeł mieszany deklaruje klasę **najostrzejszego** ruchu, jaki generuje | [`05`](05-mapowanie-can.md) §4.1 |

### Kierunek ruchu

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-010` | `M` | Węzeł **nigdy** nie odczytuje ani nie zapisuje niczego u innego węzła | [`04`](04-interakcje.md) § wstęp |
| `LB-NODE-011` | `M` | Węzeł **nigdy** nie kieruje ramki pod cudzy adres | [`04`](04-interakcje.md) § wstęp |
| `LB-NODE-012` | `M` | Jedyną transakcją, którą węzeł inicjuje, jest `ZAPYTANIE` — i jest opcjonalna | [`04`](04-interakcje.md) §8 |

### Transakcje

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-020` | `M` | Odpowiedź powtarza `Tid` z żądania | [`04`](04-interakcje.md) §2 |
| `LB-NODE-021` | `M` | Obsługa **co najmniej jednego** żądania naraz; zajęty odpowiada `BUSY` | [`04`](04-interakcje.md) §10 |
| `LB-NODE-022` | `M` | Bufor deduplikacji **co najmniej ośmiu wpisów**, mieszczący każdą komendę z okna **300 ms** | [`04`](04-interakcje.md) §2.2 |
| `LB-NODE-023` | `M` | Klucz deduplikacji: `Tid` **razem z** endpointem i numerem komendy | [`04`](04-interakcje.md) §2.2 |
| `LB-NODE-024` | `M` | Komenda o powtórzonym kluczu **nie jest wykonywana ponownie**; odsyłany zapamiętany wynik | [`04`](04-interakcje.md) §2.2 |
| `LB-NODE-025` | `M` | Żądania obsługiwane **w kolejności odbioru**, bez zmiany kolejności i łączenia | [`04`](04-interakcje.md) §10 |
| `LB-NODE-026` | `M` | Zapis atrybutu **niepodzielny**: albo w całości, albo wcale | [`04`](04-interakcje.md) §4 |
| `LB-NODE-027` | `M` | Atrybut trwały zapisany do pamięci **przed** wysłaniem odpowiedzi | [`04`](04-interakcje.md) §4.1 |
| `LB-NODE-028` | `M` | Nieudany zapis do pamięci → `FAILURE`, nigdy `OK` | [`04`](04-interakcje.md) §4.1 |

### Raporty i zdarzenia

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-030` | `M` | Raport przy zmianie i cyklicznie — **oba naraz**, nie alternatywnie | [`01`](01-model-danych.md) §6.1 |
| `LB-NODE-031` | `M` | Odstęp raportów z jednego endpointu nie mniejszy niż `ReportMinGap` | [`01`](01-model-danych.md) §6 |
| `LB-NODE-032` | `M` | Histereza dotyczy atrybutów liczbowych; dla `bool`, `enum` i pól bitowych każda zmiana jest zmianą | [`01`](01-model-danych.md) §6.2 |
| `LB-NODE-033` | `M` | Zdarzenia z jednego endpointu numerowane kolejno, licznik `u8` zawijający | [`01`](01-model-danych.md) §3.3 |
| `LB-NODE-034` | `M` | Zdarzenia **nie są retransmitowane** ani nadrabiane | [`04`](04-interakcje.md) §7.1 |
| `LB-NODE-035` | `M` | Kolejka pełna → porzucany **najstarszy raport**, nigdy zdarzenie ani odpowiedź | [`types/Diagnostics`](types/0x0002-diagnostics.md) §5.3 |

### Wartości

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-040` | `M` | Brak odczytu raportowany jako **wartość „brak"**, nigdy jako zero | [`02`](02-typy-danych.md) §2.1 |
| `LB-NODE-041` | `M` | Skale wielkości wg [`registry/quantities.yaml`](registry/quantities.yaml), bez odstępstw | [`02`](02-typy-danych.md) §3 |
| `LB-NODE-042` | `M` | Nieznana wartość wyliczenia traktowana jako nieznana, **nie jako domyślna** | [`08`](08-wersjonowanie.md) §4 |
| `LB-NODE-043` | `M` | Nieznany kod wyniku traktowany jako **błąd**, nigdy jako powodzenie | [`08`](08-wersjonowanie.md) §4 |

### Start i diagnostyka

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-050` | `M` | Przed `Booted`: odtworzenie konfiguracji, inicjalizacja endpointów, przyłączenie do magistrali | [`types/Device`](types/0x0001-device.md) §5.1 |
| `LB-NODE-051` | `M` | Węzeł nie odpowiada na nic, dopóki nie wyśle `Booted` | [`types/Device`](types/0x0001-device.md) §5.1 |
| `LB-NODE-052` | `M` | Powrót z odłączenia od magistrali **automatyczny**; restart ani ingerencja człowieka niedozwolone | [`types/Diagnostics`](types/0x0002-diagnostics.md) §5.2 |
| `LB-NODE-053` | `M` | Po powrocie z odłączenia **nie** emitować `Booted` — nie było restartu | [`types/Diagnostics`](types/0x0002-diagnostics.md) §5.2 |
| `LB-NODE-054` | `M` | Liczniki błędów odczytywane z kontrolera CAN, nie liczone w oprogramowaniu | [`types/Diagnostics`](types/0x0002-diagnostics.md) §5.1 |
| `LB-NODE-055` | `M` | `Identify` przyjmowana, potwierdzana i widoczna na diodzie stanu przez `duration`; `duration = 0` przerywa | [`types/Device`](types/0x0001-device.md) §3.1 |
| `LB-NODE-056` | `M` | `FactoryReset` bez argumentu `0x4C41474E` **odrzucana** | [`types/Device`](types/0x0001-device.md) §3.3 |
| `LB-NODE-057` | `M` | Przycisk serwisowy: reset fabryczny o skutku `FactoryReset`, zabezpieczony przed przypadkowym użyciem | [`types/Device`](types/0x0001-device.md) §5.4 |
| `LB-NODE-058` | `M` | Dioda stanu rozróżnia reset, identyfikację, usterkę magistrali, brak adresu i pracę; przy kilku naraz — stan wyższy w kolejności | [`types/Device`](types/0x0001-device.md) §5.4 |

### Zgodność w przód

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-NODE-060` | `M` | Nieznany atrybut lub komenda → `UNSUPPORTED_ELEMENT` | [`08`](08-wersjonowanie.md) §4 |
| `LB-NODE-061` | `M` | Element spoza zadeklarowanych cech → `UNSUPPORTED_FEATURE` | [`04`](04-interakcje.md) §9 |
| `LB-NODE-062` | `M` | Zachowanie węzła **nie zależy** od wersji rozmówcy; brak negocjacji wersji | [`08`](08-wersjonowanie.md) §6 |
| `LB-NODE-063` | `M` | Poprawne zadeklarowanie `ProtocolVersion` i `TypeRevision` każdego endpointu | [`08`](08-wersjonowanie.md) §1 |

---

## LB-HUB — hub

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-HUB-001` | `M` | Cała konfiguracja kluczowana `Uid`, **nigdy adresem** | [`07`](07-hub.md) §2 |
| `LB-HUB-002` | `M` | Adresy niepowtarzalne w **całej instalacji**, także między magistralami | [`03`](03-adresacja.md) §2.1 |
| `LB-HUB-003` | `M` | Hub **nie powtarza ramek** między magistralami; nadaje własne | [`03`](03-adresacja.md) §4.3 |
| `LB-HUB-004` | `M` | Komenda grupowa nadawana osobno na każdej magistrali z członkami grupy | [`03`](03-adresacja.md) §3.1 |
| `LB-HUB-005` | `M` | Od odebrania zdarzenia do przekazania komendy magistrali **najwyżej 50 ms**; bez kolejkowania i buforowania | [`07`](07-hub.md) §4.2 |
| `LB-HUB-006` | `M` | Skutek powiązania **nie wyzwala** kolejnego powiązania | [`07`](07-hub.md) §4.1 |
| `LB-HUB-007` | `M` | Powiązanie na atrybut wyzwalane **przy zmianie wartości**, nie przy każdym raporcie | [`07`](07-hub.md) §3.1 |
| `LB-HUB-008` | `M` | Brak powiązania **nie jest błędem** | [`07`](07-hub.md) §4 |
| `LB-HUB-010` | `M` | Po restarcie: nasłuchiwanie, **nie** odpytywanie wszystkich węzłów | [`07`](07-hub.md) §5.1 |
| `LB-HUB-011` | `M` | **Nie odtwarzać** zaległych zdarzeń po restarcie | [`07`](07-hub.md) §5.2 |
| `LB-HUB-012` | `M` | Nie zakładać stanu wyjść sprzed restartu; prawdą jest pierwszy raport | [`07`](07-hub.md) §5.2 |
| `LB-HUB-013` | `M` | Konfiguracja przepisywana **od huba do węzła**, nigdy w drugą stronę | [`07`](07-hub.md) §5.3 |
| `LB-HUB-020` | `M` | `ZAPYTANIE`: odpowiedź **natychmiast** z własnego modelu; źródła zewnętrzne odpytywane w tle | [`04`](04-interakcje.md) §8.2 |
| `LB-HUB-021` | `M` | `QueryEnabled` zapisywane przy zmianie **mapowania**, nie przy zmianie dostępności źródła | [`04`](04-interakcje.md) §8.6 |
| `LB-HUB-022` | `M` | Ten sam `Tid` nie używany ponownie wobec tego samego klucza (węzeł, endpoint, element) przed upływem okna deduplikacji | [`04`](04-interakcje.md) §2 |
| `LB-HUB-023` | `M` | Spadek wartości licznika `Meter` wykryty; różnica ujemna **nie jest liczona** | [`types/Meter`](types/0x0031-meter.md) §5.2 |
| `LB-HUB-024` | `M` | Wobec węzła używane wyłącznie elementy mieszczące się w jego `ProtocolVersion` i `TypeRevision` | [`08`](08-wersjonowanie.md) §5 |
| `LB-HUB-025` | `M` | Węzeł o innym `major` **nie jest interpretowany**; zgłaszany operatorowi | [`08`](08-wersjonowanie.md) §2.1 |
| `LB-HUB-026` | `M` | Hub **nie konfiguruje** elementów spoza cech zadeklarowanych przez endpoint; taka konfiguracja zgłaszana operatorowi | [`01`](01-model-danych.md) §2.1 |
| `LB-HUB-030` | `M` | Tryb przyjmowania nowych urządzeń wygasa samoczynnie po 15 minutach | [`06`](06-cykl-zycia-urzadzenia.md) §2.1 |
| `LB-HUB-031` | `M` | `ShortId` znany hubowi dostaje adres **zawsze**, niezależnie od trybu przyjmowania | [`06`](06-cykl-zycia-urzadzenia.md) §2.1 |
| `LB-HUB-032` | `M` | Adres dla nieznanego `ShortId` brany z **bloku wskazanego przez `NodeClass`**; `UNSPECIFIED` → rezerwa | [`03`](03-adresacja.md) §2.3 |
| `LB-HUB-033` | `M` | Po enumeracji zgodność klasy z deskryptorem sprawdzona; rozjazd → przesunięcie zapisem `Device.Address` | [`06`](06-cykl-zycia-urzadzenia.md) §4.1 |
| `LB-HUB-034` | `M` | `NodeClass` **nie jest** używany do interpretacji zdolności węzła — wyłącznie do wyboru bloku | [`05`](05-mapowanie-can.md) §4.1 |
| `LB-HUB-035` | `M` | Adres słyszany na magistrali od startu huba **nie jest przydzielany**, niezależnie od bazy | [`03`](03-adresacja.md) §6 |
| `LB-HUB-036` | `M` | Ramka węzła spod adresu nieznanego → odczyt `Device.Uid` i `Device.ShortId` spod tego adresu, **raz na adres**; oba nieznane → `OCZEKUJĄCY` | [`06`](06-cykl-zycia-urzadzenia.md) §2.3 |
| `LB-HUB-037` | `M` | Węzeł z adresem nieznanym hubowi, którego `Uid` **nie ma w konfiguracji huba**, **nie jest przyjmowany samoczynnie**, także przy włączonym trybie przyjmowania | [`06`](06-cykl-zycia-urzadzenia.md) §2.3 |
| `LB-HUB-038` | `M` | Węzeł z adresem nieznanym hubowi, którego `Uid` jest w konfiguracji huba i nie jest zablokowany → enumeracja pod obecnym adresem, **bez decyzji operatora** | [`06`](06-cykl-zycia-urzadzenia.md) §2.3 |
| `LB-HUB-039` | `M` | Adres i `ShortId` każdego przyłączonego węzła **przeżywają restart huba** | [`07`](07-hub.md) §5 |
| `LB-HUB-040` | `M` | Próg ciszy = **2 × najkrótszy niezerowy `ReportInterval`** węzła; `300 s`, gdy raportowanie cykliczne wyłączone wszędzie | [`06`](06-cykl-zycia-urzadzenia.md) §5.1 |
| `LB-HUB-041` | `M` | Endpointy wyłączone atrybutem `Enabled` **nie liczą się** do wyliczenia progu | [`06`](06-cykl-zycia-urzadzenia.md) §5.1 |
| `LB-HUB-042` | `M` | Po przekroczeniu progu: odczyt `Device.Uptime`; **trzy nieudane próby co 10 s** → `NIEOBECNY` | [`06`](06-cykl-zycia-urzadzenia.md) §5.2 |
| `LB-HUB-043` | `M` | Spadek `Uptime` względem poprzedniego odczytu rozpoznany jako **przeoczony restart** | [`06`](06-cykl-zycia-urzadzenia.md) §5.2 |
| `LB-HUB-044` | `M` | Usunięcie zwykłe: hub zapomina węzeł **dopiero po potwierdzeniu** `FactoryReset`; bez potwierdzenia nic się nie zmienia | [`06`](06-cykl-zycia-urzadzenia.md) §6.1 |
| `LB-HUB-045` | `M` | Po usunięciu `ShortId` traktowany jak nieznany — wraca **tylko** przez tryb przyjmowania | [`06`](06-cykl-zycia-urzadzenia.md) §6 |
| `LB-HUB-046` | `M` | Węzeł zablokowany **nie dostaje adresu** przy przyłączaniu, także przy włączonym trybie przyjmowania | [`06`](06-cykl-zycia-urzadzenia.md) §8 |
| `LB-HUB-047` | `M` | Zdarzenia i raporty węzła zablokowanego **nie wyzwalają powiązań**; żadne powiązanie nie ma go za cel | [`06`](06-cykl-zycia-urzadzenia.md) §8 |
| `LB-HUB-048` | `M` | Blokada przeżywa restart huba | [`06`](06-cykl-zycia-urzadzenia.md) §8 |

---

## Wymagania warunkowe

| Nr | | Wymaganie | Źródło |
|---|---|---|---|
| `LB-OUT-001` | `[LEVEL]` | `Level` jest jedynym stanem prawdziwym; `OnOff = (Level > 0)` | [`types/Output`](types/0x0020-output.md) §5.1 |
| `LB-OUT-002` | `[LEVEL]` | `Step` nasyca się na `MinLevel`/`MaxLevel`, **nigdy nie przechodzi przez zero** | [`types/Output`](types/0x0020-output.md) §5.2 |
| `LB-OUT-003` | `[LEVEL]` | `Level` **nie jest raportowany w trakcie przejścia** — tylko na początku i końcu | [`types/Output`](types/0x0020-output.md) §5.3 |
| `LB-KEY-001` | `M` | `Down`/`Up` wyłącznie w trybie `RAW`; w `CLICK` i `MULTICLICK` naciśnięcie nie emituje niczego przed kliknięciem albo przytrzymaniem | [`types/KeyInput`](types/0x0010-key-input.md) §5.5 |
| `LB-KEY-002` | `M` | Czas nieobecny jako atrybut stosowany **stały i w zakresie z tabeli typu** | [`types/KeyInput`](types/0x0010-key-input.md) §2.4 |
| `LB-KEY-003` | `[HOLD]` | Zwolnienie po przytrzymaniu to **wyłącznie** `HoldEnd` — bez `Click` i bez `Up` | [`types/KeyInput`](types/0x0010-key-input.md) §5.5 |
| `LB-KEY-004` | `[HOLD]` | `HoldTick` ustaje po 60 s trzymania; `HoldEnd` przy zwolnieniu przychodzi normalnie | [`types/KeyInput`](types/0x0010-key-input.md) §5.6 |
| `LB-SCN-001` | `M` | `SceneCapacity` ≥ 8; pojemność liczona w **parach** `(grupa, numer)` | [`types/Scenes`](types/0x0003-scenes.md) §3 |
| `LB-MTR-001` | `M` | Licznik **nigdy nie maleje** poza `FactoryReset` | [`types/Meter`](types/0x0031-meter.md) §5.2 |
| `LB-MTR-002` | `M` | Zapis licznika do pamięci trwałej nie częściej niż raz na 10 minut | [`types/Meter`](types/0x0031-meter.md) §5.4 |
| `LB-THR-001` | `M` | Bez temperatury regulator **wyłącza wyjście** i nie reguluje | [`types/Thermostat`](types/0x0040-thermostat.md) §5.3 |
| `LB-THR-002` | `M` | `RemoteTemperature` starsza niż `SourceTimeout` traktowana jak **brak** | [`types/Thermostat`](types/0x0040-thermostat.md) §5.2 |
| `LB-THR-003` | `M` | Regulator **nie adresuje** wyjścia na innym węźle | [`types/Thermostat`](types/0x0040-thermostat.md) §5.4 |

---

## Czego ta lista nie sprawdza

**Czasów i długości magistrali.** Prędkość i maksymalna długość odcinka nie są jeszcze
ustalone, więc zgodność elektryczna nie jest tu opisana.

**Zachowania adaptera północnego.** Jest poza zakresem całej specyfikacji.

**Jakości implementacji.** Węzeł może spełniać każde wymaganie i być źle zbudowany —
lista mówi, czy mówi tym samym językiem, a nie czy mówi mądrze.
