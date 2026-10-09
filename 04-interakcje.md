# 04 · Interakcje

> **Stabilne.** Sześć rodzajów interakcji; komenda i zapytanie są transakcjami.

Wszystko, co dzieje się na magistrali, jest jednym z **sześciu** rodzajów interakcji.

| Rodzaj | Kierunek | Adres w ramce | Potwierdzana |
|---|---|---|---|
| **Odczyt** | hub → węzeł | **odbiorca** | tak — odpowiedzią z wartością |
| **Zapis** | hub → węzeł | **odbiorca** | tak — odpowiedzią z wynikiem |
| **Komenda** | hub → węzeł albo grupa | **odbiorca** | adresowana tak, grupowa nie |
| **Raport** | węzeł → magistrala | **nadawca** | nie |
| **Zdarzenie** | węzeł → magistrala | **nadawca** | nie |
| **Zapytanie** | węzeł → hub | **nadawca** | tak — odpowiedzią z wartością albo powodem |

Podział przebiega wzdłuż granicy z modelu danych: pierwsze trzy zaczyna **hub**, trzy
ostatnie **węzeł**. Raport i zdarzenie są przy tym wypowiedziami, których nikt nie
zamawiał; zapytanie jest pytaniem i **jako jedyne z tej trójki oczekuje odpowiedzi**.

**Węzeł nigdy nie odczytuje ani nie zapisuje niczego u innego węzła** i nigdy nie kieruje
niczego pod cudzy adres ([`00-wprowadzenie.md`](00-wprowadzenie.md) § Kierunek ruchu).
Zapytanie tego nie narusza: idzie do huba, tak jak raport i zdarzenie, i niesie adres
nadawcy.

> **Przez trzy rewizje stało tu, że rodzajów jest pięć i szóstego nie będzie.** Było to
> zdanie na wyrost — nie wynikało z żadnej granicy modelu, tylko z tego, że pięć
> wystarczało. Zapytanie jest szóstym i jedynym, które **węzeł inicjuje**, zamiast tylko
> odpowiadać.

---

## 1. Ramka niesie jeden adres

Na magistrali CAN **każdą ramkę odbierają fizycznie wszystkie węzły**. Pole adresu nie
doręcza niczego — jest wyłącznie podpowiedzią, kto ma się daną ramką zainteresować.
Podział na „adresowane" i „rozgłoszeniowe" jest więc umowny, a nie fizyczny.

Skoro tak, to w ramce wystarczy **jeden adres węzła**, a rodzaj wiadomości mówi, czym on
jest:

```
ZDARZENIE   rodzaj │ NADAWCA  0x02A │ endpoint 7 │ zdarzenie 0x03
KOMENDA     rodzaj │ ODBIORCA 0x040 │ endpoint 1 │ komenda   0x02
```

Drugiej strony nie zapisujemy, bo zawsze jest nią hub: zdarzenia i raporty płyną do niego,
komendy i odczyty pochodzą od niego. Wpisywanie `0xFE` do każdej ramki byłoby powtarzaniem
tego, co i tak wiadomo z rodzaju wiadomości.

### 1.1 Dlaczego to jest ważne

**Jedenaście zaoszczędzonych bitów.** Identyfikator ramki CAN ma ich 29, a same pola
rodzaju, adresu, endpointu i elementu zajmują dokładnie tyle. Drugi adres by się nie
zmieścił — część pól musiałaby zjechać do ośmiobajtowego ładunku, zabierając miejsce
danym. Zaoszczędzone bity poszły na rozszerzenie adresu z 8 do 11
([`05-mapowanie-can.md`](05-mapowanie-can.md) §1.2).

**Adres nadawcy jest tym, czego hub potrzebuje.** Dopasowanie powiązania odbywa się po
trójce „węzeł, endpoint, zdarzenie" — a wszystkie trzy są w identyfikatorze ramki, więc
hub rozpoznaje je bez zaglądania do ładunku. To samo widać wprost w podglądzie
magistrali.

**Znika pytanie „rozgłoszenie czy adresowanie".** Zdarzenie mówi po prostu *co się stało
u kogo*; kto z tego korzysta, jest sprawą słuchacza, a nie nadawcy.

---

## 2. Transakcje

