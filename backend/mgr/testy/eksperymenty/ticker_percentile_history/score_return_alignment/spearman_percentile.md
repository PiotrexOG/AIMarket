# Ticker Percentile History - Score Return Alignment - Spearman Percentile

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_01_score_percentile_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_02_forward_return_percentile_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_03_score_minus_return_percentile_heatmap.png`

Analogiczny zestaw wykresów powstał dla Spearmana:

- `spearman_01_score_percentile_heatmap`,
- `spearman_02_forward_return_percentile_heatmap`,
- `spearman_03_score_minus_return_percentile_heatmap`.

W tym przypadku zamiast z-score używane są percentyle. `spearman_01_score_percentile_heatmap` pokazuje ranking percentylowy score w każdym tygodniu, `spearman_02_forward_return_percentile_heatmap` pokazuje ranking percentylowy przyszłych zwrotów, a `spearman_03_score_minus_return_percentile_heatmap` pokazuje różnicę między percentylem oceny i percentylem rzeczywistego wyniku.

Spearman jest bardziej odporny na skalę i wartości odstające, bo interesuje go kolejność spółek, a nie dokładna odległość między nimi. Dlatego odpowiada na pytanie, czy model dobrze szereguje spółki od najlepszych do najsłabszych w danej dacie startowej.
