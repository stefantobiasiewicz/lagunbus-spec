# 00 · Wprowadzenie

> **Stabilne.** Zakres, kierunek ruchu i podział warstw rozstrzygnięte.

## Po co to istnieje

Mieszkanie sterowane bezprzewodowo działa dobrze przez większość czasu. Raz na kilka
dni trzeba nacisnąć przycisk dwa razy. To nie jest awaria — to właściwość medium:
transmisja radiowa bywa zagłuszona, a warstwa aplikacyjna nie ma jak odróżnić
„nie usłyszałem" od „nic nie nadano".

W domu, który dopiero powstaje, można to rozwiązać u źródła: **poprowadzić kabel**.

LagunBus to specyfikacja warstwy aplikacyjnej dla takiej instalacji — co urządzenia
sobie mówią, w jakim formacie i z jakimi gwarancjami.

## Zakres

**Obejmuje** urządzenia przewodowe, montowane na stałe i budowane samodzielnie:

- w puszkach podtynkowych: przyciski, panele, czujniki, enkodery,
- na szynie DIN: przekaźniki, ściemniacze, sterowniki rolet, sterowniki LED,
- pomiary: temperatura, wilgotność, światło, jakość powietrza, energia, woda.

**Nie obejmuje** urządzeń, które przychodzą z własnym protokołem: telewizorów,
odkurzaczy, pralek, kamer, głośników. Objęcie ich tą specyfikacją dołożyłoby dwie
trzecie katalogu bez żadnego zysku.

To jest zasadnicza różnica względem Matter, z którego bierzemy model danych: Matter
musi opisać pralkę, bo jest protokołem uniwersalnym. My nie musimy.

---

## Instalacja

Instalacja składa się z **węzłów** połączonych **magistralami**, którymi zarządza
**hub**.

```
                    ┌──────────────────────────┐
                    │           HUB            │
                    │  zarządza magistralami,  │
                    │  adresacją, regułami     │
                    └──┬────────┬────────┬─────┘
                       │        │        │
              magistrala 1   magistrala 2   …
                       │        │
        ┌──────┬───────┤        ├───────┬──────┐
      węzeł  węzeł   węzeł    węzeł   węzeł  węzeł
```

### Magistrala

Magistrala niesie **dwie rzeczy**:

| Szyna | Funkcja |
|---|---|
| **Zasilanie** | zasila węzły; napięcie i wydajność są decyzją wdrożeniową |
| **Dane** | różnicowa para CAN |

Rodzaj kabla, złącza, napięcie zasilania i topologia to **decyzje wdrożeniowe, nie
elementy tej specyfikacji**. Ta sama instalacja może być poprowadzona kablem
sterowniczym, skrętką albo czymkolwiek, co poprowadzi zasilanie i parę różnicową.

Jedna magistrala rzadko obsłuży cały dom — ograniczają ją długość, liczba węzłów
i topologia CAN. Dlatego instalacja składa się z **kilku niezależnych magistral**,
a jedynym punktem, który je zna, jest hub.

### Węzeł

Jedno urządzenie fizyczne na magistrali, o jednym adresie. Wystawia swoje funkcje
jako **endpointy** — opisuje to [`01-model-danych.md`](01-model-danych.md).

### Hub

Urządzenie zarządzające całą instalacją. **Nie jest zwykłym mostkiem** — nie tylko
przekłada ramki, ale prowadzi całą logikę sieci:

- obsługuje wszystkie magistrale naraz i jest jedynym punktem, który je łączy,
- nadaje i pilnuje adresów węzłów,
- zna model każdego urządzenia i jego bieżący stan,
- wykonuje reguły sterowania,
- wystawia instalację na zewnątrz przez **wymienne adaptery**.

Adaptery północne — to, na co hub tłumaczy instalację — **nie są jeszcze ustalone**.
Kandydaci: MQTT, gniazdo TCP, port szeregowy, REST. Specyfikacja LagunBus celowo
o tym milczy: opisuje, co dzieje się na magistrali, a nie co hub robi dalej.

Rolą hub przypomina koordynator Zigbee wraz z `zigbee2mqtt` — z tą różnicą, że tutaj
jedno urządzenie robi obie te rzeczy i obsługuje kilka magistral.

---

## Kierunek ruchu

> **Węzeł rozmawia wyłącznie z hubem. Urządzenia nie rozmawiają ze sobą.**

Naciśnięcie klawisza wysyła zdarzenie do huba; hub sprawdza swoje powiązania
([`07-hub.md`](07-hub.md) §3) i wysyła
komendę do modułu wykonawczego.

Nie jest to uproszczenie na start, tylko rozstrzygnięcie. Instalacja składa się z kilku
magistral, a **ramka nie opuszcza tej, na której powstała** — jedynym urządzeniem
widzącym całość jest hub. Dopuszczenie rozmów między węzłami dałoby mechanizm działający
tylko w obrębie jednej linii, wymagający tablicy reguł w każdym mikrokontrolerze i drugiej
ścieżki sterowania, którą trzeba by diagnozować osobno. Za mało zysku, za dużo dwoistości.

**Konsekwencja, którą trzeba przyjąć świadomie:** awaria huba zatrzymuje sterowanie.

---

## Czego ten system nie robi

**LagunBus nie jest systemem automatyki domowej.** Nie ma harmonogramów, warunków, pory
dnia, trybów domu ani logiki „jeśli nikogo nie ma, zgaś wszystko". To jest zrobione —
i zrobione dobrze — w Home Assistancie, Node-RED i im podobnych. Powtarzanie tego byłoby
budowaniem gorszej wersji czegoś, co już istnieje.

Zakres jest węższy i wyraźny: **obsługujemy urządzenia i wystawiamy je na zewnątrz.**

