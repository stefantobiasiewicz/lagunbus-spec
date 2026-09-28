# Typ endpointu `0x0003` · Scenes

> **Stabilne.** Model i komendy ustalone. Minimalna pojemność może jeszcze wzrosnąć.

**Rewizja 1** · zapamiętane stany wyjść, kluczowane grupą

Siedzi na **endpoincie 3** i jest obecny **wtedy i tylko wtedy, gdy węzeł ma choć jedno
wyjście** typu [`Output`](0x0020-output.md). Węzeł złożony z samych klawiszy i czujników
tego endpointu nie ma.

Scena to zapamiętany stan wyjść, przywoływany jednym numerem. Nie jest to scena
w rozumieniu systemu automatyki — ta obejmuje cały dom i mieszka w systemie nadrzędnym.
Tu chodzi o coś węższego i o jeden konkretny zysk: **jednoczesność**.

---

## 1. Cechy

**Brak.** Węzeł różni się pojemnością tablicy scen, a to atrybut (`SceneCapacity`),
nie cecha — wartość odczytuje się z urządzenia, zamiast wnioskować ją z bitu.

---

## 2. Tożsamość sceny

> **Scenę identyfikuje para `(grupa, numer)`, nie sam numer.**

Grupa mówi, **których wyjść** scena dotyczy; numer — **który z zapamiętanych stanów**.

| Grupa | Scena obejmuje |
|---|---|
| `1`–`2047` | wyjścia węzła należące do tej grupy ([`../03-adresacja.md`](../03-adresacja.md) §3.1) |
| `0` | **wszystkie** wyjścia węzła, niezależnie od przynależności |

Numer sceny to `1`–`255`; `0` jest zarezerwowane i znaczy „żadna scena".

### 2.1 Dlaczego para, a nie sam numer

Trzy powody, każdy wystarczający sam z siebie.

