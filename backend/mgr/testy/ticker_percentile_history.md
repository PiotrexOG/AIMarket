# Ticker Percentile History

Test Ticker Percentile History jest przekrojową walidacją modelu zgodną z założeniem, że po wyborze docelowego horyzontu `long_term_200d`, czyli 21-35 tygodni, należy sprawdzić nie tylko średni wynik strategii, ale również stabilność sygnału w czasie i na poziomie poszczególnych spółek. Celem testu jest odpowiedź na pytanie, czy model działa ogólnie, dla różnych dat startowych i różnych spółek, czy jego skuteczność wynika z kilku wyjątkowych przypadków.

W badaniu cały okres symulacji zostaje podzielony na tygodnie startowe, z pominięciem ostatnich 35 tygodni, dla których nie da się już policzyć pełnego przyszłego zwrotu w najdłuższym horyzoncie. Dla każdej daty startowej i każdej spółki liczony jest score, pozycja percentylowa score oraz przyszły annualizowany zwrot w zakresie 21-35 tygodni. Następnie porównuje się ocenę modelu z rzeczywistym późniejszym wynikiem.

Podstawowym sposobem prezentacji są heatmapy, w których na osi X znajdują się kolejne daty startowe, a na osi Y spółki z badanej symulacji. Taki układ pozwala zobaczyć, czy sygnał modelu jest rozłożony względnie równomiernie, czy koncentruje się tylko w pojedynczych datach albo na pojedynczych tickerach.

## 1. Jaki jest punkt odniesienia dla przyszłych zwrotów?

Pierwszym punktem odniesienia jest wykres `excess_forward_annualized_return_heatmap`.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/forward_return_reference/excess_forward_annualized_return_heatmap.png`

Wykres `excess_forward_annualized_return_heatmap` pokazuje annualizowaną alfę każdej spółki dla każdej daty startowej. Jest to mapa rzeczywistego wyniku, czyli punkt odniesienia dla dalszych heatmap. Dzięki temu można zobaczyć, które spółki i które okresy były źródłem dodatniej lub ujemnej alfy.

## 2. Jakie IC ma zbudowany system?

Porównanie polegało na uśrednieniu wartości korelacji w zakresie horyzontów 21–35 tygodni dla przyjętego okresu badania. Zależności te — wyznaczone za pomocą korelacji Pearsona, Spearmana oraz IC opartego na percentylach — przedstawiono na wykresie score_return_correlation_by_timestamp. Wykres ten obrazuje dynamikę korelacji w czasie, ukazując wyniki osobno dla każdego tygodnia.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_by_timestamp.png`

Na wykresie ujęto również zachowanie benchmarku, gdzie szarym kolorem zaznaczono odchylenie standardowe jego stóp zwrotu. Wyniki wskazują na ujemną zależność między stopą zwrotu benchmarku a efektywnością modelu: korelacja osiągała wyższe wartości w okresach gorszych wyników benchmarku, natomiast podczas jego silnych wzrostów ulegała osłabieniu.

Kolejnym testem była ostateczna odpowiedź na pytanie, jakie IC ma zbudowany system. W tym celu zdecydowano się wykorzystać maksymalnie wszystkie obserwacje, licząc osobne wartości dla każdej długości horyzontu 21-35 tygodni, a następnie uśredniając wynik.

Ponieważ kolejne daty startowe są oddalone od siebie tylko o tydzień, a badane horyzonty trwają 21-35 tygodni, obserwacje są silnie nachodzące na siebie. To oznacza, że zwykła średnia korelacja może wyglądać zbyt pewnie, bo sąsiednie tygodnie mierzą bardzo podobny przyszły okres. Dlatego przeprowadzono diagnostykę HAC, czyli korektę uwzględniającą autokorelację i nachodzenie się obserwacji.

Wykresy `score_return_correlation_pearson_autocorrelation_by_horizon_lag`, `score_return_correlation_spearman_autocorrelation_by_horizon_lag` oraz `score_return_correlation_score_percentile_pearson_autocorrelation_by_horizon_lag` pokazują autokorelację dla każdej długości horyzontu i dla kolejnych lagów. Pod spodem znajdują się wartości 95% CI liczone klasycznie oraz po korekcie HAC. Te wykresy są więc diagnostyką tego, jak mocno nachodzące obserwacje wpływają na niepewność wyniku.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_pearson_autocorrelation_by_horizon_lag.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_spearman_autocorrelation_by_horizon_lag.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_score_percentile_pearson_autocorrelation_by_horizon_lag.png`

Wyniki końcowe przedstawia wykres `score_return_correlation_hac_diagnostics`.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_hac_diagnostics.png`

Dla Pearsona oficjalny IC wynosi ok. 0.205, a 95% przedział ufności po konserwatywnym raportowaniu wynosi ok. 0.145-0.266. Dla Spearmana średnia wynosi ok. 0.183, a przedział 95% ok. 0.132-0.234. Dla `score_percentile_pearson_ic` średnia wynosi ok. 0.208, a przedział 95% ok. 0.150-0.265.

