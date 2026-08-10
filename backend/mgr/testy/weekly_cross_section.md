# Weekly Cross Section

Weekly Cross Section sprawdza, czy model dobrze szereguje spółki dostępne w tym samym tygodniu. To jest podstawowy, relatywny test jakości score: nie pytamy jeszcze, czy rynek jako całość urośnie, tylko czy spółki z wyższym score zachowują się później lepiej niż spółki z niższym score w tym samym przekroju tygodnia.

Najpierw porównujemy samą korelację score z późniejszym zwrotem dla trzech timeframe'ów: short-term, medium-term i long-term. Dopiero po tym sprawdzamy, co ta korelacja pozwala praktycznie pokazać: czy wybieranie najlepszych spółek z rankingu działa i czy wynik pogarsza się wraz ze spadkiem pozycji w rankingu.

## 1. Czy score porządkuje spółki w przekroju tygodnia?

Test Information Coefficient mierzy, czy dla każdego tygodnia score rzeczywiście porządkuje spółki zgodnie z ich późniejszym zwrotem. Dla każdego horyzontu inwestycyjnego osobno liczona jest korelacja przekrojowa w każdym tygodniu, a potem średnia z tych tygodniowych korelacji.

Innymi słowy: sprawdzamy, czy w danym tygodniu spółki z wyższym score miały potem wyższy zwrot niż spółki z niższym score. Na wykresach są trzy metryki:

- Pearson IC: klasyczna korelacja Pearsona między score a przyszłym zwrotem,
- Spearman IC: korelacja rang, czyli test tego, czy kolejność spółek według score zgadza się z kolejnością późniejszych zwrotów,
- Score Percentile Pearson IC: korelacja Pearsona między tygodniowym percentylem score a przyszłym zwrotem; to wersja stabilniejsza względem skali score, bo patrzy na względną pozycję spółki w danym tygodniu.

Porównanie robimy osobno dla trzech horyzontów:

**PNG:** `backend/data/results/weekly_cross_section/information_coefficient/short_term_14d_weekly_information_coefficient.png`

**PNG:** `backend/data/results/weekly_cross_section/information_coefficient/medium_term_50d_weekly_information_coefficient.png`

**PNG:** `backend/data/results/weekly_cross_section/information_coefficient/long_term_200d_weekly_information_coefficient.png`

Dla krótszych horyzontów mamy naturalnie więcej obserwacji, ale sama liczba obserwacji nie wystarcza. Kluczowe jest to, czy średnia korelacja jest dodatnia, czy zachowuje stabilny znak i czy nie wygląda jak przypadkowy szum wokół zera.

W praktyce short-term i medium-term nie pokazują wystarczająco dobrej, stabilnej korelacji. To oznacza, że w krótkim i średnim terminie score nie porządkuje spółek wystarczająco konsekwentnie, aby na tej podstawie budować dalszą analizę selekcji.

Dla long-term 200d wynik wygląda najlepiej: korelacja jest dodatnia i bardziej uporządkowana. Dla zakresu long-term 21-35 tygodni średnie wartości wyniosły:

- Pearson IC: ok. 0.195,
- Spearman IC: ok. 0.183,
- Score Percentile Pearson IC: ok. 0.199.

Interpretacja: dla horyzontu około 200 dni pojawia się dodatnia i dość stabilna zależność. Score nie przewiduje dokładnie przyszłych zwrotów punkt po punkcie, ale statystycznie pomaga ustawiać spółki w lepszej kolejności w obrębie tego samego tygodnia.

## 2. Czy kupowanie Top N najwyżej ocenionych spółek działa?

Top N Selection pokazuje, jak zmienia się roczny zwrot strategii kupującej co tydzień Top N najwyżej ocenionych spółek. Dla każdego horyzontu inwestycyjnego brane są wszystkie dostępne tygodnie startowe. W każdym takim tygodniu spółki są sortowane według score, wybierane jest Top N, liczony jest ich średni przyszły zwrot, a następnie wyniki są uśredniane i annualizowane.

**PNG:** `backend/data/results/weekly_cross_section/top_n_selection/long_term_200d_top_n_annualized_return.png`

Top 18 pełni rolę benchmarku, ponieważ oznacza kupno wszystkich 18 spółek po równo. Pozostałe linie pokazują coraz bardziej selektywne strategie: Top 14, Top 9, Top 7, aż do Top 1.

Interpretacja tego kroku jest prosta: im bardziej elitarna selekcja, tym wyższy średni zwrot. Top 1 daje najwyższy wynik, ale jest najbardziej wrażliwy na pojedyncze trafienia. Top 18 jest najstabilniejsze, ale najbliższe benchmarkowi całego koszyka.

To jest praktyczny skutek dodatniego Information Coefficient dla long-term. Skoro ranking ma dodatni związek z późniejszym zachowaniem spółek, to górne koszyki rankingu powinny przeciętnie zachowywać się lepiej. Wykres Top N pokazuje właśnie ten efekt w formie prostej strategii selekcyjnej.

## 3. Czy wynik spada wraz z pogarszaniem pozycji w rankingu?

Rank Bucket Returns rozbija ranking tygodniowy na 18 osobnych koszyków: Rank 1, Rank 2, ..., Rank 18. Rank 1 oznacza najlepszą spółkę według score w danym tygodniu, Rank 18 najniżej ocenioną. Dla każdego koszyka liczony jest średni przyszły zwrot dla różnych horyzontów, a następnie annualizowany.

**PNG:** `backend/data/results/weekly_cross_section/rank_bucket_returns/long_term_200d_rank_bucket_annualized_return_lines.png`

**PNG:** `backend/data/results/weekly_cross_section/rank_bucket_returns/long_term_200d_rank_bucket_annualized_return_average.png`

Ten test odpowiada na pytanie: czy zwrot spada wraz z pogarszaniem się pozycji w rankingu? Idealny model dawałby niemal monotoniczną funkcję malejącą: Rank 1 najlepszy, Rank 2 trochę słabszy, itd. Wtedy Spearman między score/rankiem a przyszłym zwrotem byłby bardzo wysoki.

Wyniki dla zakresu 21-35 tygodni:

- Rank 1: ok. 60.7% rocznie,
- średnia dla Rank 1-6: ok. 29.6% rocznie,
- średnia dla Rank 7-12: ok. 18.8% rocznie,
- średnia dla Rank 13-18: ok. 11.0% rocznie.

Funkcja nie jest idealnie malejąca. Widać lokalne zaburzenia, np. niektóre dalsze rankingi potrafią wypaść lepiej niż bliższe. Mimo tego ogólny gradient jest wyraźny: górne pozycje rankingu mają przeciętnie wyższy zwrot niż dolne.

## Interpretacja całości

Weekly Cross Section najpierw porównuje korelację dla short-term, medium-term i long-term. Ten etap pokazuje, że użyteczna siła przekrojowa modelu pojawia się przede wszystkim w horyzoncie long-term 200d, czyli w zakresie 21-35 tygodni.

Dopiero na tej podstawie patrzymy na Top N Selection i Rank Bucket Returns. Te testy pokazują, co dodatnia korelacja oznacza praktycznie: najbardziej selektywne koszyki osiągają wyższe zwroty, a górna część rankingu jest wyraźnie mocniejsza od dolnej.
