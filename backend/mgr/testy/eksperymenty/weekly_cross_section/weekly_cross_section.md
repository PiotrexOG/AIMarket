# Weekly Cross Section

Weekly Cross Section sprawdza, czy model dobrze szereguje spółki dostępne w tym samym tygodniu. To jest podstawowy, relatywny test jakości score.

Eksperyment w aktualnej konfiguracji jest liczony dla zakresu 21-35 tygodni. Liczba obserwacji maleje wraz z horyzontem: dla 21 tygodni było 51 tygodniowych próbek, a dla 35 tygodni 37 próbek. Jest to naturalne, bo im dłuższy horyzont przyszłego zwrotu, tym mniej dat startowych ma jeszcze kompletny przyszły okres zwrotu.

## 1. Czy kupowanie Top N najwyżej ocenionych spółek działa?

Pierwszy test, Top N Selection, pokazuje, jak zmienia się roczny zwrot strategii kupującej co tydzień Top N najwyżej ocenionych spółek. Dla każdego horyzontu inwestycyjnego brane są wszystkie dostępne tygodnie startowe. W każdym takim tygodniu spółki są sortowane według score, wybierane jest Top N, liczony jest ich średni przyszły zwrot, a następnie wyniki są uśredniane i annualizowane.

**PNG:** `backend/data/results/weekly_cross_section/top_n_selection/long_term_200d_top_n_annualized_return.png`

Top 18 pełni rolę benchmarku, ponieważ oznacza kupno wszystkich 18 spółek po równo. Pozostałe linie pokazują coraz bardziej selektywne strategie: Top 14, Top 9, Top 7, aż do Top 1.


Interpretacja tego pierwszego kroku jest prosta: im bardziej elitarna selekcja, tym wyższy średni zwrot. Top 1 daje najwyższy wynik, ale jest najbardziej wrażliwy na pojedyncze trafienia. Top 18 jest najstabilniejsze, ale najbliższe benchmarkowi całego koszyka.

Sam wykres Top N pokazuje, że wybieranie najlepszych według modelu historycznie dawało wyższą stopę zwrotu. Nie mówi jednak jeszcze, czy cały ranking jest uporządkowany sensownie, ani czy zależność między score i przyszłym zwrotem jest stabilna w kolejnych horyzontach.

## 2. Czy score rzeczywiście porządkuje spółki w przekroju tygodnia?

Test Information Coefficient mierzy, czy dla każdego tygodnia score rzeczywiście porządkuje spółki zgodnie z ich późniejszym zwrotem. Dla każdego horyzontu inwestycyjnego osobno liczona jest korelacja przekrojowa w każdym tygodniu, a potem średnia z tych tygodniowych korelacji.

**PNG:** `backend/data/results/weekly_cross_section/information_coefficient/long_term_200d_weekly_information_coefficient.png`

Innymi słowy: sprawdzamy, czy w danym tygodniu spółki z wyższym score miały potem wyższy zwrot niż spółki z niższym score. Na wykresie są trzy metryki:

- Pearson IC: klasyczna korelacja Pearsona między score a przyszłym zwrotem,
- Spearman IC: korelacja rang, czyli test tego, czy kolejność spółek według score zgadza się z kolejnością późniejszych zwrotów,
- Score Percentile Pearson IC: korelacja Pearsona między tygodniowym percentylem score a przyszłym zwrotem; to wersja stabilniejsza względem skali score, bo patrzy na względną pozycję spółki w danym tygodniu.

Jako że dla krótszego horyzontu mamy naturalnie więcej obserwacji niż dla dłuższych, średnia wartość tych korelacji nie jest jedyną oceną modelu, ale pokazuje, jak zmienia się jego skuteczność dla różnych długości trwania horyzontu.

Dla zakresu long-term 21-35 tygodni średnie wartości wyniosły:

- Pearson IC: ok. 0.195,
- Spearman IC: ok. 0.183,
- Score Percentile Pearson IC: ok. 0.199.

Interpretacja: dla horyzontu około 200 dni pojawia się dodatnia i dość stabilna zależność. W praktyce oznacza to, że score nie przewiduje dokładnie przyszłych zwrotów punkt po punkcie, ale statystycznie pomaga ustawiać spółki w lepszej kolejności w obrębie tego samego tygodnia.

To tłumaczy, dlaczego Top N Selection działa: najlepsze koszyki są lepsze nie tylko przypadkowo, ale dlatego, że w wielu tygodniach ranking modelu ma dodatni związek z późniejszym zachowaniem spółek.

## 3. Czy wynik spada wraz z pogarszaniem pozycji w rankingu?

Ostatni krok rozbija ranking tygodniowy na 18 osobnych koszyków: Rank 1, Rank 2, ..., Rank 18. Rank 1 oznacza najlepszą spółkę według score w danym tygodniu, Rank 18 najniżej ocenioną. Dla każdego koszyka liczony jest średni przyszły zwrot dla różnych horyzontów, a następnie annualizowany.

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

Weekly Cross Section potwierdza, że model ma użyteczną siłę przekrojową w horyzoncie 21-35 tygodni. Najpierw widać to w prostym wyniku strategii Top N: bardziej selektywne koszyki osiągają wyższe zwroty. Potem potwierdza to Information Coefficient: score ma dodatnią korelację z przyszłym zwrotem w obrębie tygodnia. Na końcu Rank Bucket Returns pokazuje, że górna część rankingu jest wyraźnie mocniejsza od dolnej.

Najważniejszy wniosek praktyczny jest taki, że model najlepiej sprawdza się jako narzędzie do wyboru najlepszych kandydatów w danym tygodniu. Jest mocny w identyfikowaniu czołówki rankingu, szczególnie Rank 1 i najbardziej selektywnych koszyków Top N, ale nie porządkuje idealnie całej listy od najlepszej do najgorszej.
