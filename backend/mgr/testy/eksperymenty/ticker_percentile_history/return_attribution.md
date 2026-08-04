# Ticker Percentile History - Return Attribution

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/return_contribution_attribution_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/long_only_return_contribution_attribution_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/normalized_excess_attribution_by_timestamp.png`

Oprócz klasycznych korelacji zbudowano również metryki atrybucji zysku. Wykres `return_contribution_attribution_heatmap` pokazuje hipotetyczny wkład strategii long-short. Dla każdego tygodnia spółka dostaje wagę związaną z jej score percentile minus 0.5, a następnie ta waga jest mnożona przez jej annualizowaną alfę. W praktyce dodatni wynik oznacza, że model przypisał większą wagę spółkom, które później dały lepszą alfę, oraz mniejszą lub ujemną wagę tym, które później zachowały się słabiej.

Wykres `long_only_return_contribution_attribution_heatmap` pokazuje analogiczną logikę, ale tylko dla strony long, czyli dla spółek z górnej połowy rankingu score. Ten wariant jest bliższy praktycznej strategii kupowania najlepszych spółek bez shortowania słabszych. W badaniu long-only wyglądał lepiej niż long-short, co jest ważne praktycznie: przewaga modelu wydaje się silniejsza w identyfikowaniu dobrych kandydatów do kupna niż w budowaniu symetrycznej strategii long-short.

Pomocniczo powstał także wykres `normalized_excess_attribution_by_timestamp`. Pokazuje on, jak zmieniał się zagregowany, znormalizowany wkład modelu w kolejnych datach startowych. Jest to sposób na sprawdzenie, czy dodatni wynik atrybucji pochodzi z wielu tygodni, czy z pojedynczego wyjątkowego okresu. Wykres pomaga więc łączyć interpretację heatmap z oceną stabilności po czasie.
