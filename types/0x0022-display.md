# Typ endpointu `0x0022` · Display

> **Szkic.** Atrybuty i zachowanie rozstrzygnięte 2026-10-13. Cecha `VALUE` czeka na
> pierwsze zbudowane urządzenie (e-papier segmentowy z temperaturą i wilgotnością); cecha
> `TEXT` nie ma jeszcze urządzenia i jest sprawdzona tylko w symulatorze.

**Rewizja 1** · pole wyświetlacza

Jedno miejsce na ekranie, w którym urządzenie pokazuje to, co przyszło z systemu: liczbę
z jednostką — temperaturę z czujnika w innym pokoju, wilgotność, moc — albo krótki tekst.

> **Czym to się różni od [`Sense`](0x0030-sense.md).** `Sense` mierzy wartość, którą sam
> zna. Pole wyświetlacza **pokazuje wartość, której samo nie zna** — dostaje ją zapisem
> i niczego o niej nie wie poza tym, jak ją narysować.

> **Jeden endpoint to jedno pole, a nie cały ekran.** Ekran z temperaturą na górze i tekstem
> na dole to dwa endpointy `Display`. Każde pole ma własną treść, własny stan i własną nazwę
> w hubie. Cały ekran w jednym endpoincie potrzebowałby numeru pola w każdym zapisie, czyli
> adresowania wewnątrz endpointu — a tego protokół nigdzie nie ma i mieć nie powinien:
> endpoint **jest** najmniejszą adresowalną jednostką.

Typ jest celowo wąski. Wyświetlacze bywają dowolnie złożone, a wspólny kontrakt da się
utrzymać tylko dla tego, co mają wszystkie: miejsca na liczbę i miejsca na tekst. Układ
ekranu, czcionki, ikony i kolory należą do urządzenia (§5.9).

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
| — | *(zawsze)* | `Content`, `ContentTimeout` (opcjonalny) |
| 0 | `VALUE` | `Quantity`, `Value` — liczba z jednostką |
| 1 | `TEXT` | `TextLength`, `Text` — tekst |
| 2–15 | — | zarezerwowane, nadawaj `0` |

Pole może mieć jedną albo obie cechy. **Pole bez żadnej jest błędem urządzenia** — nie ma
czego pokazać.

Cechy odpowiadają budowie ekranu, a nie wyborowi huba: wyświetlacz segmentowy narysuje
cyfry, ale liter już nie, więc deklaruje sam `VALUE`. Ekran graficzny może zadeklarować oba.

---

## 2. Atrybuty

`Value` ma typ i skalę **wynikające z `Quantity`**, tak jak w [`Sense`](0x0030-sense.md) —
tabela wielkości jest w [`02-typy-danych.md`](../02-typy-danych.md) §3.

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | `Content` | `enum8` | RO | V | **tak** | M | §2.3 | `NONE` |
| `0x01` | `Quantity` | `enum8` | RO | P | nie | `[VALUE]` | wyliczenie z [`Sense`](0x0030-sense.md) §2.3 | ustala producent |
| `0x02` | `Value` | `⟨Q⟩` | RW | V | nie | `[VALUE]` | typ wielkości, także „brak" | brak |
| `0x03` | `TextLength` | `u8` | RO | P | nie | `[TEXT]` | 1–254 | ustala producent |
| `0x04` | `Text` | `string` | RW | V | nie | `[TEXT]` | 0…`TextLength` bajtów UTF-8 | pusty |

`Quantity` i `TextLength` są **deklaracją urządzenia**: mówią, co pole umie pokazać,
i nie zmieniają się w czasie pracy (§5.2, §5.3).

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | `ContentTimeout` | `u16` [s] | RW | P | nie | O | `0` albo 60–3600 | `600` |

`0` znaczy „treść nigdy się nie przeterminowuje" (§5.5).

Ustawienia raportowania są **atrybutami wspólnymi** `0xF8`–`0xFA` i ten typ ich nie
powiela ([`01-model-danych.md`](../01-model-danych.md) §4).

### 2.3 `Content`

