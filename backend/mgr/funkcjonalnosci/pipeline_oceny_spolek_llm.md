# Pipeline oceny spolek z wykorzystaniem danych finansowych i LLM

## 1. Cel tej czesci systemu

Ta czesc aplikacji odpowiada za przygotowanie porownywalnej oceny spolek, ktora pozniej moze zostac wykorzystana przez portfele inwestycyjne. Jej zadaniem nie jest bezposrednie wykonanie transakcji, tylko przetworzenie wielu roznych danych o spolce w jedna uporzadkowana informacje: jak dana spolka wyglada sama w sobie oraz jak wypada na tle innych spolek analizowanych w tym samym momencie.

Najwazniejsza idea polega na tym, ze system nie opiera decyzji inwestycyjnej na jednym wskazniku, np. samej cenie albo samym P/E. Zamiast tego laczy dane techniczne, fundamentalne, wyceny, opinie analitykow i informacje newsowe. Dopiero po takim przygotowaniu dane trafiaja do modeli LLM, ktore zamieniaja je najpierw na ocene pojedynczej spolki, a nastepnie na ocene relatywna wzgledem innych spolek.

Efektem tego etapu jest liczbowy `score` dla kazdej spolki. Ten wynik moze byc pozniej uzywany w sposob deterministyczny przez rozne portfele, ktore maja wlasne parametry, np. inna liczbe wybieranych spolek, inny czas trwania cyklu inwestycyjnego albo inne zasady rebalancingu.

## 2. Pobieranie i przygotowanie danych wejsciowych

Pierwszym etapem pipeline'u jest zebranie danych, ktore opisuja spolke z kilku stron. System przygotowuje je przed wykonaniem oceny, poniewaz LLM nie powinien samodzielnie domyslac sie aktualnej sytuacji spolki ani korzystac z wiedzy spoza przekazanego kontekstu.

Do systemu trafiaja przede wszystkim:

- dane cenowe OHLCV, czyli open, high, low, close oraz wolumen,
- wskazniki techniczne wyliczone na podstawie historii cen i wolumenu,
- dane fundamentalne ze sprawozdan finansowych,
- dane kwartalne potrzebne do liczenia wartosci TTM i dynamiki rok do roku,
- daty i wartosci wynikow finansowych,
- szacunki EPS z poprzedniego i nastepnego okresu,
- oceny analitykow,
- newsy dotyczace spolki,
- streszczenia newsow,
- oceny waznosci newsow.

System dziala przy tym przyrostowo. Oznacza to, ze przed symulacja lub kolejnym krokiem czasowym sprawdza, czy ma juz potrzebne dane dla wymaganego zakresu. Jesli jakiegos fragmentu brakuje, pobierany albo liczony jest tylko brakujacy zakres, a nie caly zbior od poczatku. Jest to wazne przy dluzszych symulacjach, poniewaz kolejne uruchomienia moga korzystac z danych zapisanych wczesniej.

## 3. Dane cenowe OHLCV i warstwa techniczna

Dane OHLCV sa podstawa warstwy technicznej. Na ich podstawie system moze okreslic, w jakim stanie rynkowym znajduje sie spolka w danym momencie. Nie chodzi tylko o sama cene zamkniecia, ale rowniez o kierunek ruchu, zmiennosc, wolumen, pozycje ceny wzgledem srednich kroczacych oraz polozenie wzgledem wsparc i oporow.

Z danych cenowych wyprowadzane sa m.in. informacje dotyczace:

- krotkoterminowego momentum,
- poziomu RSI,
- polozenia w pasmach Bollingera,
- tempa zmiany ceny,
- relacji ceny do SMA20, SMA50 i SMA200,
- ukladu srednich kroczacych,
- sygnalow MACD,
- zmiennosci mierzonej przez ATR,
- relatywnego wolumenu,
- lokalnych stref wsparcia i oporu.

Nastepnie te liczby nie sa przekazywane dalej jako surowa tabela. W module `summaryMakers` sa zamieniane na bardziej zrozumiale opisy semantyczne. Przykladowo zamiast przekazac modelowi jedynie liczbe RSI, system moze opisac ja jako stan typu `OVERBOUGHT_EXTREME (72.6)`. Dzieki temu LLM otrzymuje jednoczesnie interpretacje i konkretna wartosc liczbowa.

## 4. Dane fundamentalne i sprawozdania finansowe

