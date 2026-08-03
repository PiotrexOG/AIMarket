# Plan rozdzialu: Wstep

## 1. Aktualnosc tematu

**Co opisac w tym miejscu:**

- Rozpoczac od tego, ze podejmowanie decyzji inwestycyjnych jest trudne, bo rynek finansowy jest zmienny, niepewny i zalezy od wielu czynnikow jednoczesnie.
- Wspomniec, ze inwestor musi analizowac dane cenowe, dane fundamentalne, newsy, rekomendacje analitykow oraz sytuacje innych spolek.
- Zaznaczyc, ze liczba informacji jest duza, a ich interpretacja czesto niejednoznaczna.
- Wprowadzic LLM jako aktualny kierunek rozwoju narzedzi analitycznych: modele jezykowe potrafia pracowac z tekstem, streszczac informacje i laczyc rozne przeslanki.
- Pokazac, ze w finansach jest to szczegolnie interesujace, bo czesc waznych informacji ma charakter opisowy, np. newsy, komentarze i komunikaty.

**Najwazniejszy przekaz:**

Temat jest aktualny, poniewaz wspolczesna analiza inwestycyjna wymaga laczenia danych liczbowych i tekstowych, a LLM daja nowe mozliwosci porzadkowania informacji opisowych.

## 2. Uzasadnienie problemu

**Co opisac w tym miejscu:**

- Wyjasnic, ze samo wspomaganie decyzji inwestycyjnych jest trudne do jednoznacznej oceny, bo zalezy od inwestora i jego sposobu wykorzystania informacji.
- Dlatego w pracy przyjeto mocniejszy wariant badania: sprawdzenie, czy oceny spolek moga zostac przeksztalcone w konkretne decyzje portfelowe.
- Podkreslic, ze decyzje sa wykonywane w kontrolowanym srodowisku badawczym, a nie w rzeczywistym obrocie gieldowym.
- Wyjasnic, ze takie podejscie pozwala mierzyc wyniki bardziej obiektywnie: przez ranking spolek, transakcje, sklad portfela, zwrot i porownanie z punktem odniesienia.
- Zaznaczyc, ze celem nie bylo dobranie okresu, spolek ani parametrow pod maksymalizacje wyniku.

**Najwazniejszy przekaz:**

Praca traktuje automatyzacje decyzji jako sposob sprawdzenia, czy oceny tworzone z wykorzystaniem LLM maja mierzalna wartosc inwestycyjna.

## 3. Charakter walidacji

**Co opisac w tym miejscu:**

- Doprecyzowac, ze badanie nie polegalo na klasycznym doborze historycznego okresu pod jak najlepszy wynik.
- Opisac podejscie jako zblizone do walidacji "prawie na zywo": w kolejnych momentach wykonywano oceny spolek wzgledem siebie, a dopiero po uplywie odpowiedniego czasu sprawdzano, jak te oceny wypadly.
- Wspomniec, ze taka procedura ogranicza ryzyko nadmiernego dopasowania do znanego z gory wyniku.
- Zaznaczyc, ze mimo tego nadal pozostaja typowe ograniczenia badan inwestycyjnych, np. ograniczona liczba obserwacji, zmiennosc rynku i potrzeba dalszej walidacji.

**Najwazniejszy przekaz:**

Walidacja miala charakter sekwencyjny i zblizony do oceny wykonywanej w czasie rzeczywistym, a nie do jednorazowego dopasowania strategii do historii.

## 4. Problem badawczy

**Propozycja sformulowania problemu badawczego:**

Czy oceny spolek tworzone na podstawie danych finansowych, technicznych, informacyjnych oraz interpretacji tekstu przez modele jezykowe moga zostac wykorzystane do automatycznego generowania decyzji inwestycyjnych w kontrolowanym srodowisku symulacyjnym?

**Pytania pomocnicze:**

- Czy dane liczbowe i tekstowe mozna przeksztalcic w porownywalna ocene spolki?
- Czy ranking spolek moze byc podstawa decyzji kupna, sprzedazy lub utrzymania pozycji?
- Czy oceny wykonywane sekwencyjnie zachowuja zwiazek z pozniejszymi wynikami spolek?
- Jakie ograniczenia ma podejscie wykorzystujace LLM w analizie inwestycyjnej?

**Najwazniejszy przekaz:**