**Grupa jest już w ramce.** Komenda grupowa niesie numer grupy w polu adresu
([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §2), więc przy przywołaniu grupowym
węzeł zna grupę za darmo — nie trzeba jej powtarzać w ładunku ani wymagać, żeby endpoint
systemowy `3` do czegokolwiek należał.

**Ziarnistość.** Przy samym numerze scena musiałaby obejmować wszystkie wyjścia węzła.
Ośmiokanałowy moduł z czterema kanałami na parterze i czterema na piętrze nie mógłby mieć
osobnej sceny wieczornej dla każdej połowy. Przy kluczu z grupą może.

**Jedno wyjście w kilku scenach.** Kanał należący do dwóch grup bierze udział w scenach
obu. Przywołania nie mieszają się, bo każde dotyczy innego zbioru wyjść.

---

## 3. Atrybuty

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | `SceneCapacity` | `u8` | RO | P | nie | M | 8–255 | — |
| `0x01` | `SceneCount` | `u8` | RO | P | tak | M | 0–`SceneCapacity` | `0` |
| `0x02` | `LastGroup` | `u16` | RO | V | tak | O | 0–2047 | `0` |
| `0x03` | `LastScene` | `u8` | RO | V | tak | O | 0–255 | `0` |

`SceneCapacity` liczy **pary**, nie numery: wpisy `(1, 4)` i `(2, 4)` zajmują dwa miejsca.
Wynosi co najmniej osiem — poniżej tej liczby mechanizm przestaje być użyteczny, a węzeł
i tak musi mieć pamięć trwałą na konfigurację wyjść.

Sufit `255` jest limitem specyfikacji, nie zaleceniem. Realną wartość dyktuje pamięć:
wpis to trzy bajty klucza plus stan wyjść, a ten rośnie z ich liczbą i cechami.

| Urządzenie | Wpis | 64 sceny | 255 scen |
|---|---|---|---|
| ośmiokanałowy przekaźnik | 11 B | 0,7 kB | 2,8 kB |
| ośmiokanałowy sterownik RGBW | 51 B | 3,3 kB | 13 kB |

Przy pamięci nieulotnej emulowanej we flashu mikrokontrolera trzynaście kilobajtów to dużo.
Dlatego pojemność deklaruje każdy moduł osobno, zamiast wynikać z typu.

`LastGroup` i `LastScene` mówią, **co przywołano ostatnio**, a nie co obowiązuje teraz.
Rozróżnienie jest istotne: węzeł może mieć równocześnie przywołaną scenę `(1, 4)` na jednej
połowie wyjść i `(2, 7)` na drugiej, a ta para pokazuje wyłącznie późniejsze z przywołań.
`LastScene = 0` znaczy „żadna" — nic jeszcze nie przywołano albo stan wyjść zmienił się po
przywołaniu (§6.5).

---

## 4. Komendy

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | `Store` | `group: u16`, `scene: u8` | M |
| `0x01` | `Recall` | `group: u16`, `scene: u8`, `transition: u16` [ms] | M |
| `0x02` | `Remove` | `group: u16`, `scene: u8` | M |
| `0x03` | `RemoveAll` | `group: u16` | M |

Wywołane **adresowo** są transakcjami i dostają odpowiedź z kodem wyniku
([`../04-interakcje.md`](../04-interakcje.md) §5).

### 4.1 Postać grupowa

Przy wywołaniu grupowym **argument `group` znika z ładunku** — węzeł bierze go z pola
adresu ramki:

```
adresowo   KOMENDA          ep=3   [0] nagłówek  [1..2] group  [3] scene  [4..5] transition
grupowo    KOMENDA_GRUPOWA  ep=3   [0] scene  [1..2] transition
```

Pole endpointu niesie **`3`**, a nie zero: komendę wykonuje ten typ, a nie endpointy
należące do grupy ([`../04-interakcje.md`](../04-interakcje.md) §5.2). Zero oznaczałoby
„rozdziel do członków grupy" i trafiłoby w wyjścia, dla których `0x01` znaczy `On`, a nie
`Recall`.

Endpoint `3` **sam do żadnej grupy nie należy** — w tablicy przynależności
([`0x0004-groups.md`](0x0004-groups.md)) wpisuje się wyłącznie endpointy, które przyjmują
komendy grupowe. Nie jest to potrzebne: węzeł przyjmuje ramkę grupową, gdy do grupy należy
**którekolwiek z jego wyjść**, a obsługuje ją endpoint `3`, czytając numer grupy prosto
z ramki. To jest właśnie powód, dla którego scena jest kluczowana parą.

Grupa `0` nie jest adresem grupowym ([`../03-adresacja.md`](../03-adresacja.md) §3.1),
więc **sceny grupy `0` przywołuje się wyłącznie adresowo**. Jest to spójne z ich
znaczeniem: dotyczą całego węzła, więc i tak kieruje się je do konkretnego węzła.

### 4.2 Kody wyniku

| Sytuacja | Wynik |
|---|---|
| `scene = 0` | `INVALID_VALUE` — numer zarezerwowany |
| `group > 0x7FF` | `INVALID_VALUE` — poza przestrzenią grup |
| `Store` dla grupy, do której nie należy żadne wyjście węzła | `INVALID_STATE` |
| `Store` przy zapełnionej tablicy | `INSUFFICIENT_SPACE` |
| `Recall` albo `Remove` nieistniejącej pary | `INVALID_STATE` |
| zapis do pamięci trwałej się nie powiódł | `FAILURE` |

`transition` zachowuje się tak jak w typie `Output`: `0` oznacza zmianę natychmiastową,
`0xFFFF` — „użyj `DefaultFadeTime`" każdego wyjścia z osobna
([`0x0020-output.md`](0x0020-output.md) §3).

---

## 5. Zdarzenia

**Brak.** Przywołanie sceny jest widoczne w raportach wyjść, które się zmieniły, a samo
polecenie pochodzi od huba — więc hub i tak o nim wie. Zdarzenie opisywałoby fakt, który
nadawca sam wywołał ([`01-model-danych.md`](../01-model-danych.md) §3).

---

## 6. Zachowanie

### 6.1 Co scena obejmuje

Scena zapamiętuje **pełny stan wyjść należących do jej grupy**, w zakresie wynikającym
z cech każdego z nich:

```
Store(grupa 1, scena 4) na module, w którym

  ep4  Output [LEVEL]              w grupie 1   → zapamiętany: Level
  ep5  Output [LEVEL | COLOR_RGB]  w grupie 1   → zapamiętany: Level, R, G, B, W
  ep6  Output —                    w grupie 2   → pominięty, inna grupa
```

Przy grupie `0` zapamiętywane są **wszystkie** wyjścia węzła, bez oglądania się na
przynależność.

Scena **nie obejmuje** konfiguracji (`MinLevel`, `PowerOnBehaviour`, `Purpose`) ani niczego,
co nie jest wyjściem. Konfiguracja opisuje, czym urządzenie jest; scena — w jakim jest
stanie. Mieszanie tych dwóch rzeczy oznaczałoby, że przywołanie sceny może przestawić
próg ściemniania, a tego nikt się nie spodziewa.

Wyjście z atrybutem wspólnym `0xF3 Enabled = 0` jest w scenie pomijane — i przy zapisie,
i przy przywołaniu.

**Kanały nie mają tu znaczenia.** O składzie sceny rozstrzyga wyłącznie grupa; kanał opisuje
układ fizyczny urządzenia i z adresowaniem nie ma nic wspólnego
([`../01-model-danych.md`](../01-model-danych.md) §5.2).

### 6.2 Dlaczego scena mieszka w węźle

To jest jedyne miejsce w całej specyfikacji, w którym węzeł pamięta stan sterowania —
a więc wymaga uzasadnienia mocniejszego niż wygoda.

Powodem jest **ośmiobajtowa ramka**. Polecenie jednorodne — „zgaś" — mieści się w komendzie
bez argumentów i sceny nie potrzebuje. Ale „lampa nad stołem na 30%, kinkiety na 10%, taśma
w ciepłej bieli" to trzydzieści różnych wartości docelowych, czyli setki bajtów. Nie ma
sposobu, żeby przesłać to jedną ramką.

Scena przenosi te wartości **do węzłów z wyprzedzeniem**. Ramka wyzwalająca niesie już tylko
numer — i dlatego może być jedna, a wszystkie wyjścia ruszają w tej samej milisekundzie.
Przywołanie komendą po komendzie dałoby kaskadę rozciągniętą na kilkanaście milisekund,
którą widać i która wygląda na usterkę.

> **Scena nie jest regułą i nie zastępuje huba.** Węzeł nigdy nie przywołuje sceny sam:
> nie ma warunku, harmonogramu ani reakcji na zdarzenie. Przywołanie zawsze pochodzi
> z zewnątrz ([`00-wprowadzenie.md`](../00-wprowadzenie.md) § Kierunek ruchu).

To jest granica, której warto pilnować przy rozbudowie tego typu. Scena przechowuje
**wartości**, nie zachowanie.

### 6.3 Zapisuj adresowo, przywołuj grupowo

Przywołanie grupowe jest **niepotwierdzane** i nie ma `Tid`
([`../04-interakcje.md`](../04-interakcje.md) §5.1). Wynika stąd podział ról:

| Operacja | Jak wysyłać | Dlaczego |
|---|---|---|
| `Recall` | **grupowo** | o to w tym wszystkim chodzi — jednoczesność |
| `Store` | **adresowo, do każdego węzła osobno** | niżej |
| `Remove`, `RemoveAll` | adresowo | j.w. |

`Store` wysłany grupowo **zadziała** — ale nikt się nie dowie, czy się udało. Zapis do
pamięci trwałej bywa nieudany, a skutku `Store` nie widać w żadnym raporcie: wyjścia się
nie zmieniają. Byłaby to jedyna operacja w całej specyfikacji, której niepowodzenie jest
całkowicie niewidoczne.

Zapis zdarza się raz przy konfiguracji, przywołanie — codziennie. Koszt odwrotnego wyboru
jest więc niesymetryczny.

### 6.4 Wyjście w kilku grupach

Wyjście należące do dwóch grup bierze udział w scenach obu. Przywołania **nie mieszają
się** — każde dotyczy innego zbioru wyjść — ale mogą się nawzajem nadpisywać: jeśli
`Recall(1, 4)` i `Recall(2, 7)` obejmują to samo wyjście, obowiązuje późniejsze.

Jest to ta sama reguła co przy dwóch sprzecznych komendach
([`../04-interakcje.md`](../04-interakcje.md) §10): wygrywa późniejsza, bo taka była
kolejność na magistrali.

### 6.5 Kiedy scena przestaje być aktywna

`LastGroup` i `LastScene` są ustawiane przy udanym `Recall` i **zerowane przy każdej zmianie
stanu dowolnego wyjścia z innego powodu** — komendą adresowaną, wyłączeniem automatycznym
(`AutoOffTime`), przywróceniem po zaniku zasilania.

Jest to jedyny uczciwy sposób, by odpowiedzieć na pytanie „czy scena nadal obowiązuje".
Scena „wieczór" przestaje obowiązywać w chwili, gdy ktoś przygasi jedną lampę — stan
wyjść przestał odpowiadać zapamiętanemu i udawanie, że nadal odpowiada, wprowadzałoby
w błąd.

Węzeł **nie porównuje** stanu bieżącego z zapamiętanym, żeby wykryć powrót do sceny.
Kosztowałoby to pamięć i czas, a zysk byłby żaden: przywrócenie ręką dokładnie tych samych
wartości zdarza się nigdy.

### 6.6 Trwałość i reset

Sceny mieszkają w pamięci trwałej i przeżywają restart. `LastGroup` i `LastScene` nie — są
ulotne i po starcie wynoszą `0`, bo stan wyjść ustala wtedy `PowerOnBehaviour`, a nie scena
([`0x0020-output.md`](0x0020-output.md) §2.3).

`FactoryReset` kasuje wszystkie sceny, tak jak całą resztę konfiguracji
([`0x0001-device.md`](0x0001-device.md) §3.3).

### 6.7 Przywołanie a ograniczenia wyjścia

Przywołana wartość przechodzi przez **te same ograniczenia co komenda `SetLevel`**:
nasycenie na `MinLevel` i `MaxLevel` ([`0x0020-output.md`](0x0020-output.md) §5.2).

Scena zapisana przed zmianą `MinLevel` może więc dać po przywołaniu wartość inną niż
zapamiętana. Jest to zachowanie zamierzone: `MinLevel` istnieje, bo poniżej niego
ściemniacz migocze, a scena nie jest powodem, żeby na to pozwolić.

### 6.8 Czego nie ma: definiowania sceny wprost

Scenę da się **wyłącznie zapamiętać z bieżącego stanu**. Nie ma komendy, która podawałaby
wartości wprost — „ustaw scenę 4 na 30%, 10% i ciepłą biel" bez doprowadzania wyjść do tego
stanu.

Jest to skutek ośmiu bajtów, nie przeoczenie: lista wartości dla kilku wyjść nie mieści się
w ramce. Konfiguracja sceny wygląda więc tak, że hub ustawia wyjścia, a potem je utrwala.
Przesyłanie w segmentach ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §6) już istnieje,
więc komenda definiująca scenę wprost **jest dziś możliwa** — nie ma jej wyłącznie dlatego,
że nikt jej jeszcze nie potrzebował. Będzie rozszerzeniem zgodnym wstecz.

