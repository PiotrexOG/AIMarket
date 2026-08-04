# Weekly Cross Section - Rank Bucket Returns

**Wyniki PNG**

- `backend/data/results/weekly_cross_section/rank_bucket_returns/long_term_200d_rank_bucket_annualized_return_lines.png`
- `backend/data/results/weekly_cross_section/rank_bucket_returns/long_term_200d_rank_bucket_annualized_return_average.png`

Test Rank Bucket Returns rozbija ranking tygodniowy na 18 osobnych koszyków: Rank 1, Rank 2, ..., Rank 18. Rank 1 oznacza najlepszą spółkę według score w danym tygodniu, Rank 18 najniżej ocenioną. Dla każdego koszyka liczony jest średni przyszły zwrot dla różnych horyzontów, a następnie annualizowany.

Ten test odpowiada na pytanie: czy zwrot spada wraz z pogarszaniem się pozycji w rankingu? Idealny model dawałby niemal monotoniczną funkcję malejącą: Rank 1 najlepszy, Rank 2 trochę słabszy, itd. Wtedy Spearman między score/rankiem a przyszłym zwrotem byłby bardzo wysoki.

Wyniki dla zakresu 21-35 tygodni:

- Rank 1: ok. 60.7% rocznie,
- średnia dla Rank 1-6: ok. 29.6% rocznie,
- średnia dla Rank 7-12: ok. 18.8% rocznie,
- średnia dla Rank 13-18: ok. 11.0% rocznie.

Funkcja nie jest idealnie malejąca. Widać lokalne zaburzenia, np. niektóre dalsze rankingi potrafią wypaść lepiej niż bliższe. Mimo tego ogólny gradient jest wyraźny: górne pozycje rankingu mają przeciętnie wyższy zwrot niż dolne.

Interpretacja: Rank Bucket Returns potwierdza wniosek z Top N Selection i Information Coefficient. Najwyżej oceniane spółki rzeczywiście mają tendencję do osiągania lepszych wyników, szczególnie Rank 1, ale ranking nie jest idealny na całej szerokości listy. Model wydaje się najmocniejszy w identyfikowaniu najlepszych kandydatów, a słabszy w precyzyjnym uporządkowaniu wszystkich 18 spółek od najlepszej do najgorszej.
