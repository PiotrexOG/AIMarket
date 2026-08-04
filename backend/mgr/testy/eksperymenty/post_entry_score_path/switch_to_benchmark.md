# Post Entry Score Path - Switch To Benchmark

**Wyniki PNG**

- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_downside_deviation_heatmap.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_downside_information_ratio_heatmap.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_mean_switch_to_benchmark_annualized_gain_heatmap.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_thresholds_after_25_30pct.png`

Do wyboru konkretnej reguły rebalancingu powstały trzy główne heatmapy:

- `long_term_200d_switch_to_benchmark_downside_deviation_heatmap`,
- `long_term_200d_switch_to_benchmark_downside_information_ratio_heatmap`,
- `long_term_200d_switch_to_benchmark_mean_switch_to_benchmark_annualized_gain_heatmap`.

Heatmapy te łączą dwa parametry decyzji: procent upłyniętego horyzontu oraz próg `relative_score_percentile_change`, poniżej którego spółka byłaby zamieniana na benchmark. Metryka `mean_switch_to_benchmark_annualized_gain` pokazuje średni annualizowany zysk z takiej zamiany. Downside deviation mierzy bolesną stronę błędu, czyli przypadki, w których zamiana na benchmark okazałaby się gorsza niż dalsze trzymanie spółki. Downside information ratio łączy oba elementy: średni zysk z decyzji podzielony przez downside deviation.

Po analizie tych heatmap najciekawszy stabilny obszar pojawia się w okolicy 25-30% upłyniętego horyzontu oraz progu `relative_score_percentile_change` mniejszego niż ok. -55%. W aktualnym wyniku dla progu -55% po 25-30% horyzontu średni annualizowany zysk z zamiany na benchmark wynosi ok. 10.9%, downside deviation ok. 5.9%, a downside information ratio ok. 1.85. Jest to policzone na 82 przypadkach zamiany, czyli nie jest to tylko pojedyncza anomalia.

Nie jest to tak silny efekt jak sama selekcja najlepszych spółek przez model, ale jest to dodatkowe ulepszenie strategii: pozwala wcześniej ograniczać ekspozycję na spółki, które po dobrym starcie szybko tracą miejsce w rankingu i często zaczynają zachowywać się słabiej od rynku.

Ostatni etap dotyczy wyboru progu M. Przeprowadzono eksperyment, w którym ta sama logika zamiany na benchmark była liczona dla różnych początkowych poziomów entry score percentile oraz dla różnych momentów trwania horyzontu. Następnie szukano stabilnych obszarów wysokiego downside information ratio. Najbardziej użyteczny obszar pojawiał się dla spółek startujących od ok. 70. percentyla score, dlatego wariant M = 70 jest racjonalnym kompromisem: obejmuje spółki, które początkowo były wystarczająco dobre, aby strategia faktycznie mogła je trzymać, ale jednocześnie pozwala odfiltrować te przypadki, w których późniejszy spadek score ma największe znaczenie decyzyjne.

Interpretacja całości `post_entry_score_path`: test nie zastępuje głównego mechanizmu selekcji spółek, tylko dodaje warstwę kontroli pozycji po wejściu. Sugeruje, że jeżeli spółka startuje z wysokiego percentyla score, ale po ok. 25-30% planowanego horyzontu jej średni score percentile spada relatywnie o ponad 55% względem wejścia, to dalsze trzymanie tej pozycji często ma gorszy profil niż zamiana jej na benchmark.
