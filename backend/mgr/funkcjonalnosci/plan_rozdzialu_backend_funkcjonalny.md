# Plan rozdziału: Backend systemu symulacji inwestycyjnej

## 1. Cel i ogólna idea systemu

**Co opisać w tym miejscu:**

- Rozpocząć od krótkiego przedstawienia, że zbudowany system służy do symulowania działania automatycznych portfeli inwestycyjnych.
- Wyjaśnić, że symulacja odbywa się w określonym przedziale czasu: od daty początkowej do daty końcowej.
- Napisać, że system cyklicznie, np. co tydzień albo co ustalony krok czasowy, analizuje spółki i podejmuje decyzje inwestycyjne.
- Podkreślić, że decyzje nie są wpisywane ręcznie, tylko powstają automatycznie na podstawie danych finansowych, ocen spółek i parametrów danego portfela.
- Wspomnieć, że backend pełni rolę głównego silnika systemu, ponieważ odpowiada za pobieranie danych, prowadzenie portfeli, wykonywanie decyzji oraz zapisywanie wyników.

**Najważniejszy przekaz:**

System został zaprojektowany tak, aby możliwie automatycznie przeprowadzać pełną symulację inwestowania: od zebrania danych, przez ocenę spółek, aż po zakup, sprzedaż i zapis historii portfela.

**Czego nie rozwijać za bardzo:**

- Nie trzeba na początku tłumaczyć struktury folderów ani konkretnych klas.
- Nie trzeba od razu opisywać szczegółów technicznych API.

## 2. Zakres funkcjonalny backendu

**Co opisać w tym miejscu:**

- Wskazać, że backend odpowiada za kilka głównych obszarów działania systemu:
  - uruchamianie symulacji,
  - przechowywanie konfiguracji symulacji,
  - tworzenie portfeli inwestycyjnych,
  - pobieranie i aktualizowanie danych finansowych,
  - ocenianie spółek,
  - podejmowanie decyzji kupna i sprzedaży,
  - zapisywanie transakcji,
  - zapisywanie historii portfeli,
  - udostępnianie wyników do frontendu.
- Opisać backend jako część, która „spina” wszystkie procesy w jeden przepływ.
- Wspomnieć, że frontend jest warstwą prezentacji, natomiast rzeczywista logika symulacji znajduje się po stronie backendu.

**Najważniejszy przekaz:**

Backend nie jest tylko pośrednikiem między frontendem a bazą danych, ale samodzielnie prowadzi proces symulacji inwestycyjnej.

**Czego nie rozwijać za bardzo:**

- Nie trzeba szczegółowo opisywać, że istnieje osobny serwis do każdej operacji.
- Wystarczy zaznaczyć ogólny podział odpowiedzialności.

## 3. Konfiguracja symulacji

**Co opisać w tym miejscu:**

- Wyjaśnić, że przed uruchomieniem symulacji określa się jej podstawowe parametry.
- Opisać najważniejsze elementy konfiguracji:
  - lista analizowanych spółek,
  - data początkowa,
  - data końcowa,
  - krok czasowy symulacji,
  - początkowa wartość gotówki,
  - liczba portfeli generowanych dla danego typu strategii,
  - wybór konfiguracji archetypów.
- Napisać, że te parametry decydują o zakresie symulacji oraz o tym, jakie portfele zostaną porównane.
- Wspomnieć, że system może działać etapami, więc data startu nie zawsze musi być pierwotną datą początkową. Jeśli istnieje wcześniejsza historia, system może rozpocząć od kolejnego punktu po ostatnim zapisanym stanie.

**Najważniejszy przekaz:**

Konfiguracja określa ramy eksperymentu: jakie spółki są analizowane, jaki okres obejmuje symulacja i jakie typy portfeli biorą w niej udział.

**Czego nie rozwijać za bardzo:**

- Nie trzeba opisywać dokładnie, w którym pliku znajduje się każda stała konfiguracyjna.
- Można wspomnieć o tym tylko wtedy, gdy będzie potrzebny konkretny przykład.

## 4. Portfele inwestycyjne i ich parametry

**Co opisać w tym miejscu:**

