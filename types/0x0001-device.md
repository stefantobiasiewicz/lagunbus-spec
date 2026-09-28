# Typ endpointu `0x0001` · Device

> **Stabilne.** Rewizja 1 zamknięta. `Uid`, `VendorName` i `ModelName` odczytuje się
> w segmentach ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §6).

**Rewizja 1** · tożsamość węzła

Siedzi zawsze na **endpoincie 0** i jest jedynym typem obecnym w każdym węźle bez
wyjątku. Odpowiada na pytanie „czym jesteś" — zanim hub dowie się czegokolwiek o funkcjach
urządzenia, musi umieć odczytać ten typ.

---

## 1. Cechy

**Brak.** `Device` jest identyczny w każdym węźle; wariantowanie go zniweczyłoby sens
istnienia punktu, od którego zaczyna się rozpoznanie urządzenia.

---

## 2. Atrybuty

### 2.1 Tożsamość

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x00` | `Uid` | `blob` | RO | P | nie | M | 8–16 B, unikalny globalnie |
| `0x01` | `ShortId` | `u32` | RO | P | nie | M | CRC-32 z `Uid` |
| `0x02` | `DeviceType` | `u16` | RO | P | nie | M | model — unikalny w obrębie `VendorId` (§2.6) |
| `0x03` | `ProtocolVersion` | `u16` | RO | — | nie | M | `major << 8 \| minor` |
| `0x04` | `FirmwareVersion` | `u32` | RO | — | nie | M | `major << 16 \| minor << 8 \| patch` |
| `0x05` | `HardwareVersion` | `u16` | RO | P | nie | O | rewizja płytki |
| `0x06` | `VendorId` | `u16` | RO | P | nie | M | `0` = konstrukcja własna (§2.6) |
| `0x07` | `EndpointCount` | `u8` | RO | — | nie | M | liczba endpointów funkcjonalnych |
| `0x08` | `VendorName` | `string` | RO | P | nie | O | nazwa producenta, §2.7 |
| `0x09` | `ModelName` | `string` | RO | P | nie | O | nazwa modelu, §2.7 |

**Dlaczego dwa identyfikatory.** `Uid` jest prawdziwą tożsamością — pochodzi ze sprzętu,
nie zmienia się nigdy i jest za długi, by zmieścić się w pojedynczej ramce. `ShortId` to
jego skrót, który mieści się wszędzie i wystarcza tam, gdzie trzeba tylko odróżnić dwa
węzły od siebie, na przykład przy nadawaniu adresów.

Kolizja skrótu jest teoretycznie możliwa. Przy stu węzłach prawdopodobieństwo wynosi
około jednej milionowej, a skutkiem jest odmowa przyłączenia drugiego węzła — nie ciche
pomieszanie tożsamości. Hub porównuje pełny `Uid`, gdy tylko jest to możliwe.

### 2.2 Stan

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Uwagi |
|---|---|---|---|---|---|---|---|
| `0x10` | `Uptime` | `u32` | RO | — | nie | M | sekundy od startu |
| `0x11` | `BootCount` | `u16` | RO | P | nie | O | liczba uruchomień |
| `0x12` | `LastResetReason` | `enum8` | RO | — | nie | M | §2.4 |

`Uptime` nie jest raportowany cyklicznie — rósłby bez końca, generując ruch bez treści.
Odczytuje się go na żądanie albo bierze z `Booted` (§4).

### 2.3 Konfiguracja

| ID | Nazwa | Typ | Dostęp | Trw. | Rap. | Konf. | Zakres | Domyśl. |
|---|---|---|---|---|---|---|---|---|
| `0x20` | `Address` | `u16` | RW | P | nie | M | §2.5 | brak |

Sposób, w jaki węzeł adres otrzymuje, opisuje [`03-adresacja.md`](../03-adresacja.md) §5,
a zmianę już nadanego — [`06-cykl-zycia-urzadzenia.md`](../06-cykl-zycia-urzadzenia.md) §4.
Tutaj adres jest zwykłym atrybutem — trwałym, bo węzeł po restarcie musi wrócić na
magistralę pod tym samym numerem.

### 2.4 `LastResetReason`

| Wartość | Nazwa | Znaczenie |
|---|---|---|
| `0` | `POWER_ON` | włączenie zasilania |
| `1` | `EXTERNAL` | zewnętrzny sygnał zerowania |
| `2` | `WATCHDOG` | układ nadzorujący — **firmware się zawiesiło** |
| `3` | `SOFTWARE` | zamierzony restart, np. po komendzie `Reboot` |
| `4` | `BROWNOUT` | zapaść napięcia zasilania |
| `5` | `UNKNOWN` | przyczyny nie da się ustalić |

`WATCHDOG` i `BROWNOUT` to jedyne wartości, które oznaczają usterkę. Pierwsza wskazuje
na błąd oprogramowania, druga na niewydolne zasilanie albo za długi odcinek magistrali.
Hub powinien je odnotować i pokazać — węzeł, który sam się zeruje raz dziennie, jest
sprawny w każdej pojedynczej chwili i mimo to zepsuty.

### 2.5 Zakres adresu

Adres ma **11 bitów** i mieści się w `u16`; górne pięć bitów jest zawsze zerowe.
Wartość `0x000` oznacza **węzeł bez przydzielonego adresu**.

Pozostałe wartości i zasady ich nadawania opisuje
[`03-adresacja.md`](../03-adresacja.md).

### 2.6 Tożsamość modelu: `VendorId` + `DeviceType`

Deskryptor mówi, **co urządzenie potrafi**. Ta para mówi, **czym urządzenie jest** — i są
to dwa różne pytania, dokładnie tak jak adres i `Uid`
([`../03-adresacja.md`](../03-adresacja.md) §2.2).

> **Hub nigdy nie pyta rejestru modeli o to, co urządzenie potrafi.**
> Interpretacja danych opiera się wyłącznie na deskryptorze odczytanym z węzła.

Skoro tak, warto powiedzieć wprost, do czego `DeviceType` jest potrzebny, skoro nie do
interpretacji:

| Zastosowanie | Dlaczego deskryptor nie wystarcza |
|---|---|
| **Aktualizacja firmware** | dwa różne produkty mogą mieć identyczny deskryptor i niekompatybilny firmware; cztery wyjścia to cztery wyjścia, ale procesor pod spodem bywa inny |
| **Część zamienna** | do zamówienia zamiennika potrzeba nazwy modelu, nie listy zdolności |
| **Pochodzenie** | czyj to projekt i gdzie jest jego dokumentacja — jedyna rzecz, której z zachowania urządzenia wyprowadzić się nie da |

Wszystkie trzy są **inwentarzowe** i żadne nie jest pilne. Dlatego `DeviceType` odczytuje
się normalnie, z tego endpointu, i **nie ma go w ramce przyłączania**. Jedyną decyzją, którą
hub musi podjąć przed enumeracją, jest wybór bloku adresowego — służy do tego osobne pole
`NodeClass`, które mówi o pilności ruchu i nie wymaga od huba żadnej tablicy modeli
([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §4.1).

Rozdzielenie jest celowe: **numer modelu jest tożsamością, a nie priorytetem.** Wyprowadzanie
adresu z modelu wymagałoby, żeby hub znał katalog każdego producenta, z którego urządzeniem
się spotka — a nie zna i nie ma jak poznać.

**`DeviceType` jest unikalny w obrębie `VendorId`, nie globalnie.** Tożsamością modelu jest
para. Dzięki temu obcy autor może budować urządzenia bez pytania kogokolwiek o przydział
numeru — wystarczy mu własny `VendorId`, i to jest cała koordynacja, jakiej ten ekosystem
wymaga.

Z tego powodu `VendorId` jest **obowiązkowy**, choć jego wartość domyślna `0` znaczy po
prostu „konstrukcja własna". Gdyby był opcjonalny, para identyfikująca model rozpadłaby się
wszędzie tam, gdzie spotkałyby się urządzenia dwóch autorów.
### 2.7 Nazwy producenta i modelu

`VendorId` i `DeviceType` to tożsamość **dla maszyny**: para liczb, po której hub rozpoznaje
model i dobiera firmware. `VendorName` i `ModelName` to ta sama para **dla człowieka**:

```
VendorId  0            VendorName  "Lagun"
DeviceType 0x0205      ModelName   "DIN 4x16A z pomiarem"
```

Oba są `string` w UTF-8 i **nie mieszczą się w pojedynczej ramce** — odczytuje się je
w segmentach ([`../05-mapowanie-can.md`](../05-mapowanie-can.md) §6). Oba są
opcjonalne, bo urządzenie bez nich jest w pełni użyteczne; hub ma `VendorId` i `DeviceType`
i to mu wystarcza do wszystkiego, co robi automatycznie.

> **To nie jest nazwa nadana przez człowieka.** „Lampa nad stołem" mieszka w bazie huba
> ([`../02-typy-danych.md`](../02-typy-danych.md) §2.2) i tam zostaje. Tu chodzi o nazwę
> **fabryczną**, którą nadał autor urządzenia i której użytkownik nie zmienia.

Wartość tych atrybutów rośnie wraz z liczbą autorów. W instalacji zbudowanej przez jedną
osobę `DeviceType 0x0205` wystarcza. W instalacji, w której moduł zbudował ktoś inny, jest to
**jedyna rzecz mówiąca serwisantowi, co trzyma w ręku** — i jedyny punkt zaczepienia, żeby
znaleźć dokumentację.

Węzeł, który ich nie ma, odpowiada `UNSUPPORTED_ELEMENT`. Węzeł, który ma pamięć, ale nie ma
czego powiedzieć, zwraca łańcuch o długości zero.
---

## 3. Komendy

| ID | Nazwa | Argumenty | Konf. |
|---|---|---|---|
| `0x00` | `Identify` | `duration: u16` [s], `0` = przerwij | M |
| `0x01` | `Reboot` | `delay: u16` [ms] | M |
| `0x02` | `FactoryReset` | `magic: u32` | M |

### 3.1 `Identify`

Węzeł ma się zasygnalizować w sposób dostrzegalny dla człowieka stojącego obok —
zamrugać diodą, zapiszczeć, wypisać coś na wyświetlaczu. Czym dokładnie, zależy od
sprzętu; wymagane jest tylko, żeby **dało się to zauważyć i żeby ustało samo**.

To jedyny sposób, by odpowiedzieć na pytanie „która z tych czterdziestu identycznych
puszek to węzeł `0x2A`". Bez tego serwis instalacji polega na zgadywaniu.

Węzeł, który nie ma czym zasygnalizować, i tak musi komendę przyjąć i potwierdzić.

### 3.2 `Reboot`

Restart po upływie `delay`. Zwłoka istnieje po to, by węzeł zdążył potwierdzić przyjęcie
komendy, zanim zniknie z magistrali. `delay = 0` znaczy „natychmiast" i jest dopuszczalne,
ale wtedy nadawca nie ma jak odróżnić restartu od awarii.

Po restarcie węzeł emituje `Booted` z `LastResetReason = SOFTWARE`.

### 3.3 `FactoryReset`

Przywraca wartości domyślne **wszystkich** atrybutów konfiguracyjnych we wszystkich
typach węzła, łącznie z `Address`. Nie zmienia `Uid`, `DeviceType` ani wersji.

Argument `magic` musi mieć wartość `0x4C41474E` (znaki `LAGN`). Każda inna kończy się
odrzuceniem komendy. Zabezpieczenie jest tu dlatego, że przypadkowe wyzerowanie węzła
w ścianie kosztuje wyjazd z drabiną — a pojedynczy przekręcony bit w identyfikatorze
komendy nie powinien mieć takich skutków.

Węzeł **potwierdza komendę jeszcze spod starego adresu** i dopiero potem się zeruje — tak
samo jak przy zapisie `Address` ([`06-cykl-zycia-urzadzenia.md`](../06-cykl-zycia-urzadzenia.md)
§4.2). Potwierdzenie spod `0x000` nie dotarłoby do nikogo, a nadawca nie wiedziałby, czy
reset zaszedł. Po resecie węzeł jest w stanie **BEZ ADRESU** i zgłasza się jak nowe
urządzenie.

---

## 4. Zdarzenia

| ID | Nazwa | Parametry | Priorytet |
|---|---|---|---|
| `0x01` | `Booted` | `resetReason: enum8`, `firmwareVersion: u32` | `WARNING` |

Emitowane raz, gdy węzeł jest gotowy do pracy. Jest to jedyne zdarzenie w tym typie
i pełni trzy role naraz: ogłasza obecność węzła na magistrali, przenosi przyczynę
poprzedniego zerowania i pozwala hubowi wykryć restart, którego nie zlecił.

Priorytet `WARNING`, a nie `INFO`, bo **nieoczekiwany restart jest zawsze wart uwagi**.
Węzeł, który zgłasza `Booted` z przyczyną `WATCHDOG` w środku nocy, właśnie powiedział
coś ważnego o jakości firmware albo zasilania.

---

## 5. Zachowanie

### 5.1 Kolejność startowa

Węzeł nie odpowiada na nic, dopóki nie jest gotowy. Zanim wyśle `Booted`:

1. odtwarza konfigurację z pamięci trwałej,
2. inicjalizuje endpointy i doprowadza wyjścia do stanu wynikającego z ich konfiguracji,
3. przyłącza się do magistrali.

Dopiero potem emituje `Booted` i zaczyna odpowiadać na odczyty. Węzeł, który odpowiadałby
wcześniej, podawałby wartości sprzed odtworzenia konfiguracji — a hub nie miałby jak
odróżnić ich od prawdziwych.

### 5.2 Rozpoznanie urządzenia

Hub, który zobaczy nieznany węzeł, odczytuje w kolejności:

```
Device.DeviceType     ── czym to jest
Device.EndpointCount  ── ile ma funkcji
dla każdego endpointu:
    0xF0 TypeId       ── jaki typ
    0xF2 Features     ── w jakim wariancie