| Wartość | Nazwa | Pole pokazuje |
|---|---|---|
| `0` | `NONE` | nic: kreski albo pustkę — jak, rozstrzyga urządzenie |
| `1` | `VALUE` | liczbę z `Value` |
| `2` | `TEXT` | tekst z `Text` |

---

## 3. Komendy

**Brak.** Wszystko, co pole pokazuje, jest **stanem**, a stan ustawia się zapisem — ta sama
zasada co w [`ValueInput`](0x0011-value-input.md). Czyszczenie pola to zapis wartości
„brak" albo pustego tekstu, a nie osobna komenda.

Rozważana była komenda `ShowValue(quantity, value)`. Jedynym realnym „za" była
niepodzielność wielkości i wartości w jednej ramce — a ta znika, gdy wielkość pola jest
stała (§5.2). Drugie „za", komenda grupowa pokazująca jedną liczbę na wielu
wyświetlaczach naraz, nie uzasadnia osobnej ścieżki dla kilku ekranów w instalacji.

---

## 4. Zdarzenia

**Brak.** Pole niczego nie mierzy i niczego nie decyduje — jego jedyną zmianą jest
zmiana tego, co pokazuje, a to jest stan i jedzie raportem `Content`. Przyciski przy
wyświetlaczu nie należą do pola (§5.9) — są osobnymi endpointami
[`KeyInput`](0x0010-key-input.md).

---

## 4a. Wejścia

| Bit | Atrybut | Czym jest |
|---|---|---|
| 0 | `Value` | liczba do pokazania |
| 1–15 | — | zarezerwowane, nadawaj `0` |

Pole może po starcie zapytać hub o `Value`, zamiast czekać na zapis
([`../04-interakcje.md`](../04-interakcje.md) §8). Pyta tylko wtedy, gdy hub zapalił bit
w `QueryEnabled` — czyli gdy ma dla tego pola źródło. Bez zapalonego bitu hub może nie znać
wartości i pytanie byłoby zgadywaniem. Wartość z odpowiedzi działa dokładnie jak zapis
(§5.1).

**`Text` nie jest wejściem**, choć wypełnia go hub. Odpowiedź huba na zapytanie jest
zawsze jedną ramką, a łańcuch znaków nigdy się w ramce nie mieści
([`../02-typy-danych.md`](../02-typy-danych.md) §2.2). Długiej odpowiedzi huba
specyfikacja nie ma i nie ma powodu jej dokładać dla jednego atrybutu.

**Bez wejścia pole działa normalnie**: pokazuje `NONE`, dopóki hub czegoś nie zapisze.
Nie czeka na odpowiedź i nie przestaje przyjmować zapisów.

---

## 5. Zachowanie

### 5.1 Treść przychodzi zapisem i zastępuje poprzednią

Zapis `Value` albo `Text` **od razu** zmienia to, co pole pokazuje, i ustawia `Content`.
Nowa treść zastępuje poprzednią w całości:

| Zapis | Pole pokazuje | `Content` | Drugi atrybut |
|---|---|---|---|
| `Value` = liczba | liczbę | `VALUE` | `Text` ← pusty |
| `Value` = „brak" | nic | `NONE` | `Text` ← pusty |
| `Text` = niepusty | tekst | `TEXT` | `Value` ← „brak" |
| `Text` = pusty | nic | `NONE` | `Value` ← „brak" |

Kolumna „drugi atrybut" dotyczy pola z obiema cechami i ma jeden cel: **odczyt zgadza się
z ekranem**. Pole, które pokazuje tekst, a na pytanie o `Value` odpowiada liczbą sprzed
pięciu minut, kłamie — i hub nie ma jak tego wykryć.

`Content` jest raportowany przy każdej zmianie. Hub, który sam pisze treść, raportu nie
potrzebuje; potrzebuje go przy przeterminowaniu (§5.5) i po restarcie węzła (§5.7), czyli
dokładnie wtedy, gdy pole zmienia się **bez** zapisu.

Zapis tej samej treści co obecna jest poprawny i nie zmienia `Content` — ale **odnawia
treść** w rozumieniu §5.5.

### 5.2 Wielkość pola jest stała