Najważniejszy wniosek jest taki, że nawet po uwzględnieniu problemu nachodzących horyzontów przedziały pozostają dodatnie. Nie eliminuje to ryzyka overfittingu, ale wzmacnia argument, że dodatni sygnał modelu nie jest tylko artefaktem kilku przypadkowych tygodni ani jednego arbitralnie dobranego horyzontu.

## 3. Gdzie score modelu zgadza się z późniejszym wynikiem?

Analiza Score Return Alignment pokazuje, gdzie ocena modelu zgadza się z późniejszym wynikiem spółek, a gdzie pojawiają się systematyczne przeszacowania lub niedoszacowania. Pierwszy zestaw dotyczy Pearsona, więc zamiast rang wykorzystuje znormalizowane wartości z-score.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_01_score_zscore_heatmap.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_02_forward_return_zscore_heatmap.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/pearson_zscore/pearson_03_score_minus_return_zscore_heatmap.png`

Wykres `pearson_01_score_zscore_heatmap` pokazuje, jak w każdym tygodniu wyglądał znormalizowany score poszczególnych spółek. Dla każdej daty startowej score są przekształcane do z-score w ramach przekroju spółek, a następnie nanoszone na heatmapę. Średnia wartość w wierszu pokazuje, czy dana spółka była przez model zazwyczaj oceniana wyżej lub niżej od pozostałych spółek.

Wykres `pearson_02_forward_return_zscore_heatmap` pokazuje analogiczną normalizację, ale dla przyszłego annualizowanego zwrotu. Dla każdego tygodnia zwroty spółek są zamieniane na z-score w ramach tego samego przekroju. Średnia wartość w wierszu odpowiada na pytanie, które spółki miały ponadprzeciętny lub poniżejprzeciętny przyszły zwrot w całym badanym okresie.

Wykres `pearson_03_score_minus_return_zscore_heatmap` odejmuje wartość z `pearson_02_forward_return_zscore_heatmap` od wartości z `pearson_01_score_zscore_heatmap`. Innymi słowy: pokazuje różnicę między tym, jak mocno model oceniał spółkę, a tym, jak mocno spółka faktycznie później wypadła w przekroju zwrotów. Wartość bliska 0 oznacza zgodność oceny z wynikiem. Wartość dodatnia oznacza sytuację, w której model oceniał spółkę relatywnie wysoko względem tego, co później dostarczyła. Wartość ujemna oznacza sytuację odwrotną, czyli spółka wypadła lepiej, niż sugerowała jej ocena.

## 4. Czy kolejność spółek według score zgadza się z kolejnością zwrotów?

Analogiczny zestaw wykresów powstał dla Spearmana:

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_01_score_percentile_heatmap.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_02_forward_return_percentile_heatmap.png`

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/score_return_alignment/spearman_percentile/spearman_03_score_minus_return_percentile_heatmap.png`

W tym przypadku zamiast z-score używane są percentyle. `spearman_01_score_percentile_heatmap` pokazuje ranking percentylowy score w każdym tygodniu, `spearman_02_forward_return_percentile_heatmap` pokazuje ranking percentylowy przyszłych zwrotów, a `spearman_03_score_minus_return_percentile_heatmap` pokazuje różnicę między percentylem oceny i percentylem rzeczywistego wyniku.

Spearman jest bardziej odporny na skalę i wartości odstające, bo interesuje go kolejność spółek, a nie dokładna odległość między nimi. Dlatego odpowiada na pytanie, czy model dobrze szereguje spółki od najlepszych do najsłabszych w danej dacie startowej.

## 5. Jak korelacje przekładają się na atrybucję zysku?

Oprócz klasycznych korelacji zbudowano również metryki atrybucji zysku. Wykres `return_contribution_attribution_heatmap` pokazuje hipotetyczny wkład strategii long-short.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/return_contribution_attribution_heatmap.png`

Dla każdego tygodnia spółka dostaje wagę związaną z jej score percentile minus 0.5, a następnie ta waga jest mnożona przez jej annualizowaną alfę. W praktyce dodatni wynik oznacza, że model przypisał większą wagę spółkom, które później dały lepszą alfę, oraz mniejszą lub ujemną wagę tym, które później zachowały się słabiej.

Wykres `long_only_return_contribution_attribution_heatmap` pokazuje analogiczną logikę, ale tylko dla strony long, czyli dla spółek z górnej połowy rankingu score.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/long_only_return_contribution_attribution_heatmap.png`

Ten wariant jest bliższy praktycznej strategii kupowania najlepszych spółek bez shortowania słabszych. W badaniu long-only wyglądał lepiej niż long-short, co jest ważne praktycznie: przewaga modelu wydaje się silniejsza w identyfikowaniu dobrych kandydatów do kupna niż w budowaniu symetrycznej strategii long-short.

Pomocniczo powstał także wykres `normalized_excess_attribution_by_timestamp`.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/return_attribution/normalized_excess_attribution_by_timestamp.png`