```

Cztery odczyty na endpoint plus dwa na węzeł
([`../06-cykl-zycia-urzadzenia.md`](../06-cykl-zycia-urzadzenia.md) §3.1).

**Odczyt z węzła jest rozstrzygający i jest jedynym źródłem.** Rejestr modeli
([`../registry/device-types.yaml`](../registry/device-types.yaml)) nie zawiera list
endpointów i nie będzie ich zawierał — urządzenie po aktualizacji firmware może mieć więcej
endpointów, niż miało w chwili produkcji, a hub ma to obsłużyć bez aktualizowania
czegokolwiek u siebie.

### 5.3 Zmiana adresu

Zapis `Address` odnosi skutek **natychmiast**: potwierdzenie zapisu wychodzi jeszcze
spod starego adresu, a wszystko po nim spod nowego. Nadawca musi być na to przygotowany.

Nowy adres trafia do pamięci trwałej przed potwierdzeniem, więc restart w trakcie operacji
nie zostawia węzła w stanie nieokreślonym — jest albo pod starym, albo pod nowym.

---

## 6. Reprezentacja poza magistralą

`Device` nie jest funkcją urządzenia i nie odpowiada niczemu, co użytkownik obsługuje.
Hub wykorzystuje go do zbudowania własnego obrazu instalacji, a na zewnątrz wystawia
najwyżej jako informacje serwisowe: wersję firmware, czas pracy, przyczynę ostatniego
restartu.

Nazwa nadana przez człowieka — „Salon, ściana wschodnia" — **nie mieszka w węźle**.
Trzyma ją hub, kluczując po `Uid` ([`02-typy-danych.md`](../02-typy-danych.md) §2.2).