---

## 7. Wzorce użycia

| Zastosowanie | Jak to wygląda |
|---|---|
| „Wychodzę z domu" | grupa `1` = wszystkie światła; `Recall(scena 1)` grupowo do grupy `1` |
| Scena wieczorna w salonie | grupa `5` = salon, obejmuje trzy węzły; `Recall(scena 4)` grupowo, `transition = 2000` |
| Dwie scenerie w jednym module | kanały `1`–`4` w grupie `2`, kanały `5`–`8` w grupie `3`; sceny `(2, 4)` i `(3, 4)` niezależne |
| Scena obejmująca cały węzeł | `Recall(grupa 0, scena 9)` — **adresowo**, bo grupa `0` nie jest adresem (§4.1) |
| Klawisz sceny | dwuklik → hub → `Recall` grupowe; [`0x0010-key-input.md`](0x0010-key-input.md) §6 |
| Zapamiętanie bieżącego stanu | przytrzymanie klawisza → hub → `Store(grupa, scena)` adresowo do każdego węzła grupy |
| Powrót po awarii | `PowerOnBehaviour = RESTORE` na wyjściach; scen się do tego nie używa |

Ostatni wiersz jest wart uwagi: **scena nie służy do odtwarzania stanu po zaniku zasilania.**
Do tego jest `PowerOnBehaviour`, bo działa bez huba i bez magistrali. Scena wymaga, żeby
ktoś ją przywołał.

---

## 8. Reprezentacja poza magistralą

System nadrzędny widzi scenę jako **parę liczb i nic więcej** — węzeł nie zna jej nazwy ani
tego, co zawiera. Nazwy scen mieszkają w bazie huba, tak jak nazwy urządzeń
([`02-typy-danych.md`](../02-typy-danych.md) §2.2).

Kluczem nazwy jest para `(grupa, numer)` **na poziomie instalacji**, a nie na poziomie
węzła: scena `(5, 4)` to „wieczór w salonie" niezależnie od tego, ile modułów bierze w niej
udział. Tym różni się od nazw urządzeń, które klucza się po `Uid`.

Zalecenie niezależne od adaptera: **hub powinien znać zawartość każdej sceny**, choćby
dlatego, że sam ją zapisywał. Odczytanie sceny z węzła nie jest możliwe — nie ma komendy,
która by to robiła, i nie będzie, bo zawartość sceny nie mieści się w ośmiu bajtach.
Węzeł umie ją odtworzyć, ale nie umie o niej opowiedzieć.
