# Plan rozdzialu: Przeglad literatury i istniejacych podejsc

## 1. Cel i zakres rozdzialu

**Co opisac w tym miejscu:**

- Wyjasnic, ze ten rozdzial ma pokazac najwazniejsze kierunki badan zwiazane z automatyczna analiza inwestycyjna.
- Zaznaczyc, ze rozdzial nie ma byc pelnym przegladem calej literatury finansowej, tylko krotkim omowieniem podejsc najblizszych tematyce pracy.
- Pokazac logiczna kolejnosc rozwoju metod:
  - klasyczne modele ilosciowe,
  - machine learning w finansach,
  - NLP i analiza tekstu finansowego,
  - LLM w analizie tekstu i wspomaganiu decyzji,
  - ograniczenia LLM.
- Napisac, ze rozdzial powinien miec charakter selektywny: lepiej omowic mniej prac, ale pokazac ich znaczenie dla tematu.

**Najwazniejszy przekaz:**

Rozdzial powinien pokazac, ze nowoczesne podejscia inwestycyjne rozwijaly sie od modeli opartych glownie na danych liczbowych do metod, ktore potrafia wykorzystywac takze tekst i informacje opisowe.

**Czego nie rozwijac za bardzo:**

- Nie trzeba omawiac wielu odmian kazdego modelu.
- Nie trzeba wyprowadzac wzorow.
- Nie trzeba jeszcze opisywac wlasnego rozwiazania.

## 2. Klasyczne podejscia ilosciowe

**Co opisac w tym miejscu:**

- Krotko wyjasnic, ze klasyczne podejscia ilosciowe probuja opisac decyzje inwestycyjne za pomoca liczb: oczekiwanego zwrotu, ryzyka, korelacji, zmiennosci i cech spolek.
- Przywolac Markowitza jako punkt wyjscia nowoczesnej teorii portfelowej:
  - inwestor nie powinien patrzec tylko na pojedyncze aktywo,
  - wazne jest, jak aktywa zachowuja sie razem w portfelu,
  - dywersyfikacja moze ograniczac ryzyko.
- Wspomniec o modelach faktorowych, szczegolnie Fama-French:
  - zwroty spolek mozna probowac tlumaczyc przez zestaw czynnikow,
  - wazne moga byc cechy takie jak wielkosc spolki, wycena, rentownosc czy momentum.
- Krotko wspomniec o momentum jako przykladzie podejscia rankingowego: spolki sa porownywane na podstawie historycznych wynikow.
- Pokazac ograniczenie klasycznych podejsc: dobrze porzadkuja myslenie o rynku, ale zwykle upraszczaja rzeczywistosc i skupiaja sie glownie na danych liczbowych.

**Najwazniejszy przekaz:**

Klasyczne modele ilosciowe stworzyly fundament analizy portfeli i porownywania spolek, ale nie byly projektowane do interpretacji zlozonych informacji tekstowych.

**Prace, ktore warto przywolac:**

- Harry Markowitz, "Portfolio Selection", Journal of Finance, 1952: https://doi.org/10.1111/j.1540-6261.1952.tb01525.x
- Eugene F. Fama, Kenneth R. French, "Common risk factors in the returns on stocks and bonds", Journal of Financial Economics, 1993: https://doi.org/10.1016/0304-405X(93)90023-5
- Narasimhan Jegadeesh, Sheridan Titman, "Returns to Buying Winners and Selling Losers", Journal of Finance, 1993: https://doi.org/10.2307/2328882

**Czego nie rozwijac za bardzo:**

- Nie trzeba szczegolowo opisywac CAPM, jezeli brakuje miejsca.
- Nie trzeba omawiac wielu faktorow ani problemu factor zoo.
- Wystarczy pokazac, ze literatura ilosciowa wprowadzila idee portfela, ryzyka, rankingu i porownywania spolek.

## 3. Machine learning w finansach

**Co opisac w tym miejscu:**

- Wyjasnic, ze machine learning jest naturalnym rozszerzeniem klasycznych modeli, bo pozwala analizowac wiecej zmiennych i bardziej zlozone zaleznosci.
- Napisac, ze w finansach ML moze byc wykorzystywany m.in. do:
  - prognozowania zwrotow,
  - klasyfikacji spolek,
  - wykrywania nieliniowych zaleznosci,
  - laczenia wielu cech w jedna ocene.