Rownolegle system przygotowuje dane fundamentalne. Sa one liczone na podstawie danych kwartalnych, przede wszystkim z ostatnich osmiu kwartalow. Taki zakres pozwala porownac biezace cztery kwartaly z poprzednimi czterema kwartalami i obliczyc wartosci TTM oraz zmiane rok do roku.

Na tym etapie system wylicza m.in.:

- przychody TTM,
- EPS TTM,
- wolne przeplywy pieniezne TTM,
- marze brutto, operacyjna i netto,
- wzrost przychodow rok do roku,
- wzrost EPS rok do roku,
- poziom zadluzenia,
- gotowke i ekwiwalenty gotowki,
- kapital wlasny,
- liczbe akcji,
- kwartalna dynamike wynikow wzgledem oczekiwan.

Z tych danych budowany jest opis kondycji biznesowej spolki. System rozroznia np. jakosc biznesu, zdrowie bilansu, generowanie gotowki, skale dzialalnosci, profil wzrostu i momentum wynikow kwartalnych. W efekcie LLM nie dostaje tylko listy pozycji ze sprawozdan, ale zwarte podsumowanie: czy spolka ma wysokie marze, czy generuje gotowke, czy rosnie, czy ma stabilny bilans oraz czy najnowsze wyniki wskazuja na poprawe albo pogorszenie.

## 5. Metryki wyceny

Osobnym krokiem jest obliczenie metryk wyceny, poniewaz dobra spolka nie zawsze musi byc dobra inwestycja przy kazdej cenie. Do policzenia tej czesci potrzebne sa zarowno dane fundamentalne, jak i aktualna cena akcji.

System wylicza m.in.:

- kapitalizacje rynkowa,
- enterprise value,
- P/E TTM,
- P/S TTM,
- P/B,
- wzrost EPS TTM rok do roku,
- PEG,
- relacje enterprise value do kapitalizacji.

Pozniej `ValuationSummaryBuilder` zamienia te liczby na opis wyceny. Przykladowo spolka moze zostac oznaczona jako `PREMIUM_VALUATION`, `DEEP_VALUE_DISCOUNT`, `GROWTH_OVERPRICED` albo `CASH_RICH_DISCOUNT`, ale przy tej etykiecie zachowywane sa konkretne wartosci, np. P/E, P/S, P/B lub PEG. Jest to istotne, bo LLM ma oceniac nie tylko kierunek narracji, ale rowniez skale przewartosciowania albo atrakcyjnosci wyceny.

## 6. Dane analitykow

Kolejna warstwa dotyczy ocen analitykow. System nie traktuje ich jako bezposredniego sygnalu kupna lub sprzedazy, tylko jako dodatkowy opis sentymentu rynkowego wokol spolki.

`AnalystConsensusBuilder` bierze aktualny rozklad rekomendacji oraz, jesli jest dostepny, poprzedni rozklad. Nastepnie zamienia go na kilka prostych informacji:

- ogolny stan konsensusu,
- sile przekonania analitykow,
- kierunek zmiany sentymentu,
- poziom polaryzacji opinii.

Dzieki temu system moze odroznic sytuacje, w ktorej wiekszosc analitykow jest zgodnie pozytywna, od sytuacji, w ktorej opinie sa mieszane albo pogarszaja sie wzgledem poprzedniego odczytu. Ta informacja trafia pozniej do LLM jako jeden z elementow oceny spolki.

## 7. Newsy, ich streszczenia i ocena waznosci

Newsy sa najbardziej zmiennym elementem pipeline'u, dlatego system nie przekazuje dalej wszystkich dostepnych informacji. Najpierw newsy sa agregowane i streszczane, a nastepnie oceniana jest ich waznosc. Ocena waznosci jest zapisywana jako liczba w skali od 0 do 10.

Pipeline newsowy mozna opisac w trzech krokach:

1. System pobiera newsy dotyczace spolki i grupuje je wedlug dat.
2. Dla kazdego dnia tworzone jest streszczenie najwazniejszych informacji.
3. Streszczenia sa oceniane pod wzgledem waznosci finansowej, dzieki czemu pozniej mozna wybrac tylko najbardziej istotne informacje.

Nastepnie `NewsNarrativeService` wybiera najwazniejsze newsy dla trzech horyzontow:

- `short_term_14d`,
- `medium_term_50d`,
- `long_term_200d`.

