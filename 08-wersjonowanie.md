# 08 · Wersjonowanie kontraktu

> **Szkic.** Reguły ustalone; zamrożenie v1 jeszcze nie nastąpiło.

Specyfikacja będzie się zmieniać po tym, jak powstaną pierwsze urządzenia. Ten rozdział
mówi, **jak wolno ją zmieniać, żeby to, co już wisi w ścianie, nie przestało działać.**

Pytanie nie jest teoretyczne. Węzeł w puszce podtynkowej żyje dwadzieścia lat i nikt go nie
zaktualizuje, bo trzeba by zdjąć ramkę, wykręcić moduł i podłączyć programator. **Każda
reguła w tym rozdziale zakłada, że aktualizacja węzła jest niemożliwa.**

---

## 1. Cztery liczby, które łatwo pomylić

| Liczba | Gdzie | Mówi o |
|---|---|---|
| `ProtocolVersion` | [`Device`](types/0x0001-device.md) `0x03` | **kontrakcie** — tej specyfikacji |
| `TypeRevision` | atrybut wspólny `0xF1` | **typie endpointu** — jego kontrakcie |
| `FirmwareVersion` | [`Device`](types/0x0001-device.md) `0x04` | **oprogramowaniu** konkretnego węzła |
| `HardwareVersion` | [`Device`](types/0x0001-device.md) `0x05` | **płytce** |

Dwie pierwsze są **wspólne dla wszystkich**: mówią, jakim językiem węzeł mówi. Dwie ostatnie
są jego prywatną sprawą — hub używa ich do aktualizacji i serwisu, nie do rozumienia ramek.

Najczęstsza pomyłka polega na wiązaniu zachowania z `FirmwareVersion`. Jest to zawsze błąd:
firmware zmienia się z powodów, o których hub nie ma pojęcia, a kontrakt zmienia się przez
`ProtocolVersion` i `TypeRevision`.

---

## 2. `ProtocolVersion`

`u16` w postaci `major << 8 | minor`.

| Część | Rośnie, gdy |
|---|---|
| **minor** | coś **przybywa**: nowy rodzaj ramki, kod wyniku, atrybut wspólny, typ endpointu |
| **major** | coś się **zmienia albo znika**: inne pole, inna szerokość, inne znaczenie |

> **Zmiana `minor` nie może zepsuć niczego, co działało.** Wolno wyłącznie dokładać.

Węzeł deklarujący `major` `1`, `minor` `0` rozumie się z hubem obsługującym `1.7` — hub po
prostu nie użyje wobec niego niczego, co przyszło po `1.0`. Odwrotnie też: hub `1.0` i węzeł
`1.7` dogadają się w zakresie `1.0`.

### 2.1 Różne `major` to różne protokoły

Hub, który zobaczy węzeł o innym `major`, **nie interpretuje go**. Zgłasza to operatorowi
jako urządzenie wymagające uwagi i zostawia w spokoju — nie zgaduje, nie próbuje częściowo.

Żeby to w ogóle było wykonalne, jedna rzecz musi przetrwać każdą zmianę `major`:

> **Odczyt `ProtocolVersion` z endpointu `0` musi działać zawsze.**
> Cokolwiek zmieni się w przyszłej wersji `major`, ta jedna ścieżka zostaje nietknięta.

Bez tego hub napotkany węzeł mógłby tylko zignorować, nie wiedząc nawet, dlaczego go nie
rozumie. Jest to jedyne zobowiązanie, jakie ta specyfikacja zaciąga wobec swoich własnych
przyszłych wersji.

---

## 3. Rewizja typu tylko rośnie

`TypeRevision` jest `u8` bez podziału na `major` i `minor` — i nie potrzebuje go, bo
obowiązuje reguła mocniejsza:

> **Kontrakt typu może wyłącznie rosnąć.** Zmiana, która zepsułaby istniejącą implementację,
> **wymaga nowego identyfikatora typu**, a nie nowej rewizji.

Wolno więc dołożyć atrybut opcjonalny, komendę, cechę, wartość wyliczenia, bit w polu
bitowym. Nie wolno zmienić skali, szerokości, znaczenia bitu ani usunąć czegokolwiek.

### 3.1 Dlaczego nie „podnieś rewizję i zaktualizuj węzły"

Bo to nie jest opcja. Węzeł w ścianie zostaje z rewizją, którą ma, na resztę swojego życia.

Gdyby rewizja mogła oznaczać zmianę niezgodną, **hub musiałby nosić osobną implementację
każdego typu w każdej rewizji** i wybierać ją przy każdej ramce. Przy dwóch rewizjach to
uciążliwe, przy pięciu — źródło błędów, których nikt nie odtworzy.

Przy regule „tylko rośnie" hub ma **jedną implementację na typ**. Rewizja mówi mu wyłącznie,
**ile** z typu istnieje w tym węźle:

