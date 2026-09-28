# 07 · Hub

> **Szkic.** Model powiązań i obowiązki huba są ustalone. Adapter północny pozostaje poza
> zakresem tej specyfikacji.

Sześć poprzednich rozdziałów opisuje, co robi **węzeł**. Ten opisuje drugą stronę: co hub
musi robić, żeby instalacja działała tak, jak obiecuje
[`00-wprowadzenie.md`](00-wprowadzenie.md).

Rozdział jest **normatywny dla tego, co hub kładzie na magistralę**, i doradczy dla tego,
jak organizuje się w środku. Baza, język i architektura huba to jego sprawa; ramki i czasy
są sprawą wspólną.

---

## 1. Co hub musi umieć

| Obowiązek | Opisuje |
|---|---|
| Nadawać i pilnować adresów | [`03-adresacja.md`](03-adresacja.md) §5, [`06`](06-cykl-zycia-urzadzenia.md) §2 |
| Prowadzić model instalacji | §2 |
| Wykonywać powiązania | §3–§6 |
| Wykrywać nieobecność węzłów | [`06`](06-cykl-zycia-urzadzenia.md) §5 |
| Wystawiać instalację na zewnątrz | poza zakresem |

**Czego nie musi:** harmonogramów, warunków, pory dnia, trybów domu. To jest zadanie
systemu nadrzędnego i powtarzanie go byłoby budowaniem gorszej wersji czegoś, co istnieje
([`00-wprowadzenie.md`](00-wprowadzenie.md) § Czego ten system nie robi).

---

## 2. Model instalacji

Hub przechowuje dla każdego węzła, **kluczując po `Uid`**:

```
Uid  →  adres bieżący           z przyłączania, zmienny
        model                    endpointy, typy, rewizje, cechy, kanały
        nazwy                    nadane przez człowieka
        powiązania               §3
        zawartość scen           bo węzeł nie umie jej odczytać
        QueryEnabled             które wejścia hub obsługuje
```

> **Wszystko, co hub zapisuje o urządzeniu, jest kluczowane `Uid`, nigdy adresem.**

Adres jest drogą, nie tożsamością ([`03-adresacja.md`](03-adresacja.md) §2.2). Konfiguracja
zapisana „na adres `0x2A`" rozsypuje się przy pierwszym przenumerowaniu, a zapisana na `Uid`
przeżywa wszystko poza wymianą sprzętu na nowy egzemplarz.

Odwzorowanie `Uid → adres` jest jedynym miejscem, w którym adres występuje — i jedynym,
które trzeba odbudować po przeadresowaniu.

---

## 3. Powiązanie

Powiązanie mówi: **gdy zdarzy się to, zrób tamto.**

```
ŹRÓDŁO                                   CEL
(Uid, endpoint, element)        →        (Uid, endpoint, komenda, argumenty)
```

Obie strony kluczowane `Uid`. Hub tłumaczy adres na `Uid` przy odbiorze i `Uid` na adres
przy nadawaniu — i jest to jedyne tłumaczenie w całym systemie.

### 3.1 Co może być źródłem

| Źródło | Przykład |
|---|---|
| **Zdarzenie** | `Click` z klawisza, `DemandChanged` z termostatu |
| **Zmiana raportowanego atrybutu** | `Contact.State`, `Output.OnOff` |

Powiązanie na zmianę atrybutu wyzwala się **przy zmianie wartości**, nie przy każdym
raporcie — raport cykliczny niosący tę samą wartość co poprzedni nie jest zdarzeniem
i niczego nie uruchamia. Inaczej odświeżanie cykliczne generowałoby komendy w kółko.

Źródłem **nie może być** komenda ani odpowiedź: te pochodzą od huba i wiązanie ich do
siebie tworzyłoby pętlę z definicji.

#### Gdy typ opisuje to samo dwa razy

Niektóre typy celowo dublują jedną decyzję: emitują zdarzenie **i** raportują atrybut
o tym samym znaczeniu. Wolno im, pod warunkiem rozstrzygnięcia sporu
([`01-model-danych.md`](01-model-danych.md) §3). Dziś robi tak
[`Thermostat`](types/0x0040-thermostat.md): `DemandChanged` i `Running` mówią o tej samej
decyzji regulatora.

> **W takim przypadku hub wiąże zdarzenie, nie raport.**

Powód jest podwójny. Zdarzenie jedzie z priorytetem `0x1`, a raport z `0x8` — czyli po to
zdarzenie w ogóle istnieje. A gdyby hub związał oba, **wysłałby komendę dwa razy** przy
każdej zmianie: raz na zdarzenie, raz na raport, który przyjdzie chwilę później.

Raport zostaje do tego, do czego jest: do odtwarzania obrazu po restarcie i do
rozstrzygania, gdy zdarzenie przepadło.