- Przywolac prace Gu, Kelly i Xiu jako jedna z najwazniejszych prac pokazujacych zastosowanie ML w empirycznym asset pricingu.
- Podkreslic, ze ML nie rozwiazuje automatycznie problemu przewidywania rynku:
  - dane finansowe sa zaszumione,
  - zaleznosci moga byc niestabilne,
  - latwo o overfitting,
  - bardzo wazna jest walidacja poza proba.
- Wspomniec, ze ML dobrze pasuje do danych liczbowych, ale sam z siebie nie wystarcza do pelnej interpretacji newsow, raportow i opinii analitykow.

**Najwazniejszy przekaz:**

Machine learning pozwala budowac bardziej elastyczne modele inwestycyjne, ale wymaga ostroznej walidacji, bo w finansach latwo pomylic rzeczywisty sygnal z przypadkowym szumem.

**Prace, ktore warto przywolac:**

- Shihao Gu, Bryan Kelly, Dacheng Xiu, "Empirical Asset Pricing via Machine Learning", Review of Financial Studies, 2020: https://doi.org/10.1093/rfs/hhaa009
- Nusret Cakici, Christian Fieberg, Daniel Metko, Adam Zaremba, "Machine learning goes global: Cross-sectional return predictability in international stock markets", Journal of Economic Dynamics and Control, 2023: https://doi.org/10.1016/j.jedc.2023.104725

**Czego nie rozwijac za bardzo:**

- Nie trzeba porownywac wszystkich algorytmow ML.
- Nie trzeba opisywac matematyki drzew, sieci neuronowych ani regularyzacji.
- Wystarczy pokazac, dlaczego ML stal sie wazny w analizie inwestycyjnej i jakie ma ograniczenia.

## 4. NLP i analiza tekstu finansowego

**Co opisac w tym miejscu:**

- Wyjasnic, ze rynek reaguje nie tylko na dane liczbowe, ale tez na informacje tekstowe: newsy, raporty, komunikaty spolek, wypowiedzi zarzadow i rekomendacje analitykow.
- Opisac, ze przed era LLM tekst finansowy analizowano glownie przez:
  - slowniki sentymentu,
  - liczenie slow pozytywnych i negatywnych,
  - klasyfikatory NLP,
  - modele wyspecjalizowane dla jezyka finansowego.
- Przywolac Tetlocka jako przyklad pracy pokazujacej zwiazek tonu mediow z rynkiem.
- Przywolac Loughrana i McDonalda jako przyklad pracy pokazujacej, ze ogolne slowniki nie zawsze dobrze dzialaja w finansach.
- Przywolac FinBERT jako przyklad modelu jezykowego dostosowanego do finansowej analizy sentymentu.
- Pokazac ograniczenie starszych metod NLP: potrafia klasyfikowac tekst, ale czesto gorzej radza sobie z szerszym kontekstem, niuansami i laczeniem wielu informacji naraz.

**Najwazniejszy przekaz:**

Analiza tekstu finansowego pokazala, ze newsy i raporty moga zawierac sygnal istotny dla rynku, ale skuteczna interpretacja takiego tekstu wymaga modeli rozumiejacych kontekst finansowy.

**Prace, ktore warto przywolac:**

- Paul C. Tetlock, "Giving Content to Investor Sentiment: The Role of Media in the Stock Market", Journal of Finance, 2007: https://doi.org/10.1111/j.1540-6261.2007.01232.x
- Tim Loughran, Bill McDonald, "When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks", Journal of Finance, 2011: https://doi.org/10.1111/j.1540-6261.2010.01625.x
- Dogu Araci, "FinBERT: Financial Sentiment Analysis with Pre-trained Language Models", 2019: https://arxiv.org/abs/1908.10063

**Czego nie rozwijac za bardzo:**

- Nie trzeba omawiac mediow spolecznosciowych, jezeli rozdzial ma byc krotki.
- Nie trzeba robic przegladu wszystkich modeli NLP.
- Wystarczy pokazac przejscie od prostych slownikow do modeli domenowych.

