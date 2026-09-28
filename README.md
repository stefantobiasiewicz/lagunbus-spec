# LagunBus

Otwarta specyfikacja warstwy aplikacyjnej dla przewodowej automatyki domowej.

Instalacja to **węzły** na **magistralach CAN**, którymi zarządza **hub**. Magistrala
niesie zasilanie i różnicową parę danych; rodzaj kabla, napięcie i topologia są
decyzjami wdrożeniowymi, nie elementami tej specyfikacji.

**Status: v0.1, w opracowaniu.** Nic tu jeszcze nie jest zamrożone.

---

## Jak czytać

To repozytorium zawiera **wyłącznie specyfikację**. Firmware, oprogramowanie huba
i narzędzia mieszkają w osobnych repozytoriach.

Zacznij od [`00-wprowadzenie.md`](00-wprowadzenie.md), potem
[`01-model-danych.md`](01-model-danych.md). Gdy coś w tabeli jest niejasne —
[`POJECIA.md`](POJECIA.md) wyjaśnia notację i słownictwo.

### Rozdziały

| Plik | Zawartość | Stan |
|---|---|---|
| [`00-wprowadzenie.md`](00-wprowadzenie.md) | cel, zakres, instalacja, hub, kierunek ruchu | stabilne |
| [`01-model-danych.md`](01-model-danych.md) | węzeł, endpoint, typ, atrybut, komenda, zdarzenie, kanał | stabilne |
| [`02-typy-danych.md`](02-typy-danych.md) | typy, jednostki, skale, kodowanie | stabilne |
| [`03-adresacja.md`](03-adresacja.md) | adresy węzłów, endpointów, grup; przyłączanie węzła | stabilne |
| [`04-interakcje.md`](04-interakcje.md) | odczyt, zapis, komenda, raport, zdarzenie | stabilne |
| [`05-mapowanie-can.md`](05-mapowanie-can.md) | identyfikator, rodzaje ramek, priorytet, segmenty, budżet pasma | **szkic** |
| [`06-cykl-zycia-urzadzenia.md`](06-cykl-zycia-urzadzenia.md) | dodanie, rozpoznanie, zmiana adresu, usunięcie | stabilne |
| [`07-hub.md`](07-hub.md) | model instalacji, powiązania, restart huba, wiele magistral | **szkic** |
| [`08-wersjonowanie.md`](08-wersjonowanie.md) | jak wolno zmieniać kontrakt, żeby nie psuć tego, co wisi w ścianie | **szkic** |

Wszystkie planowane rozdziały istnieją.

### Katalogi i dokumenty pomocnicze

| Plik / katalog | Zawartość |
|---|---|
| [`types/`](types/) | katalog typów endpointów; [`SZABLON.md`](types/SZABLON.md) dla nowych |
| [`registry/`](registry/) | **rejestr identyfikatorów — źródło prawdy** dla ID, kodów, skal i modeli (niżej) |
| [`PRZYKLADY.md`](PRZYKLADY.md) | przykładowe ramki na magistrali — od konfiguracji po arbitraż |
| [`COMPLIANCE.md`](COMPLIANCE.md) | **wymagania zgodności** — ponumerowane, do odhaczenia przed podłączeniem |
| [`POJECIA.md`](POJECIA.md) | słownik, notacja tabel, siła zobowiązań |
| [`OTWARTE.md`](OTWARTE.md) | punkty otwarte i sprzeczności znalezione przy implementacji |
| [`DECYZJE.md`](DECYZJE.md) | rejestr decyzji — dlaczego tak, a nie inaczej; pisany ręcznie |

## Rejestr identyfikatorów

W [`registry/`](registry/) mieszkają **liczby, które muszą znaczyć jedno**: identyfikatory
typów endpointów, rodzaje ramek, kody wyniku, wielkości fizyczne i ich skale.

> **Rejestr jest źródłem prawdy.** Gdy tabela w markdown nie zgadza się z YAML-em,
> to tabela jest błędna.

Ta sama liczba potrafi być potrzebna w trzech narracjach naraz: w rozdziale ogólnym,
w specyfikacji typu i w rozdziale o mapowaniu na ramki. Dopóki mieszkała wyłącznie
w prozie, każde jej użycie było osobną kopią — i kopie zaczęły się rozjeżdżać. Tabela
w markdown zostaje, bo jest formą czytelną dla człowieka; rejestr rozstrzyga, **która
wersja jest prawdziwa**, i pozwala to sprawdzić maszynowo.

