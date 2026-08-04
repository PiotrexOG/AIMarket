# Global Score Calibration - Top Percent Selection

**Wyniki PNG**

- `backend/data/results/global_score_calibration/top_percent_selection/long_term_200d_top_percent_annualized_return.png`

Test Top Percent Selection działa podobnie jak tygodniowy Top N Selection, ale zamiast oceniać ranking osobno w każdym tygodniu, wykorzystuje ocenę globalną. Oznacza to, że dla każdego horyzontu inwestycyjnego wszystkie obserwacje, czyli wszystkie score'y i odpowiadające im przyszłe zwroty, są wrzucane do jednego wspólnego zbioru. Następnie sprawdzamy, czy spółki, które globalnie otrzymały najwyższe wartości score lub najwyższe percentyle score, osiągały później najwyższe zwroty.

Innymi słowy: test nie pyta już tylko o to, czy w danym tygodniu najlepsza spółka według score była lepsza od pozostałych spółek z tego samego tygodnia. Pyta raczej, czy wysoki score sam w sobie, niezależnie od tygodnia, oznaczał wyjątkowo dobrą okazję inwestycyjną.

Jest to ważna różnica względem `weekly_cross_section`. W analizie tygodniowej model oceniany jest relatywnie: czy dobrze porządkuje spółki dostępne w tym samym momencie. W analizie globalnej model oceniany jest absolutnie: czy score z różnych tygodni można porównywać między sobą i traktować jako miarę ogólnej atrakcyjności inwestycji.

W aktualnym wyniku globalne Top 1% osiąga ok. 72.3% rocznie, Top 5% ok. 52.6% rocznie, Top 10% ok. 41.2% rocznie, Top 20% ok. 31.4% rocznie, a Top 100% ok. 19.5% rocznie. To sugeruje, że absolutnie wysokie score'y faktycznie zawierają dodatni sygnał, choć taka interpretacja jest bardziej wrażliwa na niestabilność skali score między tygodniami.