### 3.2 Co może być celem

| Cel | Kiedy |
|---|---|
| **Komenda adresowana** | gdy zależy nam na potwierdzeniu |
| **Komenda grupowa** | gdy celów jest wiele i mają ruszyć razem |
| **Zapis atrybutu** | gdy celem jest wartość, nie akcja — np. wypełnienie wejścia |

Ostatni wiersz jest tym, co obsługuje zapytania: powiązanie „wejście ← źródło" ma jako cel
zapis, a nie komendę ([`04-interakcje.md`](04-interakcje.md) §8).

### 3.3 Trzy powiązania, które dziś istnieją

```
klawisz       Click                → komenda Toggle na przekaźniku
termostat     DemandChanged(1)     → komenda On na siłowniku
czujnik       Value                → zapis RemoteTemperature w regulatorze
```

Wzorzec jest w każdym ten sam, a hub nie musi ich odróżniać. Silnik powiązań, który obsłuży
pierwszy, obsłuży wszystkie trzy.

---

## 4. Dopasowanie

```
1.  odbierz ramkę
2.  zamień adres nadawcy na Uid
3.  znajdź powiązania o pasującym (Uid, endpoint, element)
4.  dla każdego: zamień Uid celu na adres i nadaj
```

**Brak powiązania nie jest błędem.** Zdarzenie, którego nikt nie słucha, jest normalnym
stanem instalacji — klawisz może po prostu nie być jeszcze skonfigurowany.

Jedno źródło może mieć **wiele celów**. Hub wykonuje je w kolejności konfiguracji, ale gdy
cele mają ruszyć **jednocześnie**, właściwym narzędziem jest komenda grupowa, a nie kilka
adresowanych ([`03-adresacja.md`](03-adresacja.md) §3.1) — kilka komend daje widoczny rozjazd
kilkunastu milisekund.

### 4.1 Skutek powiązania nie wyzwala kolejnego

> **Powiązania nie łączą się w łańcuchy.** Komenda nadana przez hub w skutku powiązania
> **nie jest** źródłem dla żadnego innego powiązania, a raport, który po niej przyjdzie,
> również nie.

Bez tej reguły powstaje pętla, i to trywialnie: wyjście A raportuje zmianę, powiązanie
włącza wyjście B, B raportuje zmianę, powiązanie włącza A. Magistrala zapełnia się
w ułamku sekundy, a instalacja przestaje reagować na cokolwiek.

Reguła jest ostra i świadomie uboga. Łańcuchy dałoby się dopuścić z wykrywaniem cykli, ale
byłby to mechanizm skomplikowany, trudny do zdiagnozowania i **niepotrzebny**: wszystkie
trzy istniejące powiązania mają jeden krok. Logika wymagająca łańcucha należy do systemu
nadrzędnego, który ma na to narzędzia i czas.

### 4.2 Budżet czasu

> **Od odebrania zdarzenia do przekazania komendy magistrali — najwyżej 50 ms.**

| | Czas | Status |
|---|---|---|
| Typowo | **kilka ms** — tyle, ile pokazuje [`00-wprowadzenie.md`](00-wprowadzenie.md) | wynik, nie wymaganie |
| Granica | **50 ms** na hub | wymaganie |

