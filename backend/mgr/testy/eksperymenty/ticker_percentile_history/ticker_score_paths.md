# Ticker Percentile History - Ticker Score Paths

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/ticker_score_paths/AAPL_score_percentile_with_price.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/ticker_score_paths/NVDA_score_percentile_with_price.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/ticker_score_paths/TSM_score_percentile_with_price.png`

W katalogu `ticker_score_paths` znajdują się wykresy pojedynczych spółek, np. `AAPL_score_percentile_with_price`, `NVDA_score_percentile_with_price`, `TSM_score_percentile_with_price` i analogiczne wykresy dla pozostałych tickerów. Pokazują one historię score percentile wraz z ceną zamknięcia danej spółki.

Ich rola jest bardziej diagnostyczna niż statystyczna: pomagają sprawdzić, czy zachowanie score dla konkretnej spółki wygląda intuicyjnie i czy nie występują pojedyncze anomalie danych. Te wykresy nie są osobnym testem skuteczności modelu, tylko uzupełniającą kontrolą jakości sygnału na poziomie pojedynczego tickera.