- Przedstawić portfel jako podstawowy obiekt symulacji.
- Wyjaśnić, że każdy portfel posiada:
  - gotówkę,
  - posiadane akcje,
  - historię zmian,
  - zestaw parametrów wpływających na sposób inwestowania.
- Opisać, że portfele różnią się między sobą nie tylko nazwą, ale przede wszystkim parametrami strategii.
- Szczególnie opisać trzy najważniejsze parametry:
  - `top_m_share` jako parametr określający, jak szeroko portfel inwestuje w najlepsze spółki,
  - `investment_time_days` jako długość cyklu inwestycyjnego,
  - `rebalance_time_share` jako moment wykonania rebalancingu w trakcie cyklu.
- Wyjaśnić, że dzięki tym parametrom można badać różne style inwestowania, np. portfele bardziej skoncentrowane albo bardziej rozproszone, portfele o krótszym albo dłuższym horyzoncie oraz portfele szybciej albo wolniej reagujące na zmianę ocen spółek.

**Najważniejszy przekaz:**

Portfel w systemie jest nie tylko zapisem posiadanych aktywów, ale reprezentuje konkretną strategię inwestycyjną.

**Czego nie rozwijać za bardzo:**

- Nie trzeba tłumaczyć szczegółowo, jak technicznie liczona jest wartość każdej pozycji.
- Wystarczy napisać, że system na podstawie cen rynkowych potrafi wyznaczyć aktualną wartość portfela.

## 5. Archetypy strategii i generowanie portfeli

**Co opisać w tym miejscu:**

- Wyjaśnić, że archetyp jest wzorcem strategii inwestycyjnej.
- Napisać, że archetyp nie musi oznaczać jednego konkretnego portfela, ale może definiować zakres parametrów, z których generowane są różne portfele.
- Opisać, że system może utworzyć wielu użytkowników i wiele portfeli dla danego archetypu.
- Wskazać, że takie podejście pozwala testować nie jedną sztywną strategię, ale całą grupę podobnych strategii.
- Wspomnieć o benchmarku:
  - benchmark inwestuje szeroko w dostępne spółki,
  - jest punktem odniesienia dla strategii aktywnych,
  - pozwala sprawdzić, czy bardziej złożone strategie faktycznie osiągają lepsze wyniki.

**Najważniejszy przekaz:**

Archetypy pozwalają porównywać różne style inwestowania i badać, jak zmiana parametrów wpływa na wynik portfela.

**Czego nie rozwijać za bardzo:**

- Nie trzeba dokładnie opisywać sposobu losowania parametrów, chyba że chcesz pokazać, że portfele w ramach jednego archetypu mogą się od siebie różnić.

## 6. Dane wejściowe wykorzystywane przez system
## 7. Przygotowanie oceny pojedynczej spółki
## 8. Porównywanie spółek między sobą
(TE KROKI SĄ WAŻNE I SZERZEJ OPISANE W PLIKU pipeline_oceny_spolek)


## 9. Zamiana ocen na decyzje inwestycyjne

**Co opisać w tym miejscu:**

- Przejść od samej oceny spółek do praktycznego pytania: co portfel ma zrobić z tym rankingiem?
- Wyjaśnić, że system:
  - oblicza końcową ocenę spółki,
  - zamienia ją na pozycję względną względem innych spółek,
  - wybiera najlepszą część spółek,
  - przypisuje im docelowe udziały w portfelu,
  - tworzy decyzje kupna lub sprzedaży.
- Opisać znaczenie parametru `top_m_share`:
  - niska wartość oznacza portfel bardziej skoncentrowany,
  - wysoka wartość oznacza portfel bardziej rozproszony,
  - wartość benchmarkowa oznacza szerokie objęcie całego uniwersum spółek.
- Wspomnieć, że decyzje są deterministyczne, czyli dla tych samych danych i tych samych parametrów system wygeneruje te same decyzje.

**Najważniejszy przekaz:**

Ranking spółek jest przekształcany w konkretne działania portfela: zakup, sprzedaż albo brak zmiany.

**Czego nie rozwijać za bardzo:**