`Quantity` ustawia producent i **nie zmienia się w czasie pracy** — z tego samego powodu
co w [`Sense`](0x0030-sense.md) §2.3: od niej zależy typ `Value`, a zapisywalna wielkość
unieważniałaby wszystko, co hub o polu wie.

Wynika to też z budowy wyświetlaczy, dla których ta cecha istnieje. Pole segmentowe ma
jednostkę **narysowaną na stałe** — segment `°C` albo `%` — i innej wielkości nie pokaże.
Ekran, który umie pokazać dowolną liczbę z dowolną jednostką, potrzebuje cechy `TEXT`:
liczbę z jednostką formatuje wtedy hub, który i tak zna wielkość źródła.

`Value` = „brak" jest pokazywane jako brak, **nigdy jako zero** — ten sam powód co
w [`Sense`](0x0030-sense.md) §5.2: zero stopni na ekranie wygląda jak mróz, a nie jak awaria.

### 5.3 Tekst

`Text` jest łańcuchem UTF-8 i jak każdy łańcuch jedzie **zawsze zapisem długim**, także
pusty ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §6).

`TextLength` mówi, ile **bajtów** pole pomieści. Bajtów, nie znaków: `ż` to dwa bajty, więc
pole na 16 bajtów zmieści 16 liter łacińskich albo 8 polskich. Zapis dłuższy niż
`TextLength` kończy się `INVALID_VALUE` i nie zmienia niczego — hub zna `TextLength`
z enumeracji, więc ma jak tego uniknąć.

**Znak, którego urządzenie nie umie narysować, zastępuje `?`. Zapis nie jest odrzucany.**
Hub nie zna czcionki urządzenia i nie miałby jak uniknąć odmowy, a tekst z jednym znakiem
zastępczym jest czytelny. Polskie znaki warto mieć w czcionce każdego urządzenia z tą cechą.

Urządzenie może zawijać tekst w kilka linii, jeśli pole ma na to miejsce. Kontrakt tego
nie opisuje (§5.9).

### 5.4 Wartość, której pole nie zmieści

Pole segmentowe z trzema cyframi nie pokaże `1234,5`. **Zapis jest przyjmowany**, a pole
pokazuje kreski; `Content` zostaje `VALUE`, a odczyt `Value` zwraca to, co zapisano.

Odmowa byłaby gorsza: hub nie zna liczby cyfr pola, więc nie miałby jak jej uniknąć,
a powiązanie „czujnik → pole" zaczęłoby zgłaszać błędy przy każdym upale. `INVALID_VALUE`
zostaje dla tego, czego hub uniknąć **może**: wartości spoza zakresu typu i zbyt długiego
tekstu.

Ile miejsc po przecinku pokazać i jak zaokrąglić, rozstrzyga urządzenie. Skalę zna
z `Quantity`.

### 5.5 Treść się przeterminowuje

> **Treść, której hub nie odnowił przez `ContentTimeout`, znika: pole przechodzi w `NONE`.**

Przeterminowanie jest **obowiązkowe**, tak jak dla wejść
[`Thermostat`](0x0040-thermostat.md) §5.2 i z tego samego powodu: hub może paść, a pole
pokazujące temperaturę sprzed godziny wygląda dokładnie tak samo jak pole aktualne.
Kreski mówią prawdę, stara liczba — nie.

Czas liczy się od ostatniego zapisu treści albo odpowiedzi na zapytanie (§4a), także
zapisu tej samej wartości. Hub, który chce, żeby pole pokazywało coś stale, odnawia je
częściej niż `ContentTimeout` — przy powiązaniu z czujnikiem robi to sam raport cykliczny
źródła.

`ContentTimeout` jest **opcjonalny**. Pole, które go nie wystawia, stosuje własny, stały
czas z zakresu 60–3600 s ([`../01-model-danych.md`](../01-model-danych.md) §8.1).

W odróżnieniu od termostatu wolno ustawić `0` — „nigdy". Komunikat tekstowy („pranie
skończone") może mieć sens bez terminu, a hub wie, czy dane pole pokazuje pomiar, czy
komunikat. Pole bez atrybutu tej możliwości nie daje: jego czas jest zawsze skończony.

