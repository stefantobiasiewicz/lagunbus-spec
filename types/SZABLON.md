# Typ endpointu `0xNNNN` · Nazwa

> **Szkic.** Co jest ustalone, a co jeszcze nie.

**Rewizja 1** · jedno zdanie, czym to jest

Dwa–trzy zdania: co ten typ obsługuje, wymienione konkretnie. Potem, jeśli istnieje typ
sąsiedni, z którym łatwo go pomylić — wyraźne odgraniczenie w cytacie blokowym:

> **Czym to się różni od [`Innego`](0xNNNN-inny.md).** Jedno kryterium, nie trzy.

Jeśli typ obejmuje szeroką rodzinę urządzeń — powiedz jaką i dlaczego jeden typ wystarcza.
**Bez porównań z innymi protokołami**: te należą do osobnego dokumentu
([`../POJECIA.md`](../POJECIA.md) §4).

---

## 1. Cechy

Gdy typ ma cechy:

| Bit | Cecha | Dokłada |
|---|---|---|
| — | *(zawsze)* | atrybuty i komendy obecne bez względu na cechy |
| 0 | `NAZWA` | co dokłada |
| 1–15 | — | zarezerwowane, nadawaj `0` |

Gdy nie ma — **Brak.** plus jedno zdanie, *dlaczego* nie ma. Najczęstszy powód: to, czym
urządzenia się różnią, jest konfiguracją zmienną w czasie pracy, a nie właściwością sprzętu.

---

## 2. Atrybuty

### 2.1 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x00` | | | RO | V | tak | M | | |

### 2.2 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x10` | | | RW | P | nie | M | | |

Numeracja: stan od `0x00`, konfiguracja od `0x10`. Atrybutów wspólnych `0xF0`–`0xFA`
**nie powiela się** ([`../01-model-danych.md`](../01-model-danych.md) §4).

Wyliczenia i pola bitowe dostają własną podsekcję `### 2.x` z pełną tabelą wartości.

---

## 3. Komendy

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | | | M |

Każda komenda jest transakcją i dostaje odpowiedź z kodem wyniku
([`../04-interakcje.md`](../04-interakcje.md) §5). Gdy typ ma nietypowe kody błędów —
tabela „sytuacja → wynik".

Gdy komend nie ma — **Brak.** i jedno zdanie dlaczego.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet | Konf. |
|---|---|---|---|---|
| `0x01` | | | `INFO` | M |

Gdy zdarzeń nie ma — **Brak.** i uzasadnienie przez rozróżnienie stanu i faktu
([`../01-model-danych.md`](../01-model-danych.md) §3). Typ, który ma stan, zwykle nie
potrzebuje zdarzeń: zmiana stanu jest raportem.

---

## 4a. Wejścia

**Tylko jeśli typ ma atrybuty wypełniane przez hub.** Większość typów nie ma — pomiń całą
sekcję, zamiast pisać „Brak".

| Bit | Atrybut | Czym jest |
|---|---|---|
| 0 | | |
| 1–15 | — | zarezerwowane, nadawaj `0` |

Wejście to atrybut **zapisywalny, ulotny, którego węzeł sam nie zmierzy**. Numery bitów są
te, których hub używa w `QueryEnabled` ([`../04-interakcje.md`](../04-interakcje.md) §8.6).

W „Zachowaniu" trzeba wtedy powiedzieć **co typ robi bez tej wartości** — nie wolno czekać
ani przestać działać (§8.3 tamże).

---

## 5. Zachowanie

Sedno dokumentu. Jedna podsekcja na jedno rozstrzygnięcie, każda z uzasadnieniem.
Diagramy stanów w blokach kodu, jeśli typ ma maszynę stanów.

Co tu musi być, jeśli dotyczy typu:

- **relacje między atrybutami** — który jest prawdziwy, a który wyprowadzony,
- **stan początkowy** — co węzeł pokazuje, zanim cokolwiek zmierzy albo ustali; prawie
  zawsze wartość „brak", nigdy zero,
- **granice i nasycenia** — co się dzieje przy wartości poza zakresem,
- **trwałość** — co przeżywa restart, co znika,
- **koszt na magistrali** — ile ramek generuje typowe użycie.

---

## 6. Konfiguracje typowe

| Urządzenie | Cechy | Kluczowe atrybuty | Uwagi |
|---|---|---|---|

Tabela odpowiada na pytanie „mam takie urządzenie, jak je ustawić". Warto tu umieścić
wiersz, który pokazuje, czego tym typem robić **nie należy**.

---

## 7. Reprezentacja poza magistralą

Sposób, w jaki hub wystawia typ na zewnątrz, **nie należy do tej specyfikacji**. Warto
natomiast zapisać zalecenia wynikające z charakteru typu, a nie z wyboru adaptera —
zwykle jedno albo dwa, wyróżnione cytatem blokowym.

---

## Odstępstwa od układu

Powyższy układ obowiązuje **typy funkcjonalne**. Dwie rzeczy wolno zmienić, jeśli typ tego
wymaga:

- **Dołożyć sekcję przed atrybutami**, gdy typ ma pojęcie, bez którego reszta jest
  niezrozumiała. Tak robi [`Scenes`](0x0003-scenes.md), który zaczyna od tożsamości sceny —
  bo bez pary `(grupa, numer)` nie da się czytać ani atrybutów, ani komend.
- **Pominąć „Konfiguracje typowe"** w typach systemowych. `Device`, `Diagnostics` i `Groups`
  są identyczne w każdym węźle, więc tabela „mam takie urządzenie, jak je ustawić" nie ma
  czego zawierać.

Czego **nie** wolno: zmieniać kolejności sekcji, które zostają, ani numerować ich inaczej.
Czytelnik, który zna jeden typ, ma znać układ wszystkich.

## Zasady redakcyjne

Poza układem obowiązują trzy rzeczy:

1. **Każde rozstrzygnięcie ma uzasadnienie.** Nie „tak jest", tylko „tak jest, bo inaczej
   stałoby się to i to". Uzasadnienie jest tym, co przeżyje autora.
2. **Zdania normatywne o ramce należą do rozdziału 05.** Tutaj CAN występuje wyłącznie
   jako powód ([`../00-wprowadzenie.md`](../00-wprowadzenie.md) § Warstwy).
3. **Nowy typ dopisz do [rejestru](../registry/endpoint-types.yaml)** i uruchom
   `python3 registry/check.py`. Plik nieobecny w rejestrze jest błędem.
