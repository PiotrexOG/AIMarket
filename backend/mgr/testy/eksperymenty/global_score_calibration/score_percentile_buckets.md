# Global Score Calibration - Score Percentile Buckets

**Wyniki PNG**

- `backend/data/results/global_score_calibration/score_percentile_buckets/long_term_200d_score_bucket_annualized_return_lines.png`
- `backend/data/results/global_score_calibration/score_percentile_buckets/long_term_200d_score_bucket_annualized_return_average.png`

Test Score Percentile Buckets dzieli wszystkie obserwacje globalnie na koszyki percentylowe według wartości score. Oznacza to, że spółki nie są już grupowane według pozycji w tygodniowym rankingu, jak w `weekly_cross_section/rank_bucket_returns`, tylko według tego, jak wysoką ocenę otrzymały na tle wszystkich ocen wystawionych w całym badanym okresie.

Ten test odpowiada na pytanie: czy obserwacje z najwyższych globalnych percentyli score osiągały później wyższe zwroty niż obserwacje z niższych percentyli? Idealny wynik oznaczałby, że im wyższy globalny percentyl score, tym wyższy późniejszy zwrot.

W praktyce zależność okazała się dodatnia, ale słabsza i mniej regularna niż w testach `weekly_cross_section`. Oznacza to, że wysokie globalne score'y faktycznie miały pewną tendencję do wiązania się z lepszymi zwrotami, jednak nie na tyle silną i monotoniczną, aby jednoznacznie uzasadniać agresywny timing lub znaczące zmienianie wielkości pozycji wyłącznie na podstawie absolutnego poziomu score.

Interpretacja całości `global_score_calibration`: testy miały sprawdzić, czy score można traktować nie tylko jako narzędzie do tygodniowego rankingu spółek, ale również jako globalną miarę atrakcyjności inwestycyjnej. Ponieważ globalna korelacja jest dodatnia, ale wyraźnie niższa niż w testach tygodniowych, w kolejnych testach sensowne pozostaje bardziej konserwatywne założenie: unikać agresywnego timingu i stosować pełną, stałą alokację dostępnego kapitału.