Wybieranie newsow nie polega tylko na sortowaniu po samej waznosci. System uwzglednia takze czas, ktory uplynal od publikacji informacji. Dla kazdego newsa liczony jest wynik selekcji, ktory laczy waznosc informacji z jej swiezoscia. Waznosc jest dodatkowo podnoszona do kwadratu, co premiuje naprawde istotne informacje, a funkcja wygaszania zmniejsza znaczenie starszych newsow.

W uproszczeniu oznacza to, ze system wybiera te informacje, ktore sa jednoczesnie wazne i wystarczajaco aktualne dla danego horyzontu. Inaczej zachowuje sie horyzont 14-dniowy, gdzie news musi byc bardzo swiezy, a inaczej horyzont 200-dniowy, gdzie wazne wydarzenie moze pozostac istotne przez dluzszy czas.

## 8. Rola `summaryMakers`

Moduly z katalogu `summaryMakers` sa mostem pomiedzy danymi liczbowymi a LLM. Ich zadaniem jest zamienienie roznych struktur danych na krotkie, ustandaryzowane opisy, ktore model moze latwo porownywac i interpretowac.

W tej warstwie dzialaja m.in.:

- `TechnicalSummaryBuilder`,
- `FundamentalSummaryBuilder`,
- `ValuationSummaryBuilder`,
- `AnalystConsensusBuilder`,
- `NewsNarrativeBuilder`.

Kazdy z tych builderow odpowiada za inny typ danych. Techniczny builder opisuje momentum, trend, zmiennosc i poziomy cenowe. Fundamentalny builder opisuje jakosc biznesu, bilans, gotowke i wzrost. Builder wyceny opisuje, czy cena jest niska, neutralna czy wymagajaca wzgledem fundamentow. Builder analitykow opisuje konsensus i jego zmiane. Builder newsow przekazuje wyselekcjonowane streszczenia informacji.

Wazne jest to, ze `summaryMakers` nie maja zastapic LLM. One przygotowuja dane w takiej formie, aby LLM nie musial sam odkrywac podstawowych zaleznosci z surowych tabel. Model dostaje juz dane przefiltrowane, nazwane i ulozone wedlug horyzontow.

## 9. Powstanie `structured_input.json`

Po przygotowaniu wszystkich czesci system buduje jeden obiekt wejsciowy dla konkretnej spolki i konkretnego momentu czasu. Ten obiekt jest zapisywany jako `structured_input.json`.

`structured_input.json` zawiera zwykle:

- ticker spolki,
- podsumowanie danych analitykow,
- podsumowanie techniczne,
- podsumowanie fundamentalne,
- podsumowanie aktualnej wyceny,
- narracje newsowa.

Ten plik pelni role kompletnego obrazu spolki w danym momencie. Jest to material wejsciowy do pierwszego promptu LLM. Mozna go traktowac jako uporzadkowana paczke dowodow: system pokazuje, co wiadomo o spolce, ale sama interpretacja inwestycyjna nastepuje dopiero w kolejnym kroku.

Zapis `structured_input.json` ma tez znaczenie praktyczne. Po pierwsze pozwala sprawdzic, jakie dane otrzymal model. Po drugie ulatwia powtarzanie lub debugowanie oceny. Po trzecie pozwala unikac ponownego generowania tych samych danych, jesli analiza dla danego tickera i timestampu juz istnieje.

## 10. Ocena pojedynczej spolki przez LLM

Nastepnie `structured_input.json` trafia do modelu LLM wraz z odpowiednim promptem systemowym. W tej aplikacji etap pojedynczej spolki jest realizowany przez `GEMINI_MASTER`. Jego zadaniem jest zamienienie przygotowanych opisow na ustandaryzowany wynik inwestycyjny.

Model zwraca `llm_output.json`, ktory zawiera ocene spolki w trzech horyzontach:

- `short_term_14d`,
- `medium_term_50d`,
- `long_term_200d`.

Dla kazdego horyzontu powstaja trzy glowne metryki:

- `score` - kierunkowa atrakcyjnosc spolki,
- `conv` - sila i trwalosc przekonania,
- `safe` - bezpieczenstwo strukturalne i odpornosc na spadki.

Oprocz liczb model tworzy tez opisowa synteze w formacie SWOT, czyli wskazuje mocne strony, slabosci, szanse i zagrozenia. Taki opis nie jest tylko komentarzem dla uzytkownika. Ponieważ modele językowe efektywniej przetwarzają i analizują tekst niż same dane liczbowe, synteza ta stanowi dla modelu bazę do późniejszego, jakościowego porównywania spółek między sobą.

