# Ticker Percentile History - Information Coefficient

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_by_timestamp.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_pearson_autocorrelation_by_horizon_lag.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_spearman_autocorrelation_by_horizon_lag.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_score_percentile_pearson_autocorrelation_by_horizon_lag.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_hac_diagnostics.png`

Porównanie polegało na uśrednieniu wartości korelacji w zakresie horyzontów 21–35 tygodni dla przyjętego okresu badania. Zależności te — wyznaczone za pomocą korelacji Pearsona, Spearmana oraz IC opartego na percentylach — przedstawiono na wykresie score_return_correlation_by_timestamp. Wykres ten obrazuje dynamikę korelacji w czasie, ukazując wyniki osobno dla każdego tygodnia.

Na wykresie ujęto również zachowanie benchmarku, gdzie szarym kolorem zaznaczono odchylenie standardowe jego stóp zwrotu. Wyniki wskazują na ujemną zależność między stopą zwrotu benchmarku a efektywnością modelu: korelacja osiągała wyższe wartości w okresach gorszych wyników benchmarku, natomiast podczas jego silnych wzrostów ulegała osłabieniu.

Kolejnym testem była ostateczna odpowiedź na pytanie, jakie IC ma zbudowany system. W tym celu zdecydowano się wykorzystać maksymalnie wszystkie obserwacje, licząc osobne wartości dla każdej długości horyzontu 21-35 tygodni, a następnie uśredniając wynik.

Ponieważ kolejne daty startowe są oddalone od siebie tylko o tydzień, a badane horyzonty trwają 21-35 tygodni, obserwacje są silnie nachodzące na siebie. To oznacza, że zwykła średnia korelacja może wyglądać zbyt pewnie, bo sąsiednie tygodnie mierzą bardzo podobny przyszły okres. Dlatego przeprowadzono diagnostykę HAC, czyli korektę uwzględniającą autokorelację i nachodzenie się obserwacji.

Wykresy `score_return_correlation_pearson_autocorrelation_by_horizon_lag`, `score_return_correlation_spearman_autocorrelation_by_horizon_lag` oraz `score_return_correlation_score_percentile_pearson_autocorrelation_by_horizon_lag` pokazują autokorelację dla każdej długości horyzontu i dla kolejnych lagów. Pod spodem znajdują się wartości 95% CI liczone klasycznie oraz po korekcie HAC. Te wykresy są więc diagnostyką tego, jak mocno nachodzące obserwacje wpływają na niepewność wyniku.

Wyniki końcowe przedstawia wykres `score_return_correlation_hac_diagnostics`. Dla Pearsona oficjalny IC wynosi ok. 0.205, a 95% przedział ufności po konserwatywnym raportowaniu wynosi ok. 0.145-0.266. Dla Spearmana średnia wynosi ok. 0.183, a przedział 95% ok. 0.132-0.234. Dla `score_percentile_pearson_ic` średnia wynosi ok. 0.208, a przedział 95% ok. 0.150-0.265.

Najważniejszy wniosek jest taki, że nawet po uwzględnieniu problemu nachodzących horyzontów przedziały pozostają dodatnie. Nie eliminuje to ryzyka overfittingu, ale wzmacnia argument, że dodatni sygnał modelu nie jest tylko artefaktem kilku przypadkowych tygodni ani jednego arbitralnie dobranego horyzontu.