Praca bada przejscie od interpretacji informacji do konkretnych, testowalnych decyzji portfelowych.

## 5. Cel pracy

**Propozycja celu glownego:**

Celem pracy jest opracowanie i ocena systemu, ktory laczy dane finansowe, dane rynkowe oraz interpretacje tekstu przez modele jezykowe w celu generowania ocen spolek, a nastepnie wykorzystuje te oceny do podejmowania decyzji w symulowanym portfelu inwestycyjnym.

**Cele szczegolowe:**

- Omowienie podstawowych pojec zwiazanych z decyzjami inwestycyjnymi, portfelem i rankingiem spolek.
- Przeglad podejsc ilosciowych, machine learningu, NLP i LLM w finansach.
- Zaprojektowanie procesu przygotowania danych i oceny spolek.
- Przeksztalcenie ocen w ranking i decyzje portfelowe.
- Sprawdzenie wynikow ocen i decyzji po uplywie odpowiedniego horyzontu.
- Wskazanie ograniczen oraz mozliwych kierunkow dalszego rozwoju.

**Najwazniejszy przekaz:**

Celem jest sprawdzenie koncepcji automatycznego przejscia od danych i interpretacji tekstu do decyzji portfelowych, bez traktowania wynikow jako gotowej rekomendacji inwestycyjnej.

## 6. Zakres i zalozenia pracy

**Co opisac w tym miejscu:**

- Praca obejmuje czesc teoretyczna, projektowa, implementacyjna i eksperymentalna.
- Badanie dotyczy symulowanego portfela, a nie realnego wykonywania transakcji.
- Decyzje powstaja na podstawie ocen spolek i przyjetych regul, a nie na podstawie recznej selekcji.
- LLM jest traktowany jako narzedzie interpretacji i porzadkowania informacji, a nie jako gwarant poprawnej prognozy.
- Wyniki nalezy oceniac wzgledem benchmarku lub innego punktu odniesienia.
- Praca nie przesadza o mozliwosci natychmiastowego uzycia podejscia w realnym inwestowaniu, ale po dalszej walidacji i dopracowaniu ograniczen moze ono stanowic podstawe do przyszlych zastosowan finansowych.

**Poza zakresem pracy:**

- Realne transakcje gieldowe.
- Doradztwo inwestycyjne.
- Budowa modelu jezykowego od podstaw.
- Pelne porownanie wszystkich dostepnych modeli LLM.
- Gwarancja skutecznosci inwestycyjnej w przyszlosci.

**Najwazniejszy przekaz:**

Praca ma charakter badawczy i prototypowy, ale sprawdza podejscie, ktore po dalszej weryfikacji mogloby byc rozwijane w kierunku praktycznych zastosowan finansowych.

## 8. Proponowany uklad gotowego wstepu

```text
Aktualnosc tematu
        |
        v
Trudnosc decyzji inwestycyjnych
        |
        v
LLM jako narzedzie interpretacji informacji
        |
        v
Problem badawczy
        |
        v
Cel pracy
        |
        v
Charakter walidacji prawie na zywo
        |
        v
Zakres i zalozenia
```

## 9. Propozycja krotkiego akapitu otwierajacego

Wspolczesny rynek finansowy jest srodowiskiem o wysokiej zmiennosci i duzej liczbie dostepnych informacji. Decyzje inwestycyjne wymagaja laczenia danych cenowych, danych fundamentalnych, informacji prasowych oraz opinii analitykow. Wraz z rozwojem duzych modeli jezykowych pojawia sie pytanie, czy narzedzia te moga nie tylko wspierac interpretacje informacji, ale rowniez pomagac w tworzeniu uporzadkowanych ocen spolek. W niniejszej pracy zagadnienie to potraktowano w sposob eksperymentalny: zamiast ograniczac sie do samego wspomagania inwestora, zbadano mozliwosc przeksztalcenia ocen spolek w automatyczne decyzje wykonywane w symulowanym portfelu inwestycyjnym.

## 10. Propozycja zdania zamykajacego wstep

Tak zdefiniowany zakres pozwala potraktowac wspomaganie decyzji inwestycyjnych jako testowalny proces przechodzenia od danych, przez ocene spolek, do decyzji portfelowych, przy jednoczesnym zachowaniu ostroznosci wobec ograniczen modeli jezykowych, danych rynkowych i samej symulacji.