Istotna jest tez spojnosc czasowa. Jesli system posiada poprzednia ocene tej samej spolki, przekazuje modelowi poprzednie wejscie i poprzednie wyjscie. Dzieki temu LLM nie powinien zmieniac oceny chaotycznie z tygodnia na tydzien, jesli dane nie ulegly istotnej zmianie. Wynik moze sie zmieniac, ale powinien wynikac z realnej poprawy albo pogorszenia danych.

## 11. Przejscie od oceny absolutnej do porownania spolek

Ocena pojedynczej spolki mowi, czy dana spolka wyglada dobrze sama w sobie. To jednak nie wystarcza do budowania portfela, poniewaz portfel musi wybrac najlepsze spolki sposrod dostepnych alternatyw.

Dlatego po wygenerowaniu `llm_output.json` dla wielu spolek system przechodzi do analizy przekrojowej, czyli cross-section. W tym etapie do modelu trafia koszyk kilku roznych spolek naraz. Model nie ocenia juz pojedynczej spolki w izolacji, tylko porownuje spolki miedzy soba w tym samym momencie i dla tych samych horyzontow.

Jest to kluczowy moment pipeline'u. System przestaje pytac: "czy ta spolka wyglada dobrze?", a zaczyna pytac: "jak ta spolka wypada wzgledem pozostalych spolek, ktore moge kupic w tym samym czasie?".

## 12. Cross-section i `llm_ranker.json`

Za etap porownania przekrojowego odpowiada osobny prompt i osobny mechanizm rankera. Dane wielu spolek sa laczone w koszyk, a model ma wykonac relatywna kalibracje wynikow.

Wynik jest zapisywany w katalogu `CROSS_SECTION` jako `llm_ranker.json` dla danego tygodnia lub danego timestampu. W pliku znajduja sie oceny dla trzech horyzontow:

- `short_term_14d`,
- `medium_term_50d`,
- `long_term_200d`.

Dla kazdej spolki i kazdego horyzontu model zapisuje zestaw relatywnych ocen:

- `relative_technical_strength`,
- `relative_fundamental_support`,
- `relative_valuation_sustainability`,
- `relative_structural_safety`,
- `relative_conviction`,
- `relative_asymmetry_profile`.

Te wartosci nie sa prostym przepisaniem wczesniejszych liczb z `llm_output.json`. Sa ponowna, relatywna interpretacja tego, jak spolka wypada na tle innych spolek w tym samym koszyku. Dzieki temu nawet jesli kilka spolek ma podobnie dobre wyniki absolutne, system moze wskazac, ktore z nich sa relatywnie silniejsze, bez sztucznego rozciagania skali od 0 do 10.

## 13. Usrednianie ocen relatywnych do wartosci `score`

Po zapisaniu `llm_ranker.json` system moze policzyc koncowy `score` spolki. Dla danego horyzontu bierze zestaw `relative_scores` i oblicza ich srednia.

W praktyce oznacza to, ze koncowy score jest srednia kilku wymiarow oceny relatywnej:

- technicznej sily,
- wsparcia fundamentalnego,
- trwalosci wyceny,
- bezpieczenstwa strukturalnego,
- przekonania,
- profilu asymetrii zysku do ryzyka.

Taka srednia daje jedna liczbe, ktora mozna latwo sortowac, porownywac i zapisywac w historii. Jednoczesnie liczba ta nie pochodzi z jednego wskaznika, tylko jest skompresowanym wynikiem wielowymiarowej analizy.

W dalszej czesci symulacji szczegolnie istotny jest horyzont `long_term_200d`, poniewaz portfele dzialaja w cyklach inwestycyjnych, a nie jako bardzo krotkoterminowy system transakcyjny. Dlatego decyzje portfelowe korzystaja glownie z dlugoterminowej oceny przekrojowej.

## 14. Dlaczego wynik musi byc relatywny

Relatywny scoring jest potrzebny, poniewaz portfel zawsze podejmuje decyzje w kontekscie dostepnego uniwersum spolek. Nawet jezeli spolka wyglada dobrze sama w sobie, moze byc mniej atrakcyjna niz inne spolki dostepne w tym samym tygodniu. Z drugiej strony spolka o umiarkowanej ocenie absolutnej moze byc najlepszym wyborem, jesli reszta koszyka wyglada slabiej.