Odczyt, zapis i komenda adresowana są **transakcjami**: żądanie i odpowiedź tworzą parę.

Każde żądanie niesie **identyfikator transakcji** (`Tid`). Odpowiedź powtarza ten sam
`Tid`, dzięki czemu nadawca kojarzy ją z właściwym żądaniem, nawet gdy odpowiedzi
przyjdą w innej kolejności niż pytania.

`Tid` liczy się **osobno dla każdego klucza**: węzła, endpointu i elementu (atrybutu albo
komendy) — tego samego, którym węzeł rozpoznaje powtórzenie (§2.2). Odpowiedź niesie
endpoint i element w identyfikatorze ramki, więc nadawca kojarzy ją po kluczu razem
z `Tid`, a dwa żądania do różnych elementów nie mogą się pomylić, choćby miały ten sam numer.

W obrębie klucza `Tid` musi być **niepowtarzalny wśród żądań nierozstrzygniętych**
i dodatkowo **nie wolno go użyć ponownie, dopóki nie minie okno deduplikacji** (§2.2).
Poza tym może się dowolnie zawijać; nie jest licznikiem globalnym ani znacznikiem czasu.

Ma **trzy bity**, czyli osiem transakcji nierozstrzygniętych naraz wobec jednego elementu;
w praktyce jest jedna. Jedzie w pierwszym bajcie ładunku, nie w identyfikatorze ramki,
i w odpowiedzi dzieli ten bajt z kodem wyniku
([`05-mapowanie-can.md`](05-mapowanie-can.md) §5.1).

### 2.1 Powtórzenia

Nadawca, który nie otrzyma odpowiedzi w **100 ms**, powtarza żądanie z **tym samym `Tid`**.
Łącznie wykonuje najwyżej **trzy próby**, po czym uznaje węzeł za nieodpowiadający.

Powtórzenie z tym samym `Tid` jest tu istotne — patrz §2.2.

### 2.2 Powtórzenie nie może wykonać akcji dwa razy

Odczyt i zapis można powtarzać bez obaw: odczyt niczego nie zmienia, a zapis tej samej
wartości drugi raz daje ten sam skutek.

**Komendy tej własności nie mają.** `Toggle` wykonane dwa razy wraca do punktu wyjścia,
a `Step` przesuwa poziom podwójnie. Zgubiona odpowiedź na komendę jest więc groźniejsza
niż zgubiona komenda.

Dlatego węzeł zapamiętuje **wynik ostatnio wykonanych komend przez 300 ms**. Komenda
o tym samym kluczu, którą już wykonał, **nie jest wykonywana ponownie** — węzeł odsyła
zapamiętaną odpowiedź.

> **Kluczem deduplikacji jest `Tid` **razem z** endpointem i numerem komendy.**
> **Oknem jest 300 ms**, czyli dokładnie budżet trzech prób po 100 ms (§2.1).

Oba te doprecyzowania są konieczne, a nie kosmetyczne. Sam `Tid` ma trzy bity, czyli osiem
wartości — przy dłuższym oknie **poprawna kolejna komenda trafiłaby w numer, który węzeł
jeszcze pamięta**, i zostałaby po cichu połknięta.

