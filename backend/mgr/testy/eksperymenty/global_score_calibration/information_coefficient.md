# Global Score Calibration - Information Coefficient

**Wyniki PNG**

- `backend/data/results/global_score_calibration/information_coefficient/long_term_200d_global_information_coefficient.png`

Test Global Information Coefficient mierzy globalną korelację między score a przyszłym zwrotem dla różnych horyzontów inwestycyjnych. Zamiast liczyć korelację przekrojową osobno dla każdego tygodnia, jak w `weekly_cross_section/information_coefficient`, tutaj wszystkie obserwacje z danego zakresu horyzontów są analizowane razem.

Na wykresie sprawdzamy więc, czy wyższy score globalnie wiązał się z wyższym przyszłym zwrotem. Dla horyzontu 21-35 tygodni średnie wartości wyniosły:

- Pearson IC: ok. 0.110,
- Spearman IC: ok. 0.117,
- Score Percentile Pearson IC: ok. 0.116.

Korelacje są dodatnie, ale wyraźnie niższe niż w ujęciu tygodniowym, gdzie dla tego samego zakresu horyzontu wartości IC były bliżej 0.18-0.20.

Interpretacja: model lepiej sprawdza się jako narzędzie do wyboru najlepszych spółek w danym tygodniu niż jako absolutna miara tego, czy dana spółka w danym momencie jest wyjątkową okazją na tle całej historii ocen.