Pokazuje on, jak zmieniał się zagregowany, znormalizowany wkład modelu w kolejnych datach startowych. Jest to sposób na sprawdzenie, czy dodatni wynik atrybucji pochodzi z wielu tygodni, czy z pojedynczego wyjątkowego okresu. Wykres pomaga więc łączyć interpretację heatmap z oceną stabilności po czasie.

## 6. Czy model jest tylko prostym momentum?

Bezpośrednie porównanie modelu z klasycznym momentum pokazuje wykres `model_vs_momentum_jegadeesh_titman_comparison`.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/model_vs_momentum/model_vs_momentum_jegadeesh_titman_comparison.png`

Porównano średni Pearson IC, Spearman IC, wynik long-short oraz wynik long-only dla modelu i strategii momentum Jegadeesha-Titmana.

Wyniki są wyraźnie korzystniejsze dla modelu. Model ma średni Pearson IC ok. 0.188, podczas gdy momentum w tym samym porównaniu ma ok. -0.150. Modelowy Spearman IC wynosi ok. 0.178, a momentum ok. -0.185. Podobnie w metrykach atrybucji model osiąga dodatni wynik long-short ok. 0.090 i long-only ok. 0.110, podczas gdy momentum ma wartości ujemne, odpowiednio ok. -0.083 i -0.105.

Interpretacja tego porównania jest istotna: nawet jeśli score modelu ma pewien związek z historycznym momentum, to w tym badaniu nie zachowuje się jak zwykła strategia momentum. Model daje wyższą i dodatnią zgodność z przyszłymi zwrotami, podczas gdy prosty benchmark momentum wypada dużo słabiej. Oznacza to, że model najprawdopodobniej wykorzystuje dodatkową informację albo inny sposób agregacji sygnałów niż sam trailing return.

## 7. Co pokazuje analiza wewnątrz pojedynczych spółek?

Kolejnym testem była analiza w ramach pojedynczych spółek, przedstawiona na wykresie `score_to_future_annualized_return_correlation_by_ticker`.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/anti_momentum/score_to_future_annualized_return_correlation_by_ticker.png`

Tutaj pytanie jest inne niż w klasycznym IC. Nie sprawdzamy już, czy w danym tygodniu lepiej ocenione spółki zachowywały się lepiej od innych spółek, ale czy dla tej samej spółki wyższy score w jednym tygodniu oznaczał wyższy przyszły zwrot niż jej niższy score w innym tygodniu.

Wynik średnio okazał się słaby i ujemny: średnia korelacja po tickerach wynosi ok. -0.245. Nie jest to zaskakujące, ponieważ model był projektowany jako narzędzie przekrojowe: co tydzień porównuje spółki między sobą, ale nie musi mieć stabilnej absolutnej skali dla tej samej spółki w czasie.

To rozróżnienie jest ważne. Model może dobrze odpowiadać na pytanie "która spółka wygląda lepiej od innych w tym tygodniu", a jednocześnie słabiej odpowiadać na pytanie "czy ta sama spółka wygląda dzisiaj lepiej niż kilka tygodni temu". Ujemny wynik na `score_to_future_annualized_return_correlation_by_ticker` nie unieważnia więc głównego sygnału przekrojowego, ale ogranicza zastosowanie modelu jako narzędzia absolutnego timingu dla pojedynczego tickera.

Dodatkowo sprawdzono, czy score modelu nie jest po prostu ukrytym momentum. Wykres `score_to_trailing_jegadeesh_titman_return_correlation_by_ticker` pokazuje korelację między score danej spółki a jej trailing return liczonym według podejścia Jegadeesha-Titmana, z pominięciem ostatnich 4 tygodni.

**PNG:** `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/anti_momentum/score_to_trailing_jegadeesh_titman_return_correlation_by_ticker.png`

Wynik wskazuje na umiarkowany związek: średnia korelacja po tickerach wynosi ok. 0.260. Model w pewnym stopniu może więc korzystać z informacji podobnej do momentum, czyli lepiej oceniać spółki, które wcześniej zachowywały się dobrze. Sama korelacja z momentum nie wystarcza jednak, aby uznać, że model jest tylko prostym momentum.

## Interpretacja całości

Test potwierdza, że model ma dodatnią siłę przekrojową dla horyzontu 21-35 tygodni. Najważniejszy dowód daje `score_return_correlation_by_timestamp`, gdzie średnie IC są dodatnie, oraz `score_return_correlation_hac_diagnostics`, który pokazuje, że po korekcie na nachodzące obserwacje przedziały ufności nadal pozostają powyżej zera.

Heatmapy Pearsona i Spearmana pokazują, gdzie model przeszacowuje lub niedoszacowuje spółki, a atrybucje return attribution przekładają korelacje na bardziej inwestycyjną interpretację. Testy momentum controls sugerują natomiast, że model nie jest jedynie prostym momentum.

Jednocześnie analiza w ramach pojedynczych spółek ogranicza interpretację modelu jako narzędzia absolutnego timingu dla jednego tickera. Model najlepiej odpowiada na pytanie, która spółka wygląda lepiej od innych w tym samym tygodniu, a niekoniecznie na pytanie, czy ta sama spółka wygląda lepiej niż kilka tygodni wcześniej.
