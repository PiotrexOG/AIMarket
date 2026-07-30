# Plan rozdziału: Frontend systemu symulacji inwestycyjnej

## 1. Rola frontendu w systemie

**Co opisać w tym miejscu:**

- Napisać, że jego głównym zadaniem jest uruchamianie symulacji, przeglądanie wyników oraz analiza decyzji inwestycyjnych.
- Wspomnieć, że aplikacja została podzielona na kilka zakładek odpowiadających najważniejszym obszarom pracy z systemem.

**Najważniejszy przekaz:**

Frontend pełni rolę panelu sterowania i analizy wyników symulacji inwestycyjnej.

## 2. Zakładka Home

**Co opisać w tym miejscu:**

- Opisać zakładkę jako miejsce rozpoczęcia pracy z systemem.
- Wyjaśnić, że użytkownik może uruchomić nową symulację, podając:
  - datę początkową,
  - datę końcową,
  - interwał między kolejnymi ocenami spółek,
  - liczbę użytkowników na archetyp,
  - informację, czy symulacja ma zostać uruchomiona w trybie batchowym.
- Napisać, że z tego poziomu można także zresetować aktualny stan bazy danych dotyczący poprzedniej symulacji.
- Podkreślić, że zakładka Home jest punktem wejścia do całego procesu symulacyjnego.

**Najważniejszy przekaz:**

Home pozwala skonfigurować i uruchomić symulację oraz wyczyścić wcześniejsze wyniki, jeśli użytkownik chce rozpocząć nowy eksperyment.

## 3. Zakładka Portfolio

**Co opisać w tym miejscu:**

- Wyjaśnić, że zakładka Portfolio służy do analizy wyników konkretnych portfeli inwestycyjnych.
- Napisać, że użytkownik może wybrać portfele oraz dowolny zakres czasu.
- Opisać, że system pozwala porównać zwrot inwestycji wybranych portfeli w czasie.
- Wspomnieć, że po wskazaniu konkretnej daty można podejrzeć strukturę portfela, czyli skład pozycji i ich udział w portfelu.

**Najważniejszy przekaz:**

Portfolio umożliwia porównanie skuteczności konkretnych portfeli oraz sprawdzenie, z jakich pozycji składały się w wybranym momencie.

## 4. Zakładka Transaction

**Co opisać w tym miejscu:**

- Opisać tę zakładkę jako widok szczegółowej historii decyzji wykonanych przez system.
- Wyjaśnić, że dla każdego portfela można sprawdzić:
  - datę transakcji,
  - typ operacji, czyli kupno albo sprzedaż,
  - ticker spółki,
  - cenę,
  - liczbę akcji.
- Podkreślić, że ten widok pozwala prześledzić, kiedy i jak zmieniał się skład portfela.

**Najważniejszy przekaz:**

Transaction pokazuje konkretne działania systemu, czyli faktyczne kupna i sprzedaże wykonane w trakcie symulacji.

## 5. Zakładka Stocks

**Co opisać w tym miejscu:**

- Wyjaśnić, że zakładka Stocks koncentruje się na analizie pojedynczych spółek.
- Napisać, że użytkownik może wybrać ticker oraz zakres czasu i zobaczyć przebieg ceny akcji.
- Opisać, że na wykresie można zaznaczyć momenty, w których wybrany portfel kupował albo sprzedawał daną spółkę.
- Podkreślić, że pozwala to połączyć decyzje portfela z rzeczywistym ruchem ceny akcji.

**Najważniejszy przekaz:**

Stocks pozwala sprawdzić, jak decyzje kupna i sprzedaży wyglądały na tle wykresu ceny konkretnej spółki.

## 6. Zakładka Archetype Results

**Co opisać w tym miejscu:**

- Opisać tę zakładkę jako widok analizy wyników wewnątrz pojedynczych archetypów.
- Wyjaśnić, że dla dowolnego okresu inwestycyjnego można sprawdzić zwroty portfeli należących do danego archetypu.
- Napisać, że wyniki są prezentowane z podziałem na wartości parametrów strategii:
  - `top_m_share`,
  - `investment_time_days`,
  - `rebalance_time_share`.
- Podkreślić, że zakładka pomaga ocenić, które ustawienia parametrów działały najlepiej w obrębie danego typu strategii.

**Najważniejszy przekaz:**

Archetype Results umożliwia analizę wpływu parametrów strategii na wyniki portfeli w ramach konkretnego archetypu.

## 7. Zakładka All Results

**Co opisać w tym miejscu:**

- Wyjaśnić, że zakładka All Results służy do zbiorczego porównywania wyników wszystkich archetypów.
- Napisać, że dla dowolnego okresu można analizować:
  - medianę zwrotu,
  - średni zwrot,
  - Downside Information Ratio,
  - wyniki pojedynczych portfeli wewnątrz archetypów.
- Wspomnieć, że widok pozwala porównywać archetypy między sobą oraz sprawdzać rozrzut wyników portfeli w ramach tych archetypów.
- Dodać, że frontend pokazuje również wykres średniego zwrotu w porównaniu do wartości poszczególnych metryk.

**Najważniejszy przekaz:**

All Results daje najbardziej ogólny obraz skuteczności strategii i pozwala porównać archetypy na podstawie kilku miar wyników.

## 9. Podsumowanie rozdziału

**Co opisać w tym miejscu:**

- Krótko podsumować, że frontend pozwala użytkownikowi kontrolować symulację i interpretować jej wyniki.
- Podkreślić, że najważniejszą zaletą interfejsu jest połączenie konfiguracji, wyników portfeli, historii transakcji i wykresów cen w jednym miejscu.
- Zakończyć stwierdzeniem, że frontend przekształca dane generowane przez backend w czytelne widoki analityczne.

**Propozycja zdania końcowego:**

Frontend stanowi praktyczną warstwę analizy systemu, ponieważ pozwala uruchamiać symulacje, obserwować decyzje inwestycyjne oraz porównywać skuteczność portfeli i archetypów w różnych okresach czasu.