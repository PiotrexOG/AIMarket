# Ticker Percentile History - Momentum Controls - Model Vs Momentum

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/model_vs_momentum/model_vs_momentum_jegadeesh_titman_comparison.png`

Bezpośrednie porównanie modelu z klasycznym momentum pokazuje wykres `model_vs_momentum_jegadeesh_titman_comparison`. Porównano średni Pearson IC, Spearman IC, wynik long-short oraz wynik long-only dla modelu i strategii momentum Jegadeesha-Titmana.

Wyniki są wyraźnie korzystniejsze dla modelu. Model ma średni Pearson IC ok. 0.188, podczas gdy momentum w tym samym porównaniu ma ok. -0.150. Modelowy Spearman IC wynosi ok. 0.178, a momentum ok. -0.185. Podobnie w metrykach atrybucji model osiąga dodatni wynik long-short ok. 0.090 i long-only ok. 0.110, podczas gdy momentum ma wartości ujemne, odpowiednio ok. -0.083 i -0.105.

Interpretacja tego porównania jest istotna: nawet jeśli score modelu ma pewien związek z historycznym momentum, to w tym badaniu nie zachowuje się jak zwykła strategia momentum. Model daje wyższą i dodatnią zgodność z przyszłymi zwrotami, podczas gdy prosty benchmark momentum wypada dużo słabiej. Oznacza to, że model najprawdopodobniej wykorzystuje dodatkową informację albo inny sposób agregacji sygnałów niż sam trailing return.

Interpretacja całości `ticker_percentile_history`: test potwierdza, że model ma dodatnią siłę przekrojową dla horyzontu 21-35 tygodni. Najważniejszy dowód daje `score_return_correlation_by_timestamp`, gdzie średnie IC są dodatnie, oraz `score_return_correlation_hac_diagnostics`, który pokazuje, że po korekcie na nachodzące obserwacje przedziały ufności nadal pozostają powyżej zera. Heatmapy Pearsona i Spearmana pokazują, gdzie model przeszacowuje lub niedoszacowuje spółki, a atrybucje return attribution przekładają korelacje na bardziej inwestycyjną interpretację. Testy momentum controls sugerują natomiast, że model nie jest jedynie prostym momentum.
