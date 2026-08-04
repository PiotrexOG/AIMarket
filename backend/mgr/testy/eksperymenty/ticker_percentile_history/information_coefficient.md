# Ticker Percentile History - Information Coefficient

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_by_timestamp.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/information_coefficient/score_return_correlation_hac_diagnostics.png`

Heatmapy pozwalają ocenić stabilność wizualnie, ale kluczowa liczba pochodzi z bezpośredniego porównania korelacji dla każdej daty startowej. Pokazuje to wykres `score_return_correlation_by_timestamp`. Dla każdego tygodnia liczona jest przekrojowa korelacja między score i przyszłym zwrotem. Na wykresie znajdują się Pearson IC, Spearman IC oraz dodatkowy `score_percentile_pearson_ic`, czyli korelacja Pearsona między percentylem score a rzeczywistym przyszłym zwrotem.

Wyniki są dodatnie i relatywnie stabilne. Średni Pearson IC wynosi ok. 0.188, średni Spearman IC ok. 0.178, a Score Percentile Pearson IC ok. 0.195. Są to wartości zbliżone do wyników testów `weekly_cross_section` dla horyzontu long-term, co wzmacnia wniosek, że model rzeczywiście zawiera użyteczny sygnał przekrojowy.

Wykres `score_return_correlation_by_timestamp` pokazuje również znormalizowany zwrot benchmarku. Widać, że korelacja modelu nie jest stała: w niektórych okresach rośnie, a w innych spada. W notatkach szczególnie widoczna była zależność, że model często lepiej odróżniał spółki w słabszych okresach rynku, a jego przewaga bywała mniejsza, gdy cały rynek zachowywał się bardzo dobrze.

Ponieważ kolejne daty startowe są oddalone od siebie tylko o tydzień, a badane horyzonty trwają 21-35 tygodni, obserwacje są silnie nachodzące na siebie. To oznacza, że zwykła średnia korelacja może wyglądać zbyt pewnie, bo sąsiednie tygodnie mierzą bardzo podobny przyszły okres. Dlatego przeprowadzono diagnostykę HAC, czyli korektę uwzględniającą autokorelację i nachodzenie się obserwacji.

Wyniki przedstawia wykres `score_return_correlation_hac_diagnostics` oraz plik pomocniczy `score_return_correlation_hac_summary.csv`. Dla Pearsona średni IC pozostaje ok. 0.188, a 95% przedział ufności po konserwatywnym raportowaniu wynosi ok. 0.138-0.238. Dla Spearmana średnia wynosi ok. 0.178, a przedział 95% ok. 0.133-0.224. Dla `score_percentile_pearson_ic` średnia wynosi ok. 0.195, a przedział 95% ok. 0.146-0.245.

Najważniejszy wniosek jest taki, że nawet po uwzględnieniu problemu nachodzących horyzontów przedziały pozostają dodatnie. Nie eliminuje to ryzyka overfittingu, ale wzmacnia argument, że dodatni sygnał modelu nie jest tylko artefaktem kilku przypadkowych tygodni.
