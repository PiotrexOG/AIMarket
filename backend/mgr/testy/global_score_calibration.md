# Global Score Calibration

Global Score Calibration sprawdza, czy score można traktować nie tylko jako narzędzie do tygodniowego rankingu spółek, ale również jako globalną miarę atrakcyjności inwestycyjnej. To jest inne pytanie niż w `weekly_cross_section`.

W `weekly_cross_section` model oceniany jest relatywnie: czy dobrze porządkuje spółki dostępne w tym samym momencie. W `global_score_calibration` model oceniany jest absolutnie: czy score z różnych tygodni można porównywać między sobą i traktować jako spójną skalę jakości inwestycji.

To rozróżnienie jest ważne, bo system co tydzień otrzymuje aktualną sytuację każdej spółki i na tej podstawie ocenia ją względem pozostałych spółek. Powinien robić to możliwie sprawiedliwie, czyli nie tylko sztucznie rozciągać score od 0 do 1 w ramach każdego tygodnia, ale również nadawać wyższe wartości wtedy, gdy dana spółka wygląda naprawdę dobrze w sensie absolutnym. Problem polega jednak na tym, że każda ocena powstaje w osobnym promptcie, więc model nie ma pełnej pamięci ani spójnej skali względem wszystkich innych sytuacji rynkowych z historii.

## 1. Czy globalnie najwyższe score'y dawały najwyższe zwroty?

Test Top Percent Selection działa podobnie jak tygodniowy Top N Selection, ale zamiast oceniać ranking osobno w każdym tygodniu, wykorzystuje ocenę globalną. Dla każdego horyzontu inwestycyjnego wszystkie obserwacje, czyli wszystkie score'y i odpowiadające im przyszłe zwroty, są wrzucane do jednego wspólnego zbioru. Następnie sprawdzamy, czy spółki, które globalnie otrzymały najwyższe wartości score lub najwyższe percentyle score, osiągały później najwyższe zwroty.

**PNG:** `backend/data/results/global_score_calibration/top_percent_selection/long_term_200d_top_percent_annualized_return.png`

Innymi słowy: test nie pyta już tylko o to, czy w danym tygodniu najlepsza spółka według score była lepsza od pozostałych spółek z tego samego tygodnia. Pyta raczej, czy wysoki score sam w sobie, niezależnie od tygodnia, oznaczał wyjątkowo dobrą okazję inwestycyjną.

W aktualnym wyniku globalne Top 1% osiąga ok. 72.3% rocznie, Top 5% ok. 52.6% rocznie, Top 10% ok. 41.2% rocznie, Top 20% ok. 31.4% rocznie, a Top 100% ok. 19.5% rocznie. To sugeruje, że absolutnie wysokie score'y faktycznie zawierają dodatni sygnał.

Ten wynik sam w sobie wygląda mocno, ale trzeba interpretować go ostrożnie. Bardzo wysokie globalne percentyle są bardziej wrażliwe na pojedyncze obserwacje i na to, czy skala score była spójna między tygodniami. Dlatego kolejnym krokiem jest sprawdzenie globalnej korelacji score z przyszłym zwrotem.

## 2. Jak silna jest globalna korelacja score z przyszłym zwrotem?

Test Global Information Coefficient mierzy globalną korelację między score a przyszłym zwrotem dla różnych horyzontów inwestycyjnych. Zamiast liczyć korelację przekrojową osobno dla każdego tygodnia, jak w `weekly_cross_section/information_coefficient`, tutaj wszystkie obserwacje z danego zakresu horyzontów są analizowane razem.

**PNG:** `backend/data/results/global_score_calibration/information_coefficient/long_term_200d_global_information_coefficient.png`

Na wykresie sprawdzamy, czy wyższy score globalnie wiązał się z wyższym przyszłym zwrotem. Dla horyzontu 21-35 tygodni średnie wartości wyniosły:

- Pearson IC: ok. 0.110,
- Spearman IC: ok. 0.117,
- Score Percentile Pearson IC: ok. 0.116.

Korelacje są dodatnie, ale wyraźnie niższe niż w ujęciu tygodniowym, gdzie dla tego samego zakresu horyzontu wartości IC były bliżej 0.18-0.20. To oznacza, że score zawiera pewien sygnał także w ujęciu globalnym, ale jest on znacznie słabszy niż w ujęciu tygodniowego rankingu.

Interpretacja: model lepiej sprawdza się jako narzędzie do wyboru najlepszych spółek w danym tygodniu niż jako absolutna miara tego, czy dana spółka w danym momencie jest wyjątkową okazją na tle całej historii ocen.

## 3. Czy globalne koszyki percentylowe score układają się sensownie?

Następny test, Score Percentile Buckets, dzieli wszystkie obserwacje globalnie na koszyki percentylowe według wartości score. Oznacza to, że spółki nie są już grupowane według pozycji w tygodniowym rankingu, jak w `weekly_cross_section/rank_bucket_returns`, tylko według tego, jak wysoką ocenę otrzymały na tle wszystkich ocen wystawionych w całym badanym okresie.

**PNG:** `backend/data/results/global_score_calibration/score_percentile_buckets/long_term_200d_score_bucket_annualized_return_lines.png`

**PNG:** `backend/data/results/global_score_calibration/score_percentile_buckets/long_term_200d_score_bucket_annualized_return_average.png`

Ten test odpowiada na pytanie: czy obserwacje z najwyższych globalnych percentyli score osiągały później wyższe zwroty niż obserwacje z niższych percentyli? Idealny wynik oznaczałby, że im wyższy globalny percentyl score, tym wyższy późniejszy zwrot.

W praktyce zależność okazała się dodatnia, ale słabsza i mniej regularna niż w testach `weekly_cross_section`. Oznacza to, że wysokie globalne score'y faktycznie miały pewną tendencję do wiązania się z lepszymi zwrotami, jednak nie na tyle silną i monotoniczną, aby jednoznacznie uzasadniać agresywny timing lub znaczące zmienianie wielkości pozycji wyłącznie na podstawie absolutnego poziomu score.

## 4. Co to oznacza dla strategii?

Global Score Calibration miał odpowiedzieć na pytanie, czy strategię można oprzeć także na timingu, czyli nie tylko kupować najlepsze akcje danego tygodnia, ale również modyfikować wielkość zakładu w zależności od tego, jak dobry jest absolutny poziom score danej spółki oraz jak dobrze wygląda cały rynek na podstawie średnich ocen innych spółek.

Wynik jest mieszany. Z jednej strony Top Percent Selection pokazuje, że najwyższe globalne score'y historycznie dawały bardzo wysokie zwroty. Z drugiej strony Global Information Coefficient jest dodatni, ale wyraźnie słabszy niż weekly IC. Score Percentile Buckets też pokazuje dodatni sygnał, ale nie tworzy idealnie stabilnej, monotonicznej krzywej.

## Interpretacja całości

Global Score Calibration sugeruje, że score ma pewien sens absolutny, ale jego najmocniejszym zastosowaniem pozostaje ranking tygodniowy. Model dobrze odpowiada na pytanie: "która spółka wygląda najlepiej względem innych spółek w tym samym tygodniu?". Słabiej odpowiada na pytanie: "czy ten score jest bezwzględnie tak wysoki, że warto zwiększyć ekspozycję niezależnie od tygodnia?".

Dlatego globalna kalibracja score nie powinna być traktowana jako wystarczająca podstawa do agresywnego timingu. Bardziej konserwatywne założenie pozostaje takie: unikać agresywnego timingu i stosować pełną, stałą alokację dostępnego kapitału, a score wykorzystywać przede wszystkim do wyboru najlepszych spółek w danym tygodniu.