## 5. LLM w analizie finansowej

**Co opisac w tym miejscu:**

- Wyjasnic, ze duze modele jezykowe sa nowszym etapem rozwoju NLP, poniewaz potrafia wykonywac wiele zadan tekstowych na podstawie instrukcji.
- Wskazac, ze w finansach LLM moga byc wykorzystywane do:
  - streszczania newsow i raportow,
  - klasyfikacji sentymentu,
  - oceny znaczenia informacji dla spolki,
  - porownywania argumentow za i przeciw,
  - wspomagania komentarza analitycznego.
- Przywolac BloombergGPT jako przyklad duzego modelu trenowanego z uwzglednieniem danych finansowych.
- Przywolac FinGPT jako przyklad otwartego podejscia do finansowych modeli jezykowych.
- Przywolac prace Lopez-Liry i Tanga, ktora bada, czy ChatGPT moze oceniac znaczenie newsow dla przyszlych ruchow cen.
- Przywolac prace Chen, Kelly i Xiu, ktora laczy duze modele jezykowe z przewidywaniem oczekiwanych zwrotow na podstawie tekstu.
- Zaznaczyc, ze te prace sa wazne, bo nie traktuja tekstu tylko jako prostego sentymentu, ale jako zrodlo bardziej zlozonej informacji ekonomicznej.

**Najwazniejszy przekaz:**

LLM sa obiecujace w finansach, bo potrafia interpretowac tekst i laczyc wiele informacji opisowych, ale ich zastosowanie powinno byc traktowane jako wsparcie analizy, a nie gwarancja poprawnej decyzji.

**Prace, ktore warto przywolac:**

- Shijie Wu et al., "BloombergGPT: A Large Language Model for Finance", 2023: https://arxiv.org/abs/2303.17564
- Hongyang Yang, Xiao-Yang Liu, Christina Dan Wang, "FinGPT: Open-Source Financial Large Language Models", 2023: https://arxiv.org/abs/2306.06031
- Alejandro Lopez-Lira, Yuehua Tang, "Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models", SSRN / Journal of Financial Economics, 2023-2026: https://doi.org/10.2139/ssrn.4412788
- Yifei Chen, Bryan T. Kelly, Dacheng Xiu, "Expected Returns and Large Language Models", SSRN, 2023-2026: https://doi.org/10.2139/ssrn.4416687

**Czego nie rozwijac za bardzo:**

- Nie trzeba omawiac wielu ankiet i surveyow o FinLLM.
- Nie trzeba opisywac architektury transformerow.
- Nie trzeba cytowac zbyt wielu nowych preprintow, bo rozdzial moze sie wtedy rozrosnac.

## 6. Ograniczenia LLM

**Co opisac w tym miejscu:**

- Wyjasnic, ze LLM maja istotne ograniczenia, ktore w finansach sa szczegolnie wazne, bo bledna interpretacja moze prowadzic do zlych decyzji.
- Omowic najwazniejsze problemy:
  - halucynacje, czyli generowanie informacji brzmiacych wiarygodnie, ale niezgodnych z faktami,
  - brak pelnej deterministycznosci, czyli mozliwosc uzyskania roznych odpowiedzi w podobnych warunkach,
  - wrazliwosc na prompt, czyli zaleznosc wyniku od sposobu sformulowania instrukcji,
  - ryzyko interpretacyjne, czyli przecenienie albo pominiecie istotnych informacji,
  - problem aktualnosci danych,
  - ryzyko zapamietania informacji z danych treningowych.
- Podkreslic, ze z tego powodu odpowiedzialne uzycie LLM wymaga:
  - dobrze przygotowanych danych wejsciowych,
  - jasnych instrukcji,
  - zapisu wynikow,
  - walidacji na danych historycznych,
  - oddzielenia interpretacji tekstu od ostatecznej reguly decyzyjnej.

**Najwazniejszy przekaz:**

LLM moga byc bardzo pomocne w analizie informacji finansowych, ale nie sa deterministycznym ani nieomylnym narzedziem prognostycznym.

