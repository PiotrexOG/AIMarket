# Ticker Percentile History - Score Return Alignment - Pearson Z-Score

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_01_score_zscore_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_02_forward_return_zscore_heatmap.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_03_score_minus_return_zscore_heatmap.png`

Analiza Score Return Alignment pokazuje, gdzie ocena modelu zgadza się z późniejszym wynikiem spółek, a gdzie pojawiają się systematyczne przeszacowania lub niedoszacowania. Pierwszy zestaw dotyczy Pearsona, więc zamiast rang wykorzystuje znormalizowane wartości z-score.

Wykres `pearson_01_score_zscore_heatmap` pokazuje, jak w każdym tygodniu wyglądał znormalizowany score poszczególnych spółek. Dla każdej daty startowej score są przekształcane do z-score w ramach przekroju spółek, a następnie nanoszone na heatmapę. Średnia wartość w wierszu pokazuje, czy dana spółka była przez model zazwyczaj oceniana wyżej lub niżej od pozostałych spółek.

Wykres `pearson_02_forward_return_zscore_heatmap` pokazuje analogiczną normalizację, ale dla przyszłego annualizowanego zwrotu. Dla każdego tygodnia zwroty spółek są zamieniane na z-score w ramach tego samego przekroju. Średnia wartość w wierszu odpowiada na pytanie, które spółki miały ponadprzeciętny lub poniżejprzeciętny przyszły zwrot w całym badanym okresie.

Wykres `pearson_03_score_minus_return_zscore_heatmap` odejmuje wartość z `pearson_02_forward_return_zscore_heatmap` od wartości z `pearson_01_score_zscore_heatmap`. Innymi słowy: pokazuje różnicę między tym, jak mocno model oceniał spółkę, a tym, jak mocno spółka faktycznie później wypadła w przekroju zwrotów. Wartość bliska 0 oznacza zgodność oceny z wynikiem. Wartość dodatnia oznacza sytuację, w której model oceniał spółkę relatywnie wysoko względem tego, co później dostarczyła. Wartość ujemna oznacza sytuację odwrotną, czyli spółka wypadła lepiej, niż sugerowała jej ocena.
