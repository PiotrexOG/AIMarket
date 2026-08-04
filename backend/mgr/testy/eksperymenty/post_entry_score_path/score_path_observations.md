# Post Entry Score Path - Score Path Observations

**Wyniki PNG**

- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_best_correlation_overview.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_relative_score_percentile_change_scatter.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_entry_percentile_by_relative_score_change_heatmap.png`

Test Post Entry Score Path sprawdza, co dzieje się z oceną spółki już po momencie wejścia w pozycję. W testach `weekly_cross_section` i `downside_information_ratio` najważniejsze było to, czy score dobrze wybiera spółki w tygodniu startowym. Tutaj pytanie jest inne: czy późniejsza ścieżka score, czyli to, jak spółka utrzymuje lub traci swoją pozycję w rankingu w trakcie horyzontu inwestycyjnego, może pomóc w decyzji o dalszym trzymaniu pozycji albo o jej wcześniejszej zamianie na benchmark.

Test jest liczony dla horyzontu `long_term_200d`, czyli zakresu 21-35 tygodni. Dla każdej obserwacji startowej znana jest początkowa pozycja spółki według score percentile, późniejsza średnia pozycja percentylowa w trakcie horyzontu oraz przyszły zwrot spółki względem benchmarku. Benchmark oznacza średni zwrot całego dostępnego koszyka spółek w tym samym okresie.

Pierwszy punkt odniesienia daje wykres `long_term_200d_alpha_best_correlation_overview`. Pokazuje on dla wszystkich spółek i wszystkich długości horyzontu z zakresu 21-35 tygodni zależność między średnim percentylem score danej spółki w całym horyzoncie inwestycyjnym a jej średnim rocznym zwrotem powyżej benchmarku. Na osi X znajduje się średni score percentile, a na osi Y annualizowana alfa.

W analizowanym wariancie korelacja jest wyraźnie dodatnia: Pearson dla średniego score percentile względem annualizowanej alfy wynosi ok. 0.555, a Spearman ok. 0.598. Sugeruje to, że nie liczy się tylko pojedyncza ocena w momencie wejścia, ale również trwałość wysokiego percentyla w czasie.

Do opisu zmiany score wprowadzona została metryka:

```text
relative_score_percentile_change = (mean_score_percentile - entry_score_percentile) / entry_score_percentile
```

Metryka pokazuje relatywną zmianę średniego percentyla score względem percentyla z momentu wejścia. Wartość ujemna oznacza, że spółka pogorszyła swoją pozycję w rankingu; wartość dodatnia oznacza, że średnio poprawiła pozycję względem startu. Przy takim zapisie spadek może dojść do -100%, a wzrost nie ma sztywnego górnego ograniczenia.

Ponieważ test ma przede wszystkim odpowiadać na pytanie, kiedy warto wyjść ze spółki pierwotnie ocenionej wysoko, sensowne jest analizowanie głównie spółek, które na wejściu miały odpowiednio wysoki score percentile. W tym celu sprawdzany był próg M, czyli minimalny początkowy percentyl dopuszczający obserwacje do testu. Z dodatkowej analizy wariantów wynika, że stabilny i praktycznie użyteczny obszar pojawia się dla M = 70, czyli dla spółek startujących co najmniej z 70. percentyla score.

Wykres `long_term_200d_alpha_relative_score_percentile_change_scatter` pokazuje zależność między annualizowaną alfą na końcu całego horyzontu a `relative_score_percentile_change` liczonym dla całego horyzontu. W praktyce widać, że gdy relatywna zmiana score percentile spadała poniżej ok. -40%, średnia alfa często przechodziła poniżej 0%. W aktualnych danych średnia alfa dla obserwacji z `relative_score_percentile_change <= -40%` wynosi ok. -13.4% rocznie. Oznacza to, że spółki, które mocno straciły względem swojej początkowo wysokiej oceny, miały tendencję do przegrywania z benchmarkiem.

To samo zjawisko w bardziej zagregowanej formie pokazuje heatmapa `long_term_200d_alpha_entry_percentile_by_relative_score_change_heatmap`. Wiersze odpowiadają początkowym przedziałom entry score percentile, a kolumny koszykom `relative_score_percentile_change`. Kolor pokazuje średnią alfę. Heatmapa pozwala zobaczyć, że negatywny efekt spadku score jest szczególnie istotny dla spółek, które startowały wysoko, a potem mocno pogorszyły swoją względną ocenę.
