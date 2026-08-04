# Weekly Cross Section - Information Coefficient

**Wyniki PNG**

- `backend/data/results/weekly_cross_section/information_coefficient/long_term_200d_weekly_information_coefficient.png`

Test Information Coefficient mierzy, czy dla każdego tygodnia score rzeczywiście porządkuje spółki zgodnie z ich późniejszym zwrotem. Dla każdego horyzontu inwestycyjnego osobno liczona jest korelacja przekrojowa w każdym tygodniu, a potem średnia z tych tygodniowych korelacji. Innymi słowy: sprawdzamy, czy w danym tygodniu spółki z wyższym score miały potem wyższy zwrot niż spółki z niższym score.

Na wykresie są trzy metryki:

- Pearson IC: klasyczna korelacja Pearsona między score a przyszłym zwrotem,
- Spearman IC: korelacja rang, czyli test tego, czy kolejność spółek według score zgadza się z kolejnością późniejszych zwrotów,
- Score Percentile Pearson IC: korelacja Pearsona między tygodniowym percentylem score a przyszłym zwrotem; to wersja stabilniejsza względem skali score, bo patrzy na względną pozycję spółki w danym tygodniu.

Jako że dla krótszego horyzontu mamy naturalnie więcej obserwacji niż dla dłuższych, średnia wartość tych korelacji nie jest jedyną oceną modelu, ale pokazuje, jak zmienia się jego skuteczność dla różnych długości trwania horyzontu.

Dla zakresu long-term 21-35 tygodni średnie wartości wyniosły:

- Pearson IC: ok. 0.195,
- Spearman IC: ok. 0.183,
- Score Percentile Pearson IC: ok. 0.199.

Interpretacja: dla horyzontu około 200 dni pojawia się dodatnia i dość stabilna zależność. W praktyce oznacza to, że score nie przewiduje dokładnie przyszłych zwrotów punkt po punkcie, ale statystycznie pomaga ustawiać spółki w lepszej kolejności w obrębie tego samego tygodnia.