### 5.6 Wejście i przeterminowanie razem

Pole z zapalonym bitem `Value` w `QueryEnabled` **może zapytać ponownie** po
przeterminowaniu — nie częściej niż pozwala reguła dla zapytań
([`../04-interakcje.md`](../04-interakcje.md) §8.7). Odpowiedź `UNAVAILABLE` zostawia pole
w `NONE`.

### 5.7 Stan początkowy i restart

> **Po starcie pole jest puste: `Content = NONE`, `Value` = „brak", `Text` pusty.**

Treść jest ulotna. Wyświetlacz nie pamięta jej sprzed zaniku zasilania, bo po restarcie
byłaby nieaktualna, a pole nie ma jak tego oznaczyć.

Dotyczy to także ekranów, które obraz pamiętają bez zasilania, jak e-papier: **urządzenie
czyści pole przy starcie.** Stara liczba bez znaku „nieaktualne" jest gorsza niż kreski.

Osobnego raportu po starcie nie ma i nie jest potrzebny: hub dowiaduje się o restarcie
z `Booted` ([`0x0001-device.md`](0x0001-device.md) §5.1) i z niego wie, że pola węzła
trzeba wypełnić od nowa.

### 5.8 Koszt na magistrali

| Sytuacja | Ramki |
|---|---|
| zapis `Value` | 1 + odpowiedź; ładunek najwyżej 5 z 8 bajtów |
| zapis `Text` o długości *n* bajtów | ⌈(*n* + 1) / 6⌉ segmentów + odpowiedź; 32 bajty = 6 segmentów |
| zmiana `Content` | 1 raport |
| pole zasilane z czujnika | 1 zapis na `ReportInterval` źródła — domyślnie co 60 s |

Zapis jedzie z priorytetem niższym niż komenda, a zapis długi — za raportami. Dla
wyświetlacza to właściwa kolejność: treść na ekranie nigdy nie jest pilniejsza od
sterowania.

### 5.9 Czego typ świadomie nie robi

Grafiki, ikon, układu ekranu, kolorów, rozmiaru czcionki, przewijania, migania i wielu linii
w jednym polu (urządzenie może zawijać tekst, ale kontrakt tego nie opisuje). Każda z tych
rzeczy jest inna na każdym ekranie, a jej opis w kontrakcie albo byłby najmniejszym wspólnym
mianownikiem bez wartości, albo rozrósłby typ do języka opisu stron.

**Wejścia też nie.** Przyciski przy wyświetlaczu to osobne endpointy
[`KeyInput`](0x0010-key-input.md), jak w każdym panelu.

Urządzenie, które potrzebuje więcej, definiuje typ producencki
([`../registry/endpoint-types.yaml`](../registry/endpoint-types.yaml)) — i może mieć
**obok niego** pola `Display` dla tego, co zrozumie każdy hub.

---

## 6. Konfiguracje typowe

| Urządzenie | Cechy | Kluczowe atrybuty | Uwagi |
|---|---|---|---|
| E-papier segmentowy: temperatura i wilgotność | `VALUE` | dwa pola: `Quantity = TEMPERATURE`, `Quantity = HUMIDITY` | czyszczony przy starcie (§5.7) |
| Panel z wyświetlaczem LCD 2×16 | `TEXT` | dwa pola, `TextLength = 16` | liczby formatuje hub |
| Ekran graficzny: duża liczba i podpis | `VALUE` + `TEXT` | pole liczby i pole podpisu | dwa endpointy, nie jeden |
| Tablica komunikatów | `TEXT` | `TextLength = 64`, `ContentTimeout = 0` | komunikat nie wygasa |
| **Wykres, mapa, zdjęcie z kamery** | — | — | **nie tym typem** — §5.9 |

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia ten typ na zewnątrz, **nie należy do tej specyfikacji**.
Jedno zalecenie wynika jednak z charakteru pola:

> **Pole jest celem, a nie źródłem.** System nadrzędny pisze do niego treść; odczyt
> `Content` służy wyłącznie temu, żeby zobaczyć, czy pole coś pokazuje — a nie temu,
> żeby z niego brać dane.