Analiza cross-section pozwala wiec zamienic opis jakosciowy i liczbowy w ranking porownawczy. Dzieki temu system moze:

- porownywac spolki w tym samym momencie,
- oceniac, ktore spolki maja przewage wzgledem innych,
- zapisac tygodniowy obraz rynku,
- sprawdzac pozniej, czy wysokie score faktycznie wiazaly sie z lepszymi wynikami,
- wykorzystywac score w portfelach o roznych parametrach.

To rozdzielenie jest wazne: LLM pomaga w zlozonej interpretacji danych, ale pozniejsze decyzje portfela moga byc juz podejmowane deterministycznie na podstawie zapisanych liczb.

## 15. Wykorzystanie score przez portfele

Po obliczeniu score dla spolek dane moga zostac wykorzystane przez mechanizm decyzyjny portfeli. Portfel nie musi ponownie analizowac newsow, wskaznikow technicznych ani sprawozdan finansowych. Dostaje juz uporzadkowany wynik, ktory mowi, jak dana spolka wypada relatywnie w danym tygodniu.

Nastepnie kazdy portfel moze interpretowac te same score inaczej, w zaleznosci od swoich parametrow. Przykladowo jeden portfel moze wybierac tylko najwyzszy procent spolek, inny moze trzymac pozycje dluzej, a kolejny moze szybciej reagowac na pogorszenie pozycji spolki w rankingu.

Wazne jest to, ze po stronie portfela decyzje sa deterministyczne. Oznacza to, ze gdy znane sa:

- score spolek,
- aktualne ceny,
- obecny sklad portfela,
- parametry danego portfela,
- aktualny etap cyklu inwestycyjnego,

to decyzja o kupnie, sprzedazy albo utrzymaniu pozycji wynika juz z zasad systemu. LLM nie decyduje bezposrednio o transakcji. LLM przygotowuje porownywalna ocene rynku, a mechanizm portfela wykorzystuje ja wedlug okreslonych regul.

## 16. Skrot calego przeplywu

Caly pipeline tej czesci systemu mozna przedstawic w nastepujacych krokach:

1. System sprawdza, jakie dane sa potrzebne dla danego zakresu czasu i listy spolek.
2. Brakujace dane finansowe, cenowe, analityczne i newsowe sa pobierane lub aktualizowane.
3. Na podstawie OHLCV liczone sa wskazniki techniczne.
4. Na podstawie danych kwartalnych liczone sa fundamenty TTM i dynamiki rok do roku.
5. Na podstawie ceny i fundamentow liczone sa metryki wyceny, np. P/E, P/S, P/B i PEG.
6. Newsy sa streszczane, oceniane pod wzgledem waznosci i wybierane dla odpowiednich horyzontow.
7. `summaryMakers` zamieniaja dane liczbowe i tekstowe na zwarte opisy semantyczne.
8. Dla kazdej spolki powstaje `structured_input.json`.
9. `structured_input.json` trafia do LLM z promptem oceny pojedynczej spolki.
10. LLM zwraca `llm_output.json` z ocena dla horyzontow 14, 50 i 200 dni.
11. Wyniki wielu spolek sa laczone w koszyk do porownania cross-section.
12. Drugi prompt LLM porownuje spolki miedzy soba i tworzy relatywne oceny.
13. Wynik porownania jest zapisywany w `CROSS_SECTION` jako `llm_ranker.json`.
14. Dla kazdej spolki liczony jest `score` jako srednia wartosci `relative_scores`.
15. Portfele wykorzystuja score oraz swoje indywidualne parametry do deterministycznych decyzji inwestycyjnych.

## 17. Najwazniejszy przekaz

Ta czesc systemu sluzy do zamiany rozproszonych danych finansowych w porownywalny ranking spolek. Najpierw dane sa pobierane, liczone i opisywane, potem LLM ocenia pojedyncza spolke, a nastepnie inny prompt LLM porownuje wiele spolek wzgledem siebie. Dopiero z tego porownania powstaje score, ktory moze byc dalej wykorzystany przez portfele.

Dzieki temu system laczy dwa podejscia. Z jednej strony wykorzystuje LLM do interpretacji danych, ktore trudno prosto sprowadzic do jednej formuly, np. newsow, mieszanych sygnalow technicznych albo opisow fundamentalnych. Z drugiej strony koncowe decyzje portfeli opieraja sie juz na liczbach i parametrach, czyli moga byc wykonywane w sposob powtarzalny i deterministyczny.