Liczba bierze się z tego, co zauważa człowiek, a nie z tego, co potrafi sprzęt. Zwłokę
reakcji widać gdzieś od stu milisekund, a `Click` przychodzi i tak 80–150 ms po naciśnięciu
([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §5.2). Pięćdziesiąt milisekund
na hub zostawia drugą połowę na magistralę, arbitraż i węzeł wykonawczy. Granica ostrzejsza
zmuszałaby każdą implementację do obrony zapasu, którego nikt nie potrzebuje.

> **Hub nie może kolejkować ani grupować powiązań w czasie.** Nie wolno mu odkładać
> dopasowania do następnego przebiegu pętli, buforować zdarzeń ani czekać na inne.

To zdanie niesie treść niezależnie od liczby. Jest to jedyne miejsce, w którym specyfikacja
stawia hubowi wymaganie czasowe — i stawia je, bo cały projekt istnieje po to, żeby światło
zapalało się natychmiast. Powiązanie przechodzące przez bazę danych z zapytaniem na dysk
**łamie to wymaganie**, choćby zwykle mieściło się w czasie: zwykle to nie zawsze, a karta
SD potrafi zatrzymać zapis na setki milisekund.

---

## 5. Restart huba

Hub po restarcie **nie zna stanu instalacji** i musi go odzyskać. Kolejność jest ustalona,
bo od niej zależy, czy instalacja zachowa się sensownie:

```
1.  wczytaj model i powiązania z własnej bazy        klucz: Uid
2.  nasłuchuj — nie odpytuj                          §5.1
3.  odbuduj Uid → adres z ramek, które przychodzą
4.  po jednym ReportInterval masz pełny obraz stanu
```

### 5.1 Odzyskiwanie przez nasłuchiwanie, nie odpytywanie

Hub **nie odpytuje wszystkich węzłów po starcie**. Czeka jeden okres odświeżania
cyklicznego — i właśnie po to ono istnieje
([`01-model-danych.md`](01-model-danych.md) §6).

Sto węzłów odpytanych naraz to kilkaset transakcji w kilka sekund; ta sama wiedza przychodzi
sama, za darmo, w ciągu minuty. Jedyne, co hub powinien odpytać od razu, to węzły, których
stan jest potrzebny natychmiast do bezpieczeństwa.

### 5.2 Czego nie wolno robić po restarcie

> **Nie wolno odtwarzać zaległych zdarzeń.** Zdarzenia, które padły, gdy hub nie działał,
> przepadły i mają przepaść.

Zapalenie światła pół minuty po naciśnięciu klawisza jest gorsze niż niezapalenie go wcale
([`04-interakcje.md`](04-interakcje.md) §7.1). Historię wolno zapisać; działać na jej
podstawie — nie.

**Nie wolno też zakładać, że wyjścia są w stanie sprzed restartu.** Węzły mogły w tym czasie
zostać przełączone ręcznie, zrestartować się albo zadziałać `AutoOffTime`. Prawdą jest
pierwszy raport, jaki przyjdzie, a nie to, co hub pamięta.

### 5.3 Konfiguracja huba jest źródłem prawdy

Część konfiguracji mieszka fizycznie **w węzłach**: przynależność do grup, `QueryEnabled`,
zawartość scen. Kusi, żeby uznać to za kopię zapasową. **Nie jest nią.**

| Z węzła wraca | Nie wraca |
|---|---|
| `QueryEnabled` — **które** wejścia są włączone | **jakie źródło** było do nich przypisane |
| `GetMembership` — **numery** grup | **co znaczy** grupa `5` |
| — | zawartość scen, w ogóle |

Widać z tego jedną regułę, a nie trzy przypadki: **z węzłów wraca liczba, nigdy znaczenie.**
Hub, który zgubił swoją bazę, odtworzy z instalacji strukturę i nie odtworzy ani jednej
decyzji, którą podjął operator.

Odczyt służy więc **sprawdzeniu zgodności**, a nie odtwarzaniu. Hub przepisuje do węzła to,
co ma u siebie, gdy obraz się rozjedzie — i w tę stronę, nigdy w drugą.

> **Nota implementacyjna.** Hub, który wykryje rozbieżność albo brak własnej konfiguracji,
> powinien **odnotować to jako wymagające uwagi operatora**, a nie zgadywać z tego, co
> znalazł w węzłach. Konfiguracja odtworzona z samych liczb wygląda na kompletną i nie
> jest — grupy bez nazw, wejścia bez źródeł, sceny o nieznanej zawartości. Lepiej pokazać
> człowiekowi listę rzeczy do skonfigurowania od nowa niż instalację, która działa
> pozornie.

Praktyczny wniosek dla wdrożenia: **kopia bazy huba jest kopią całej instalacji**, a kopia
węzłów nie jest niczyją kopią.

---

## 6. Wiele magistral

Hub jest jeden logicznie, choć fizycznie ma kilka interfejsów
([`03-adresacja.md`](03-adresacja.md) §2.4). Wynikają z tego trzy obowiązki:

**Wie, na którym interfejsie widzi dany węzeł** — i jest to jedyne miejsce w systemie, gdzie
ta wiedza istnieje. Węzeł nie zna numeru swojej magistrali i nie ma po co
([`03-adresacja.md`](03-adresacja.md) §7).

**Nie powtarza ramek między magistralami.** Odbiera zdarzenie z jednej magistrali i nadaje
**własną komendę** na drugiej ([`03-adresacja.md`](03-adresacja.md) §4.3).

**Komendę grupową nadaje osobno na każdej magistrali**, na której są członkowie grupy. Grupa
rozciągnięta na trzy magistrale to trzy ramki — ale nadal jedna na magistralę, więc oszczędność
zostaje tam, gdzie ma znaczenie ([`03-adresacja.md`](03-adresacja.md) §3.1).

---

## 7. Poza zakresem

Poza zakresem tego rozdziału i całej specyfikacji pozostaje **adapter północny** — to, na
co hub tłumaczy instalację na zewnątrz. Kandydaci są wymienieni
w [`00-wprowadzenie.md`](00-wprowadzenie.md) § Hub i żaden nie jest wybrany.