- Nie trzeba dokładnie opisywać matematyki każdej funkcji pomocniczej.
- Warto za to jasno opisać logiczny łańcuch: dane, ocena, ranking, wybór, transakcja.

## 10. Cykl inwestycyjny portfela

**Co opisać w tym miejscu:**

- Wyjaśnić, że portfel nie podejmuje całkowicie nowych decyzji w każdym kroku symulacji.
- Opisać ideę cyklu inwestycyjnego:
  - portfel wybiera zestaw spółek na początku cyklu,
  - przez pewien czas utrzymuje pozycje,
  - w określonym momencie może wykonać rebalancing,
  - po zakończeniu cyklu resetuje układ i buduje portfel od nowa.
- Opisać początek cyklu:
  - wybór najlepszych spółek,
  - zakup akcji,
  - zapis daty rozpoczęcia,
  - zapis początkowych ocen wybranych spółek.
- Opisać zakończenie cyklu:
  - sprzedaż albo zmiana dotychczasowych pozycji,
  - ponowny wybór spółek na podstawie aktualnego rankingu,
  - rozpoczęcie kolejnego cyklu.

**Najważniejszy przekaz:**

Cykl inwestycyjny nadaje strategii strukturę czasową i sprawia, że portfel nie reaguje chaotycznie na każdy pojedynczy odczyt danych.

**Czego nie rozwijać za bardzo:**

- Nie trzeba opisywać wszystkich pól przechowujących stan cyklu.
- Ważniejsze jest pokazanie, dlaczego cykl istnieje i jak wpływa na zachowanie strategii.

## 11. Rebalancing jako kontrolowana korekta portfela

**Co opisać w tym miejscu:**

- Wydzielić rebalancing jako osobny, ważny mechanizm.
- Wyjaśnić, że rebalancing odbywa się w trakcie cyklu inwestycyjnego, ale tylko w ustalonym momencie.
- Opisać, że moment rebalancingu zależy od parametru `rebalance_time_share`.
- Wyjaśnić, co system sprawdza podczas rebalancingu:
  - jak zmieniła się pozycja danej spółki w rankingu,
  - czy spółka pogorszyła się względem momentu wejścia do portfela,
  - czy warto ją dalej trzymać,
  - czy lepiej zastąpić ją inną spółką.
- Napisać, że słabsze pozycje mogą zostać sprzedane, a zwolniony kapitał może zostać przeniesiony do lepszych kandydatów.
- Podkreślić, że rebalancing nie jest pełnym restartem portfela, tylko korektą w trakcie trwania cyklu.

**Najważniejszy przekaz:**

Rebalancing pozwala portfelowi reagować na pogorszenie wybranych pozycji bez całkowitego rozpoczynania strategii od nowa.

**Czego nie rozwijać za bardzo:**

- Nie trzeba szczegółowo opisywać progu percentylowego jako wzoru, wystarczy wyjaśnić jego sens.

## 12. Realizacja decyzji inwestycyjnych i zapis stanu portfela

**Co opisać w tym miejscu:**

- Wyjaśnić, że po wygenerowaniu decyzji inwestycyjnej system wykonuje ją jako operację na symulowanym portfelu.
- Opisać mechanizm weryfikacji zleceń przed ich realizacją:
  - sprawdzanie wystarczającej ilości środków pieniężnych (dla transakcji kupna),
  - sprawdzanie odpowiedniej liczby posiadanych akcji (dla transakcji sprzedaży).
- Opiasć proces aktualizacji oraz zapisu stanu portfela po wykonaniu transakcji:
  - rejestrowanie bieżącej wartości i składu portfela,
  - możliwość późniejszego odtworzenia historii portfela w dowolnym momencie symulacji,
  - analiza wpływu poszczególnych decyzji inwestycyjnych na osiągnięte wyniki.
- Opisać działanie systemu po ponownym uruchomieniu:
  - odczytywanie ostatniego zapisanego stanu portfela i kontynuacja inwestycji,
  - etapowe prowadzenie symulacji bez konieczności ponownego przeliczania wcześniejszych kroków,
  - pobieranie najnowszych danych rynkowych i finansowych (jeśli są dostępne) do kontynuowania symulacji na zaktualizowanym zbiorze danych.