| Plik | Zawiera | Odpowiada tabeli |
|---|---|---|
| `endpoint-types.yaml` | ID typów, ich stan i przydział bloków | `types/`, [`01-model-danych.md`](01-model-danych.md) §1.2 |
| `frame-kinds.yaml` | pole `RODZAJ`, 4 bity | [`05-mapowanie-can.md`](05-mapowanie-can.md) §2 |
| `result-codes.yaml` | kody odpowiedzi | [`04-interakcje.md`](04-interakcje.md) §9 |
| `node-classes.yaml` | `NodeClass` w ramce przyłączania | [`05-mapowanie-can.md`](05-mapowanie-can.md) §4.1 |
| `quantities.yaml` | wielkości, typy, skale, histerezy | [`02-typy-danych.md`](02-typy-danych.md) §3, [`0x0030-sense.md`](types/0x0030-sense.md) §2.3 |

### Zanim coś zmienisz

```sh
python3 registry/check.py
```

Bez zależności zewnętrznych — skrypt czyta tylko te pola YAML, których potrzebuje.
Uruchamiaj przed każdym commitem dotykającym identyfikatorów albo numeracji sekcji.
Sprawdza:

1. każdy typ oznaczony jako `opisany` ma plik, a nagłówek pliku zgadza się z ID i nazwą,
2. każdy plik w `types/` jest w rejestrze — nie da się dodać typu po cichu,
3. kody wyniku, rodzaje ramek, klasy węzłów i atrybuty wspólne zgadzają się z tabelami —
   w przypadku rodzajów ramek sprawdzany jest **każdy wiersz w rozdziale 05**, nie jeden,
4. **endpointy systemowe w diagramach** mają typ zgodny z rejestrem — diagramy ASCII są
   wycinane przed pozostałymi kontrolami, więc bez tego mogłyby latami twierdzić co innego
   niż tabela obok,
5. **odsyłacze do sekcji** wskazują sekcje, które istnieją — numer wygląda poprawnie,
   dopóki ktoś za nim nie pójdzie,
6. w całej specyfikacji nie ma martwego odsyłacza do pliku,
7. **`NodeClass` nie wyciekł do tabeli atrybutów** typu `Device` — to wskazówka do rozruchu,
   nie stan węzła; w atrybutach byłby drugim opisem zdolności obok deskryptora.

Tabele markdown **nie są generowane** z YAML-a: zgodność jest sprawdzana, nie wymuszana.
Generator ma sens dopiero wtedy, gdy format tabel przestanie się zmieniać.

## Czego ta specyfikacja nie ustala

Świadomie **nie definiujemy**:

- **mikrokontrolerów ani układów scalonych** — opisujemy standard, nie konkretną płytkę,
- **rodzaju kabla, złączy, napięcia zasilania i topologii** — to decyzje wdrożeniowe,
- **systemu nadrzędnego** i tego, na co hub tłumaczy instalację na zewnątrz.

Ustalone jest natomiast to, co musi być wspólne dla wszystkich implementacji:
**CAN 2.0B, identyfikator rozszerzony 29-bitowy, ładunek 8 bajtów.**

## Dlaczego nie Zigbee, nie Modbus, nie Matter

- **Zigbee/BLE** — bezprzewodowe, więc czasem trzeba nacisnąć dwa razy. To jest
  cały powód istnienia tego projektu.
- **Modbus RTU** — master robi polling, więc opóźnienie zależy od cyklu odpytywania
  i rośnie z liczbą urządzeń. Zły model dla zdarzeń.
- **Matter/Zigbee Cluster Library** — model danych jest znakomity i stąd go
  bierzemy, ale katalog obejmuje pralki i telewizory, a ramka nie mieści się
  w ośmiu bajtach CAN 2.0B.

Katalog urządzeń ograniczamy do tego, co **przewodowe i budowane samodzielnie**:
puszki podtynkowe i szyna DIN.

---

## Decyzje już podjęte

Uzasadnienia: [`DECYZJE.md`](DECYZJE.md).

| Decyzja | Wybór |
|---|---|
| Magistrala | **CAN 2.0B**, identyfikator rozszerzony 29-bit, ładunek 8 B |
| Szyny magistrali | zasilanie + para różnicowa danych |
| Kierunek ruchu | **węzeł ↔ hub**; urządzenia **nie rozmawiają ze sobą** |
| Zakres | obsługa urządzeń i proste, szybkie powiązania; **automatyka po stronie systemu nadrzędnego** |
| Adresacja | **globalna, 11-bitowa** — 2045 węzłów; tożsamością jest `Uid`, nie adres |
| Model aplikacyjny | **własny minimalny zestaw typów endpointów** |
| Struktura endpointu | **jeden endpoint = jeden typ** |
| Komenda | **jest transakcją** — ma odpowiedź; skutek fizyczny widać osobno w raporcie |
| Model urządzenia | tożsamością jest para `VendorId` + `DeviceType`; **rejestr nie opisuje zdolności** |
| Rozszerzanie przez obcych autorów | własny `VendorId` plus producencka przestrzeń typów `0x8000–0xFFFE` |
| Język | polski; identyfikatory po angielsku |
| Forma katalogu | markdown pisany ręcznie; **identyfikatory w [`registry/`](registry/)**, sprawdzane skryptem |