```
węzeł deklaruje   TypeRevision = 1     hub zna rewizję 3
                                       → używa wyłącznie tego, co było w rewizji 1

węzeł deklaruje   TypeRevision = 3     hub zna rewizję 1
                                       → używa tego, co zna; reszty nie widzi
```

Cena jest jedna i trzeba ją znać: **prawdziwa pomyłka projektowa w typie kosztuje nowy
identyfikator.** Jest to cena właściwa — identyfikatorów mamy trzydzieści dwa tysiące
wolnych, a urządzeń w ścianach nie da się poprawić.

---

## 4. Co robić z czymś nieznanym

To jest sedno zgodności w przód i dlatego jest tabelą, a nie prozą. **Odbiorca nigdy nie
zgaduje.**

| Nieznane | Odbiorca |
|---|---|
| Rodzaj ramki | **ignoruje** — nie odpowiada, nie zgłasza błędu |
| Typ endpointu | **nie interpretuje** go; reszta urządzenia działa normalnie |
| Atrybut albo komenda | odsyła `UNSUPPORTED_ELEMENT` |
| Bit cechy | **ignoruje**; nie zakłada, że coś dzięki niemu potrafi |
| Wartość wyliczenia | traktuje jak **nieznaną**, nie jak domyślną |
| Kod wyniku | traktuje jak **błąd**, nigdy jak powodzenie |

Ostatni wiersz jest najważniejszy i najmniej oczywisty. Gdyby nieznany kod wyniku był
traktowany jak sukces, dołożenie nowego kodu błędu w wersji `minor` **po cichu zepsułoby
każdy starszy hub** — dostawałby informację o niepowodzeniu i uznawał je za wykonanie.
Reguła „nieznane znaczy źle" sprawia, że nowy kod błędu jest zawsze zmianą bezpieczną.

Przedostatni wiersz działa podobnie: `Purpose` o nieznanej wartości ma zostać nieznany,
a nie zamienić się w `GENERIC`. Domyślna wartość jest decyzją, a odbiorca nie ma prawa jej
podejmować za urządzenie.

---

## 5. Kiedy hub może użyć nowości

> **Hub używa wobec węzła wyłącznie tego, co mieści się w zadeklarowanych przez niego
> `ProtocolVersion` i `TypeRevision`.**

Nie jest to grzeczność, tylko warunek działania: węzeł nie ma jak odmówić w sposób, który
hub zrozumie inaczej niż jako błąd. Hub, który wysyła nowy rodzaj ramki do starego węzła,
dostaje ciszę — nieodróżnialną od awarii.

Wyjątkiem są rzeczy, które **nie zmieniają zachowania węzła**: odczyt atrybutu, którego może
nie mieć, jest bezpieczny, bo odpowiedzią będzie `UNSUPPORTED_ELEMENT`, a nie cisza.

---

## 6. Wersjonowaniem zajmuje się hub

> **Węzeł nie negocjuje wersji i nie zmienia zachowania w zależności od tego, kto pyta.**

Deklaruje, czym jest, i zachowuje się zawsze tak samo. Nie ma w nim ani jednej gałęzi
„jeśli hub jest nowszy". Cała asymetria jest po stronie huba — i tak ma być, bo hub jest
jeden, aktualizuje się łatwo i ma pamięć.

Wynika stąd rzecz praktyczna dla autorów urządzeń: **implementacja węzła nie musi wiedzieć,
że wersjonowanie istnieje.** Wystarczy, żeby poprawnie deklarowała swoje liczby i odpowiadała
`UNSUPPORTED_ELEMENT` na to, czego nie zna.

---

## 7. Co się zmieni po zamrożeniu v1

Dziś obowiązuje **v0.1** i nic nie jest zamrożone — numery mogą się jeszcze zmienić,
drabinka priorytetów też ([`README.md`](README.md)).

Zamrożenie v1 oznacza, że od tej chwili:

| Wolno | Nie wolno |
|---|---|
| dokładać rodzaje ramek z wolnych wartości | przenumerowywać istniejących |
| dokładać kody wyniku, typy, atrybuty wspólne | zmieniać znaczenia istniejących |
| dokładać cechy i wartości wyliczeń | zmieniać skal i szerokości pól |
| podnosić rewizje typów o nowe elementy | usuwać cokolwiek |

Dlatego rzeczy nieodwracalne rozstrzyga się **przed** zamrożeniem, a nie po. Dwie z nich już
zapadły i obie były darmowe wtedy, a niemożliwe później: rezerwa w drabince priorytetów
([`05-mapowanie-can.md`](05-mapowanie-can.md) §2.3) i przestrzeń producencka w typach
([`registry/endpoint-types.yaml`](registry/endpoint-types.yaml)).

---

## 8. Przed zamrożeniem

Warunkiem zamrożenia v1 jest pierwsza działająca instalacja: dopóki nic nie działa, każda
reguła jest hipotezą. Z zamrożeniem [`COMPLIANCE.md`](COMPLIANCE.md) zaczyna deklarować,
której wersji kontraktu dotyczy.