**Najważniejszy przekaz:**

Każda decyzja inwestycyjna jest weryfikowana i realizowana na symulowanym portfelu, a jego stan jest na bieżąco zapisywany, co umożliwia analizę wyników, wstrzymywanie oraz płynne wznawianie symulacji z uwzględnieniem najnowszych danych.

**Czego nie rozwijać za bardzo:**

- Nie opisywać szczegółowych algorytmów walidacji ani struktur bazodanowych odpowiedzialnych za przechowywanie historii portfela.
- Nie zagłębiać się w techniczną implementację mechanizmów I/O i formatów plików stanu.

## 13. Pełny przebieg działania symulacji

**Co opisać w tym miejscu:**

- Ten podrozdział powinien zebrać wcześniejsze elementy w jeden ciąg przyczynowo-skutkowy.
- Opisać pełny scenariusz działania:
  - użytkownik wybiera zakres dat i parametry symulacji,
  - frontend wysyła żądanie do backendu,
  - backend sprawdza, czy symulacja może zostać uruchomiona,
  - system ustala datę startu,
  - tworzy albo odtwarza portfele,
  - sprawdza dostępność danych,
  - pobiera brakujące dane,
  - przechodzi przez kolejne punkty czasu,
  - przygotowuje ocenę spółek,
  - tworzy ranking,
  - każdy portfel interpretuje ranking zgodnie z własnymi parametrami,
  - system wykonuje decyzje kupna i sprzedaży,
  - zapisuje transakcje i stan portfela,
  - przechodzi do kolejnego kroku,
  - kończy działanie po osiągnięciu daty końcowej.
- Warto dodać w pracy prosty schemat blokowy pokazujący ten przepływ.

**Najważniejszy przekaz:**

Cały system działa jak zamknięty proces symulacyjny, w którym każdy kolejny etap wynika z poprzedniego: dane prowadzą do ocen, oceny do rankingu, ranking do decyzji, decyzje do transakcji, a transakcje do historii wyników.

**Proponowany schemat do narysowania:**

```text
Konfiguracja symulacji
        ↓
Sprawdzenie i pobranie danych
        ↓
Ocena pojedynczych spółek
        ↓
Ranking cross-section
        ↓
Decyzje portfeli
        ↓
Kupno / sprzedaż / brak zmiany
        ↓
Zapis transakcji i historii portfela
        ↓
Przejście do kolejnego kroku czasu
```

## 14. Tryb batchowy

**Co opisać w tym miejscu:**

- Krótko wspomnieć, że oprócz standardowego uruchomienia istnieje także tryb batchowy.
- Opisać go jako wariant działania przeznaczony do większych lub bardziej zbiorczych symulacji.
- Napisać, że jest uruchamiany jako alternatywny tryb, ale korzysta z tej samej ogólnej idei: danych, portfeli, decyzji i zapisu wyników.

**Najważniejszy przekaz:**

Tryb batchowy pokazuje, że system został przygotowany nie tylko do pojedynczego uruchomienia, ale również do bardziej masowego przetwarzania symulacji.

**Czego nie rozwijać za bardzo:**

- Nie opisywać folderu `testy`.
- Nie robić z tego głównej części rozdziału, raczej potraktować jako funkcjonalne rozszerzenie.

## 15. Podsumowanie rozdziału

**Co opisać w tym miejscu:**

- Krótko zebrać najważniejsze informacje:
  - backend prowadzi symulację od początku do końca,
  - sam przygotowuje dane,
  - tworzy i obsługuje portfele,
  - ocenia spółki,
  - podejmuje decyzje inwestycyjne,
  - zapisuje historię i transakcje,
  - umożliwia kontynuowanie działania,
  - udostępnia wyniki frontendowi.
- Zakończyć myślą, że backend jest centralnym elementem projektu, ponieważ łączy model danych, strategię inwestycyjną i możliwość analizy wyników.

**Propozycja zdania końcowego:**

W efekcie powstał backend, który automatyzuje cały proces symulacji inwestycyjnej: od przygotowania danych, przez ocenę spółek i prowadzenie portfeli, aż po zapis decyzji oraz udostępnienie wyników do dalszej analizy.