**Prace, ktore warto przywolac:**

- Ziwei Ji et al., "Survey of Hallucination in Natural Language Generation", ACM Computing Surveys, 2023: https://doi.org/10.1145/3571730
- Lei Huang et al., "A Survey on Hallucination in Large Language Models", arXiv, 2023-2024: https://doi.org/10.48550/arXiv.2311.05232
- Alejandro Lopez-Lira, Yuehua Tang, Mingyin Zhu, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?", SSRN, 2025-2026: https://doi.org/10.2139/ssrn.5217505

**Czego nie rozwijac za bardzo:**

- Nie trzeba robic osobnego rozdzialu o etyce AI.
- Nie trzeba omawiac wszystkich typow bledow modeli jezykowych.
- Wystarczy skupic sie na ograniczeniach istotnych dla analizy finansowej.

## 7. Proponowany uklad gotowego rozdzialu

**Najwazniejszy przekaz:**

Rozdzial powinien byc selektywny i argumentacyjny: ma pokazac, dlaczego temat pracy jest osadzony w istniejacej literaturze, ale nie powinien zamienic sie w dluga liste publikacji.

**Proponowany schemat rozdzialu:**

```text
Klasyczne modele ilosciowe
        |
        v
Machine learning w finansach
        |
        v
NLP i tekst finansowy
        |
        v
LLM w analizie finansowej
        |
        v
Ograniczenia LLM
        |
        v
Wnioski dla dalszej czesci pracy
```

## 8. Najwazniejsze prace do zostawienia w bibliografii

| Obszar | Praca | Dlaczego warto zostawic |
|---|---|---|
| Teoria portfela | Markowitz (1952) | klasyczny punkt startowy dla myslenia o portfelu, ryzyku i dywersyfikacji |
| Modele faktorowe | Fama i French (1993) | podstawowa praca o czynnikach wyjasniajacych zwroty |
| Momentum | Jegadeesh i Titman (1993) | wazny przyklad rankingu spolek i efektu przekrojowego |
| Machine learning | Gu, Kelly i Xiu (2020) | jedna z kluczowych prac o ML w asset pricingu |
| Tekst finansowy | Tetlock (2007) | pokazuje znaczenie tonu mediow dla rynku |
| Slowniki finansowe | Loughran i McDonald (2011) | pokazuje, ze jezyk finansowy wymaga domenowego podejscia |
| NLP finansowe | FinBERT, Araci (2019) | dobry przyklad modelu dostosowanego do sentymentu finansowego |
| LLM finansowy | BloombergGPT (2023) | wazny przyklad duzego modelu domenowego dla finansow |
| Otwarte FinLLM | FinGPT (2023) | pokazuje otwarte podejscie do finansowych LLM |
| LLM i newsy | Lopez-Lira i Tang (2023-2026) | bezposrednio laczy LLM z interpretacja newsow i ruchem cen |
| LLM i zwroty | Chen, Kelly i Xiu (2023-2026) | laczy reprezentacje tekstu z prognozowaniem zwrotow |
| Ograniczenia LLM | Ji et al. (2023) | dobre zrodlo do opisania halucynacji |

## 9. Podsumowanie rozdzialu

**Co opisac w tym miejscu:**

- Zebrac, ze literatura pokazuje przejscie od danych liczbowych do danych tekstowych.
- Podkreslic, ze klasyczne modele i ML pomagaja analizowac cechy spolek, ale tekst wymaga osobnych metod.
- Napisac, ze NLP i LLM rozszerzaja mozliwosci analizy, bo pozwalaja interpretowac newsy, raporty i komentarze.
- Zaznaczyc, ze mimo obiecujacych wynikow LLM wymagaja ostroznosci, bo sa podatne na halucynacje, zmiennosc odpowiedzi i zaleznosc od promptu.

**Propozycja zdania koncowego:**

Przeglad literatury pokazuje, ze nowoczesna analiza inwestycyjna coraz czesciej laczy dane ilosciowe z tekstem finansowym, jednak skuteczne wykorzystanie takich metod wymaga walidacji, kontroli ograniczen modeli oraz ostroznego oddzielenia sygnalu od szumu.
