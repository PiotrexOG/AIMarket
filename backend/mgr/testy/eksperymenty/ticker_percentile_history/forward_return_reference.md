# Ticker Percentile History - Forward Return Reference

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/forward_return_reference/excess_forward_annualized_return_heatmap.png`

Test Ticker Percentile History jest przekrojową walidacją modelu zgodną z założeniem, że po wyborze docelowego horyzontu `long_term_200d`, czyli 21-35 tygodni, należy sprawdzić nie tylko średni wynik strategii, ale również stabilność sygnału w czasie i na poziomie poszczególnych spółek. Celem testu jest odpowiedź na pytanie, czy model działa ogólnie, dla różnych dat startowych i różnych spółek, czy jego skuteczność wynika z kilku wyjątkowych przypadków.

W badaniu cały okres symulacji zostaje podzielony na tygodnie startowe, z pominięciem ostatnich 35 tygodni, dla których nie da się już policzyć pełnego przyszłego zwrotu w najdłuższym horyzoncie. Dla każdej daty startowej i każdej spółki liczony jest score, pozycja percentylowa score oraz przyszły annualizowany zwrot w zakresie 21-35 tygodni. Następnie porównuje się ocenę modelu z rzeczywistym późniejszym wynikiem.

Podstawowym sposobem prezentacji są heatmapy, w których na osi X znajdują się kolejne daty startowe, a na osi Y spółki z badanej symulacji. Taki układ pozwala zobaczyć, czy sygnał modelu jest rozłożony względnie równomiernie, czy koncentruje się tylko w pojedynczych datach albo na pojedynczych tickerach.

Wykres `excess_forward_annualized_return_heatmap` pokazuje annualizowaną alfę każdej spółki dla każdej daty startowej. Jest to mapa rzeczywistego wyniku, czyli punkt odniesienia dla dalszych heatmap. Kolor nie pokazuje tutaj oceny modelu, tylko to, jak spółka faktycznie zachowała się względem benchmarku w przyszłym horyzoncie. Dzięki temu można zobaczyć, które spółki i które okresy były źródłem dodatniej lub ujemnej alfy.