Nie jest to przypadek teoretyczny. Ściemnianie przytrzymaniem klawisza wysyła `Step` co
`HoldTickInterval` ([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §5.6) — przy domyślnych
200 ms to dziesięć komend na dwie sekundy. Przy oknie dwusekundowym dziewiąta kolidowałaby
z pierwszą i **ściemnianie zatrzymałoby się po 1,6 sekundy**, zwracając hubowi stary wynik
zamiast wykonać krok.

Rachunek po poprawce wygląda tak:

| | |
|---|---|
| Okno deduplikacji | 300 ms |
| Ile `Tid` do dyspozycji na klucz | 8 |
| Najszybsze udokumentowane użycie | `Step` co 50 ms → **6 komend w oknie** |
| Zapas | 2 numery |

Okno musi przy tym pokryć wszystkie powtórzenia: druga próba przychodzi 100 ms po
pierwszej, trzecia 200 ms. 300 ms obejmuje je z zapasem, a każda milisekunda ponad to
zabiera zapas po stronie `Tid` i niczego nie chroni.

Ponieważ klucz niesie endpoint i numer komendy, **budżet ośmiu `Tid` nie jest dzielony
w obrębie węzła**: osiem komend do ośmiu różnych endpointów nie koliduje ze sobą, choćby
poszły w pięć milisekund. Ograniczenie dotyczy wyłącznie powtarzania tego samego:

> **Tej samej komendy do tego samego endpointu nie wolno wysyłać częściej niż osiem razy
> na 300 ms.**

Limit zapisany jest wprost, bo inaczej wynikałby z arytmetyki rozsianej po trzech
rozdziałach i ktoś złamałby go, nie zauważając. Dotyczy to zwłaszcza dwóch rzeczy:
`HoldTickInterval` poniżej 37 ms ([`types/0x0010-key-input.md`](types/0x0010-key-input.md) §2.2 dopuszcza
minimum 50 ms, więc mieści się z zapasem) i każdego przyszłego typu regulacji, który
powtarzałby komendę częściej.

Bufor musi pomieścić **każdą komendę wykonaną w ostatnich 300 ms**. Wpis wyrzucony, gdy
komenda wciąż mieści się w oknie, oznacza, że jej powtórzenie wykona się drugi raz — czyli
zdarzy się dokładnie to, przed czym broni cały ten mechanizm.

Liczby wartości `Tid` nie da się tu użyć jako górnej granicy. Skoro budżet `Tid` nie jest
dzielony w obrębie węzła, w oknie może przyjść do jednego węzła więcej niż osiem różnych
komend: moduł ośmiu wyjść, któremu klawisz wyłącza wszystkie kanały, dostaje osiem komend
naraz, a drugi klawisz naciśnięty zaraz potem — kolejne.

> **Bufor ma co najmniej osiem wpisów**; rozsądnie — **dwa na każdy endpoint przyjmujący
> komendy**, czyli dwie pełne serie „wszystko naraz" w jednym oknie.

Jest to jedyne miejsce w całej specyfikacji, w którym węzeł ma obowiązek pamiętać cokolwiek
o przeszłości. Wpis to `Tid`, endpoint, numer komendy i chwila wykonania — kilka bajtów,
więc nawet szesnaście wpisów kosztuje najmniejszy węzeł pomijalnie mało.

---

## 3. Odczyt

```
hub   → węzeł   ODCZYT     Tid, endpoint, atrybut
węzeł → hub     ODPOWIEDŹ  Tid, wynik, [wartość]
```

Jedno żądanie odczytuje **jeden atrybut**. Odczytu zbiorczego nie ma — nie mieści się
w ośmiu bajtach bez komplikowania formatu, a jedyny przypadek, w którym miałby znaczenie,
to jednorazowe rozpoznanie urządzenia przy pierwszym uruchomieniu.

Odczyt atrybutu zapisywalnego tylko (`WO`) kończy się `WRITE_ONLY`. Odczyt atrybutu
należącego do niezadeklarowanej cechy — `UNSUPPORTED_FEATURE`.

Wartość dłuższa niż ładunek odpowiedzi przychodzi **w segmentach**: odpowiedź
niesie wtedy kod `SEGMENTED` zamiast wartości, a segmenty idą zaraz po niej
([`05-mapowanie-can.md`](05-mapowanie-can.md) §6). Dla huba jest to nadal jeden odczyt —
zmienia się tylko liczba ramek, którymi przyjeżdża wynik.

Wartość „brak" jest **poprawnym wynikiem odczytu**, nie błędem
([`02-typy-danych.md`](02-typy-danych.md) §2.1). Czujnik, który jeszcze nic nie zmierzył,
odpowiada `OK` i wartością „brak" — a nie odmową.

---

## 4. Zapis

```
hub   → węzeł   ZAPIS      Tid, endpoint, atrybut, wartość
węzeł → hub     ODPOWIEDŹ  Tid, wynik
```

Węzeł sprawdza kolejno: czy endpoint istnieje, czy atrybut należy do jego typu, czy
cecha jest zadeklarowana, czy atrybut jest zapisywalny, czy długość wartości zgadza się
z typem, czy wartość mieści się w zakresie. Pierwsza niezgodność kończy zapis
odpowiednim kodem i **nie zmienia niczego**.

Zapis jest **niepodzielny**: albo zmienia atrybut w całości, albo nie zmienia go wcale.

Wartość, która nie mieści się w ramce, jedzie **w segmentach** i wtedy ramka
`ZAPIS` w ogóle nie występuje — segmenty same niosą adres, endpoint i element, a węzeł
odpowiada dopiero po ostatnim z nich ([`05-mapowanie-can.md`](05-mapowanie-can.md) §6).
Niepodzielność obowiązuje tak samo: wartość porzucona w połowie nie zmienia niczego.

### 4.1 Trwałość

Atrybuty oznaczone jako trwałe (`P`) trafiają do pamięci nieulotnej **przed wysłaniem
odpowiedzi**. Odpowiedź `OK` znaczy więc „zapisane na stałe", a nie „przyjęte do wiadomości".

Niepowodzenie zapisu do pamięci kończy się kodem `FAILURE`. Węzeł, który nie potrafi
zapamiętać ustawienia, ma o tym powiedzieć od razu — a nie zapomnieć je po najbliższym
zaniku zasilania.

### 4.2 Zapis wywołuje raport

Zapis atrybutu raportowanego powoduje **normalny raport**, oprócz odpowiedzi na zapis.
Hub dostaje więc dwie wiadomości i jest to zamierzone: odpowiedź potwierdza transakcję,
a raport informuje **wszystkich** o nowym stanie.

---

## 5. Komenda

```
hub   → węzeł   KOMENDA    Tid, endpoint, komenda, [argumenty]
węzeł → hub     ODPOWIEDŹ  Tid, wynik, [dane]
```

Komenda wywołuje akcję. Jej **skutek** widać w raportach atrybutów, które zmieniła;
odpowiedź mówi jedynie, czy została przyjęta i wykonana.

Rozróżnienie jest praktyczne: odpowiedź `OK` na `Toggle` znaczy „przekaźnik dostał
polecenie i je wykonał", a dopiero raport `OnOff` mówi, w jakim stanie faktycznie jest.
Przy sprawnym urządzeniu to jedno i to samo — przy zaciętym styku właśnie tam widać różnicę.

Komenda wykonuje się **w całości albo wcale**. Komenda długotrwała — jak przejście
jasności rozłożone na dwie sekundy — jest przyjęta i potwierdzona natychmiast; potwierdzenie
oznacza „zacząłem", a nie „skończyłem".

### 5.1 Komenda grupowa

```
hub → grupa     KOMENDA    endpoint, komenda, [argumenty]
                (bez Tid, bez odpowiedzi)
```

Komenda skierowana do grupy **nie ma `Tid` ani odpowiedzi** — trzydzieści potwierdzeń
zajęłoby magistralę na dłużej niż trzydzieści osobnych komend, więc mechanizm zjadłby
własny powód istnienia ([`03-adresacja.md`](03-adresacja.md) §3.2).

### 5.2 Pole endpointu w komendzie grupowej

Numer endpointu w komendzie grupowej **nie jest ignorowany** i rozstrzyga, kto ma ją
wykonać:

| `ENDPOINT` | Znaczenie |
|---|---|
| `0` | **rozdziel** — wykonuje każdy endpoint węzła należący do tej grupy, wedle własnego typu |
| `1`–`63` | wykonuje **ten** endpoint, o ile do grupy należy którykolwiek endpoint węzła |

Bez tego rozróżnienia komenda grupowa jest **niejednoznaczna**, bo numery komend powtarzają
się między typami. `Output` ma `Off = 0x00` i `On = 0x01`, a `Scenes` — `Store = 0x00`
i `Recall = 0x01`. Ramka „element `0x00` do grupy 5" znaczyłaby więc jednocześnie „zgaś
salon" i „zapamiętaj bieżący stan jako scenę", a te dwie rzeczy nie mają ze sobą nic
wspólnego i jedna z nich nadpisuje dane.

Wartość `0` jest bezpiecznym sentinelem, bo endpoint `0` ma typ
[`Device`](types/0x0001-device.md), który nie przyjmuje komend grupowych — nie traci się
więc żadnej możliwości.

Skutek widać w raportach stanu, które i tak przyjdą. Hub, któremu zależy na pewności,
używa komend adresowanych.

---

## 6. Raport

```
węzeł → magistrala   RAPORT   endpoint, atrybut, wartość
```

Raport niesie **adres nadawcy** i nie wskazuje odbiorcy — mówi „u mnie jest tak",
a nie „tobie mówię, że jest tak". W tej wersji słucha go tylko hub.

Raport jest **niezamawiany i niepotwierdzany**. Węzeł wysyła go, gdy zmienił się stan,
gdy upłynął okres odświeżania albo w odpowiedzi na odczyt — reguły opisuje
[`01-model-danych.md`](01-model-danych.md) §6.

Raport **nie ma numeru kolejnego**. Stan jest wartością bieżącą, więc zgubienie raportu
niczego nie psuje: następny przyniesie wartość aktualną, a nie zaległą. Właśnie po to
istnieje odświeżanie cykliczne.

Raport nie wskazuje odbiorcy, bo nie ma czego wskazywać: hub jest jeden i to on słucha.
Gdyby kiedyś słuchał ktoś jeszcze — rejestrator, narzędzie diagnostyczne, drugi hub —
nie wymaga to zmiany ani jednego bitu.

---

## 7. Zdarzenie

```
węzeł → magistrala   ZDARZENIE   endpoint, zdarzenie, licznik, [parametry]
```

Zdarzenie jest **niezamawiane i niepotwierdzane**, jak raport, ale różni się od niego
w sposób istotny: opisuje **fakt**, który zaszedł w określonej chwili i nie ma wartości
bieżącej.

Dlatego zdarzenie niesie **licznik kolejny** — ośmiobitowy, osobny dla każdego endpointu,
zawijający się z `255` na `0`. Odbiorca, który zauważy dziurę w numeracji, wie, że coś
przepadło.

### 7.1 Zgubione zdarzenie nie jest powtarzane

Węzeł **nie retransmituje** zdarzeń i nie oczekuje potwierdzenia. Odbiorca, który wykrył
dziurę, **odnotowuje ubytek i obsługuje zdarzenie bieżące** — nie żąda powtórki.

Jest to decyzja, nie niedopatrzenie. Zapalenie światła pół minuty po naciśnięciu klawisza
jest gorsze niż niezapalenie go wcale: użytkownik dawno nacisnął drugi raz, a spóźniona
reakcja zgasi to, co właśnie zapalił.

Ta sama zasada dotyczy huba, który wrócił po restarcie. Nadrabianie zaległych zdarzeń
jest zabronione — historię można zapisać, ale nie wolno na jej podstawie działać.

### 7.2 Priorytet

Zdarzenia mają na magistrali **pierwszeństwo przed raportami**. Raport spóźniony o sekundę
nadal niesie prawdę, zdarzenie spóźnione o sekundę już nie.

Sposób realizacji pierwszeństwa należy do rozdziału o mapowaniu na CAN.

---

## 8. Zapytanie

```
węzeł → hub   ZAPYTANIE        Tid, endpoint, element
hub → węzeł   ODPOWIEDŹ_HUBA   Tid, wynik, [wartość]
```

Węzeł pyta hub o **wartość jednego ze swoich atrybutów wejściowych**. Nie pyta o cudzy stan
i nie wskazuje źródła — mówi „potrzebuję wartości tutaj", a hub odpowiada danymi albo
powodem, dla którego ich nie ma.

Termostat z własną pętlą regulacji potrzebuje temperatury zewnętrznej, której sam nie
mierzy. Ma na nią zapisywalny atrybut; zapytanie jest sposobem, by powiedzieć, **kiedy**
tej wartości potrzebuje.

### 8.1 Jest to transakcja jak każda inna

`Tid`, sto milisekund, trzy próby — obowiązują **niezmienione** reguły z §2. Zapytanie nie
dokłada ani jednej własnej: nie ma osobnego odliczania, osobnego backoffu ani osobnego
sposobu wykrywania, że coś przepadło.

Dzięki temu węzeł, któremu się nie udało, **wie dlaczego**:

| Wynik | Znaczy |
|---|---|
| `OK` | wartość w ładunku |
| `UNAVAILABLE` | hub nie ma tej wartości — brak źródła albo źródło milczy |
| `BUSY` | hub chwilowo nie może odpowiedzieć; **warto powtórzyć** |
| cisza po trzech próbach | hub nie odpowiada w ogóle |

Rozróżnienie „nie mam" od „nie odpowiadam" jest tu całym zyskiem. Węzeł może zapisać jedno
w diagnostyce, a na drugie zareagować inaczej — czego przy wiadomości niepotwierdzanej
zrobić się nie da, bo cisza znaczy wszystko naraz.

> **Węzeł jest tu po raz pierwszy stroną inicjującą transakcję.** Dotąd wyłącznie
> odpowiadał. Firmware, które chce zapytań, musi umieć prowadzić własny `Tid` i własne
> odliczanie — jest to realny koszt i dlatego zapytanie jest opcjonalne (§8.8).

### 8.2 Hub odpowiada ze swojego modelu

> **Hub odpowiada natychmiast tym, co ma u siebie.** Nie wolno mu przetrzymywać odpowiedzi,
> czekając na dane z zewnątrz.

Powód jest arytmetyczny: transakcja ma sto milisekund i trzy próby, czyli **trzysta
milisekund łącznie**. Odpytanie systemu nadrzędnego przez sieć w to się nie mieści i nie
ma sensu próbować.

Gdy hub wartości nie ma, odpowiada `UNAVAILABLE` **i dopiero wtedy sięga po nią w tle**.
Kolejne zapytanie dostanie już dane. Zapytanie jest więc sygnałem popytu, który utrzymuje
obraz huba świeży — a nie przelotem na zewnątrz instalacji.

Rozwiązuje to zarazem problem, który przesądził o tym mechanizmie: hub nie musi odpytywać
źródeł bez przerwy, żeby mieć czym odpowiadać. Odpytuje te, o które ktoś pyta.

### 8.3 Węzeł musi działać bez odpowiedzi

> **Zapytanie jest doradcze, nie jest warunkiem pracy.** Węzeł, który dostaje wyłącznie
> `UNAVAILABLE`, ma działać dalej.

Atrybut, którego nikt nie wypełnił, ma wartość **„brak"**
([`02-typy-danych.md`](02-typy-danych.md) §2.1) — i to jest stan, który typ musi umieć
obsłużyć, opisując wprost, co wtedy robi. Termostat bez temperatury zewnętrznej reguluje
gorzej, ale reguluje; nie wolno mu czekać na starcie ani przestać działać.

Reguła jest ostra, bo cena pomyłki jest wysoka: urządzenie, które blokuje się w oczekiwaniu
na dane, psuje się w sposób trudny do zdiagnozowania — wygląda jak martwe, a jest sprawne.

### 8.4 Węzeł nie wie, skąd wartość pochodzi

I nie ma prawa się tym interesować. Hub może wziąć ją z innego węzła, z własnego czujnika
albo **spoza instalacji** — z systemu nadrzędnego, do którego sam jest podłączony
([`00-wprowadzenie.md`](00-wprowadzenie.md) § Hub).

Powiązanie „ten atrybut ← to źródło" jest konfiguracją huba, nie protokołu. Węzeł zna
wyłącznie własny atrybut i to, czy hub ma czym go wypełnić.

### 8.5 Typ deklaruje swoje wejścia

Nie każdy atrybut wolno odpytywać. **Typ, który ma wejścia, wymienia je w tabeli** —
dokładnie tak, jak wymienia swoje cechy:

```
Wejścia typu Thermostat

  Bit  Atrybut                Czym jest
   0   OutdoorTemperature     temperatura zewnętrzna
   1   SetpointOverride       nastawa narzucona z zewnątrz
  2–15 — zarezerwowane, nadawaj 0
```

Wejście to atrybut **zapisywalny, ulotny, który wypełnia hub**, a węzeł sam go nie zmierzy.
Atrybut, którego w tej tabeli nie ma, nie podlega zapytaniom — zapytanie o niego kończy się
`UNSUPPORTED_ELEMENT`.

### 8.6 Hub włącza wejścia pojedynczo

Atrybut wspólny **`0xF6 QueryEnabled`** (`map16`, `RW`, trwały, domyślnie `0`) niesie
**bit na każde wejście** — numery bitów są te z tabeli typu.

Hub zapala te wejścia, które umie obsłużyć, i gasi te, których nie umie. Endpoint z dwoma
wejściami, dla którego hub ma źródło tylko jednego, dostaje `QueryEnabled = 0b01`:

```
QueryEnabled = 0x0001    bit 0 zapalony  → wolno pytać o OutdoorTemperature
                         bit 1 zgaszony  → o SetpointOverride nie wolno
```

Węzeł **nie pyta o wejście, którego bit jest zgaszony**. Nie traci więc zapytań na coś,
czego i tak nikt mu nie da, i nie musi tego odkrywać metodą prób.

> **Przy `QueryEnabled = 0` węzeł nie wysyła zapytań w ogóle.** Wartość domyślna jest zerem,
> więc urządzenie świeżo przyłączone milczy, dopóki hub go nie dopuści.

Konfiguracja jest więc **per wejście**, choć mieści się w jednym atrybucie na endpoint.
Ten sam wzorzec co przy `Features`: bitmapa wspólna, znaczenie bitów od typu.

`QueryEnabled` i `UNAVAILABLE` odpowiadają na **dwa różne pytania** i żadne nie zastępuje
drugiego:

| | Odpowiada na | Zmienność |
|---|---|---|
| `QueryEnabled` | o **które wejścia wolno mi pytać** | statyczna, sterowana przez hub |
| `UNAVAILABLE` | czy **ta wartość jest teraz** | dynamiczna, per zapytanie |

Bez flagi węzeł nie wiedziałby ani czy może pytać, ani **kiedy będzie mógł** — zostawałoby
mu odpytywanie w ciemno w nieskończoność, bo nic nie mówi mu, że sytuacja się zmieniła.
Zapis flagi jest tym brakującym sygnałem: hub włącza pytanie w chwili, gdy ma czym
odpowiadać.

Flaga bywa nieaktualna — zostaje w węźle, gdy hub straci konfigurację. Nie szkodzi to
niczemu: węzeł zapyta, dostanie `UNAVAILABLE` i zachowa się dokładnie tak, jak bez flagi.
Najgorszy przypadek jest więc równy stanowi, który flaga zastąpiła.

> **`QueryEnabled` jest konfiguracją, nie sygnałem dostępności.** Hub zapisuje ją przy
> **zmianie mapowania wejścia** — gdy przypisuje źródło albo je odbiera — i odtwarza po
> enumeracji, jeśli jego obraz się z węzłem rozjechał. **Nie wolno jej przepisywać przy
> każdej zmianie dostępności źródła**: od tego jest `UNAVAILABLE`, a flaga jest atrybutem
> trwałym i jej przepisywanie zużywa pamięć nieulotną węzła.

Rozróżnienie to jest praktyczne: źródło potrafi zamilknąć na godzinę i wrócić, a mapowanie
zmienia się raz przy konfiguracji instalacji.

### 8.7 Jak często wolno pytać

Przy zapalonym bicie węzeł pyta, kiedy potrzebuje — ale **nie częściej niż raz na
10 sekund dla jednego atrybutu**.

Odstęp jest potrzebny mimo flagi, bo `UNAVAILABLE` może się utrzymywać długo: hub ma prawo
pytać, ale źródło milczy. Bez ograniczenia węzeł odpytywałby w kółko coś, czego przez
godzinę nie będzie.

### 8.8 Zapytanie jest opcjonalne

**Żaden węzeł nie musi go umieć.** Typ, który ma atrybuty wejściowe, może polegać wyłącznie
na tym, że hub wypełni je zwykłym `ZAPIS`em z własnej inicjatywy — i jest to implementacja
w pełni zgodna.

Zapytanie jest narzędziem dla węzła, który **wie, kiedy potrzebuje danych, lepiej niż hub**.
Jeśli nie wie, nie ma po co go wysyłać — a oszczędza sobie przy tym roli inicjatora
transakcji (§8.1).

Węzeł, który zapytań nie umie, po prostu ignoruje `QueryEnabled`. Hub, który ustawi flagę
i nie doczeka się żadnego zapytania, nie ma powodu uznawać tego za usterkę.

---

## 9. Kody wyniku

| Kod | Nazwa | Znaczenie |
|---|---|---|
| `0x00` | `OK` | wykonane |
| `0x01` | `UNSUPPORTED_ENDPOINT` | węzeł nie ma takiego endpointu |
| `0x02` | `UNSUPPORTED_ELEMENT` | typ nie zna takiego atrybutu ani komendy |
| `0x03` | `UNSUPPORTED_FEATURE` | element istnieje, ale jego cecha nie jest zadeklarowana |
| `0x04` | `READ_ONLY` | próba zapisu atrybutu tylko do odczytu |
| `0x05` | `WRITE_ONLY` | próba odczytu atrybutu tylko do zapisu |
| `0x06` | `INVALID_VALUE` | zła długość albo wartość poza zakresem |
| `0x07` | `INVALID_STATE` | operacja niemożliwa w bieżącym stanie |
| `0x08` | `BUSY` | węzeł chwilowo nie może obsłużyć żądania |
| `0x09` | `FAILURE` | usterka sprzętu albo pamięci |
| `0x0A` | `INSUFFICIENT_SPACE` | brak miejsca w tablicy o ograniczonej pojemności |
| `0x0C` | `UNAVAILABLE` | hub nie ma tej wartości — brak źródła albo źródło milczy |
| `0x0B` | `SEGMENTED` | wartość nie mieści się w ramce — nadchodzi w segmentach |

Rozróżnienie `UNSUPPORTED_ELEMENT` i `UNSUPPORTED_FEATURE` ma konkretny sens
diagnostyczny. Pierwsze znaczy „pomyliłeś typ” i jest błędem huba. Drugie znaczy
„to urządzenie po prostu tego nie ma" i jest normalną odpowiedzią — ściemniacz bez cechy
`COLOR_RGB` odmawia zapisu barwy, choć atrybut istnieje w typie
([`types/0x0020-output.md`](types/0x0020-output.md) §1).

`INSUFFICIENT_SPACE` dotyczy struktur, których pojemność jest skończona i ogłoszona
w atrybucie — dziś wyłącznie tablicy scen
([`types/0x0003-scenes.md`](types/0x0003-scenes.md) §4.2). Różni się od `FAILURE` tym, że
nie jest usterką: węzeł działa poprawnie i mówi, że nie ma gdzie tego zapisać.

`SEGMENTED` **nie jest błędem** — jest zapowiedzią. Znaczy „żądanie przyjęte, wartość jest
za długa na jedną ramkę, nadchodzi segmentami"
([`05-mapowanie-can.md`](05-mapowanie-can.md) §6). Wartość, która się mieści, przychodzi
jak dotąd w tej samej odpowiedzi; kod pojawia się wyłącznie tam, gdzie nie ma innego wyjścia.

`BUSY` jest jedynym kodem, po którym **warto powtórzyć żądanie**. Pozostałe błędy
powtórzone dadzą ten sam wynik.

---

## 10. Kolejność i równoczesność

**Węzeł obsługuje żądania w kolejności odbioru.** Nie zmienia ich kolejności ani nie
łączy w grupy. Dwie komendy sprzeczne wykonają się obie, jedna po drugiej — wygrywa
późniejsza, bo taka była kolejność na magistrali.

Węzeł musi obsłużyć **co najmniej jedno żądanie naraz**. Obsługa większej ich liczby
jednocześnie jest dozwolona, ale nie wymagana; węzeł zajęty odpowiada `BUSY`.

**Raporty i zdarzenia z jednego endpointu zachowują kolejność** względem siebie.
Między różnymi endpointami — nawet tego samego węzła — kolejność nie jest gwarantowana.

Odpowiedzi mogą przyjść w innej kolejności niż żądania. Od tego jest `Tid`.

---

## 11. Podsumowanie

| | Odczyt | Zapis | Komenda | Kom. grupowa | Raport | Zdarzenie | Zapytanie |
|---|---|---|---|---|---|---|---|
| Inicjuje | hub | hub | hub | hub | węzeł | węzeł | węzeł |
| Adres w ramce | odbiorca | odbiorca | odbiorca | grupa | nadawca | nadawca | nadawca |
| `Tid` | tak | tak | tak | nie | nie | nie | **tak** |
| Odpowiedź | tak | tak | tak | nie | nie | nie | **tak** |
| Powtarzalna | zawsze | zawsze | przez `Tid` | nie | — | — | zawsze |
| Numer kolejny | nie | nie | nie | nie | nie | **tak** | nie |
| Zgubienie boli | nie | nie | nie | trochę | nie | **tak** | nie |