Do tego hub trzyma pulę **prostych, szybkich powiązań** typu klawisz → przekaźnik. Jest
po temu jeden powód i widać go w liczbach:

| Ścieżka | Opóźnienie | Dla czego |
|---|---|---|
| klawisz → hub → przekaźnik | **kilka ms** | zapalenie światła |
| klawisz → hub → system nadrzędny → hub → przekaźnik | dziesiątki do setek ms | wszystko inne |

Światło ma się zapalać natychmiast — także wtedy, gdy serwer akurat się aktualizuje.
Reszta może poczekać i może zależeć od czegokolwiek.

### Drugi wyjątek: pętla regulacji w węźle

Jest jeszcze jedna rzecz, która mieści się w zakresie mimo powyższego — i warto powiedzieć
wprost, dlaczego, bo z daleka wygląda na złamanie zasady.

Węzeł **może prowadzić jedną pętlę regulacji**: utrzymywać zadaną temperaturę obiegu,
załączając własne wyjście ([`types/0x0040-thermostat.md`](types/0x0040-thermostat.md)).

Powód jest inny niż przy szybkich powiązaniach i nie ma nic wspólnego z opóźnieniem —
pętla grzewcza jest wolna i nikogo nie obchodzi, czy zareaguje po dziesięciu, czy po dwustu
milisekundach. Powodem jest **czas przeżycia**:

| | Zapalanie światła | Ogrzewanie |
|---|---|---|
| Co boli przy awarii | ułamek sekundy zwłoki | **dom stygnie przez tydzień** |
| Co z tego wynika | powiązanie w hubie | pętla w węźle |

Awaria serwera na dwa dni jest niewygodą przy oświetleniu i awarią przy ogrzewaniu.
Dlatego pętla mieszka tam, gdzie przeżyje wszystko poza brakiem prądu.

Granica jest przy tym ostra i warto ją znać: **węzeł nie zna czasu kalendarzowego**
([`02-typy-danych.md`](02-typy-danych.md) §3.2). Wszystko, co wymaga wiedzy „która godzina"
albo „czy ktoś jest w domu", zostaje na zewnątrz i zmienia regulatorowi **jedną liczbę** —
nastawę. Harmonogram, tryby domu i obecność są nadal poza zakresem, dokładnie jak wyżej.

---

## Trzy gwarancje

**1. Determinizm.** Naciśnięcie klawisza wywołuje reakcję w przewidywalnym czasie albo
nie wywołuje jej wcale i jest to widoczne w diagnostyce. Nie ma stanu pośredniego
„czasem działa".

**2. Jawna ścieżka sterowania.** Wiadomo dokładnie, kto co wysłał, do kogo i kiedy.
Nie ma ukrytych pośredników ani cichych retransmisji zmieniających kolejność zdarzeń.

**3. Diagnozowalność.** Każdy węzeł raportuje liczniki błędów magistrali. Degradację
połączenia widać na wykresie, zanim stanie się odczuwalna dla mieszkańca.

---

## Skąd czerpiemy

Model danych pochodzi z **Zigbee Cluster Library** i **Matter Device Library**: pojęcia
atrybutu, komendy i zdarzenia oraz zasada, że typ urządzenia to lista wymaganych
zdolności, a nie lista właściwości. Dwadzieścia lat iteracji w tych specyfikacjach dało
model, który składa się kompozycyjnie i nie eksploduje kombinatorycznie.

Rozchodzimy się z nimi w dwóch miejscach. Po pierwsze, tam nazywa się to klastrem
i **endpoint skupia ich kilka**; u nas endpoint ma **dokładnie jeden typ**, więc osobne
słowo na pojemnik jest zbędne. Po drugie, Matter ma ponad czterdzieści klastrów, bo musi
obsłużyć zakres od żarówki po zmywarkę — nasz katalog liczy **kilkanaście typów**, z których
dwa (`Output` i `Sense`) pochłaniają kilkanaście klastrów Matter dzięki parametryzacji.

---

## Warstwy

```
┌─────────────────────────────────────────┐
│  System nadrzędny                       │  jeszcze nieustalony
├─────────────────────────────────────────┤
│  Adapter północny huba                  │  MQTT? TCP? szeregowy? — do ustalenia
├─────────────────────────────────────────┤
│  Hub                                    │  adresacja, reguły, model instalacji
├─────────────────────────────────────────┤
│  LagunBus — warstwa aplikacyjna         │  ← TA SPECYFIKACJA
│  typy endpointów, atrybuty, komendy     │
├─────────────────────────────────────────┤
│  Mapowanie na CAN 2.0B                  │  29-bit ID, 8 B danych
├─────────────────────────────────────────┤
│  CAN — warstwa fizyczna i łącza         │  para różnicowa + zasilanie
└─────────────────────────────────────────┘
```

**Model aplikacyjny jest projektowany pod ograniczenie ośmiu bajtów i dwudziestu dziewięciu
bitów identyfikatora.** Nie jest od CAN niezależny i nie udajemy, że jest: decyzja o jednym
typie na endpoint, szerokość adresu i rezygnacja z drugiego adresu w ramce wynikają wprost
z tego budżetu.

Podział ról jest natomiast ostry i obowiązuje w całej specyfikacji:

> **Zdania normatywne o ramce znajdują się wyłącznie w rozdziale 05.**
> W rozdziałach 01–04 CAN pojawia się tylko jako **uzasadnienie** decyzji modelowych.

Dzięki temu zmiana medium wymagałaby przepisania jednego rozdziału i przejrzenia
uzasadnień w pozostałych — a nie odtwarzania modelu danych od zera.

---

## Status

**v0.1 — w opracowaniu.** Nic nie jest zamrożone. Numery ID mogą się jeszcze zmienić.
