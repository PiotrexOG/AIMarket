# Post Entry Score Path

Test Post Entry Score Path sprawdza, co dzieje się z oceną spółki już po momencie wejścia w pozycję. W testach `weekly_cross_section` i `downside_information_ratio` najważniejsze było to, czy score dobrze wybiera spółki w tygodniu startowym. Tutaj pytanie jest inne: czy późniejsza ścieżka score, czyli to, jak spółka utrzymuje lub traci swoją pozycję w rankingu w trakcie horyzontu inwestycyjnego, może pomóc w decyzji o dalszym trzymaniu pozycji albo o jej wcześniejszej zamianie na benchmark.

Test jest liczony dla horyzontu `long_term_200d`, czyli zakresu 21-35 tygodni. Dla każdej obserwacji startowej znana jest początkowa pozycja spółki według score percentile, późniejsza średnia pozycja percentylowa w trakcie horyzontu oraz przyszły zwrot spółki względem benchmarku. Benchmark oznacza średni zwrot całego dostępnego koszyka spółek w tym samym okresie.

## 1. Czy utrzymanie wysokiego score ma znaczenie?

Pierwszy punkt odniesienia daje wykres `long_term_200d_alpha_best_correlation_overview`.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_best_correlation_overview.png`

Wykres pokazuje dla wszystkich spółek i wszystkich długości horyzontu z zakresu 21-35 tygodni zależność między średnim percentylem score danej spółki w całym horyzoncie inwestycyjnym a jej średnim rocznym zwrotem powyżej benchmarku. Na osi X znajduje się średni score percentile, a na osi Y annualizowana alfa. Odpowiada to na pytanie, czy spółki regularnie utrzymujące wysoką ocenę modelu faktycznie osiągały wyższy zwrot ponad rynek.

W analizowanym wariancie korelacja jest wyraźnie dodatnia: Pearson dla średniego score percentile względem annualizowanej alfy wynosi ok. 0.555, a Spearman ok. 0.598. Sugeruje to, że nie liczy się tylko pojedyncza ocena w momencie wejścia, ale również trwałość wysokiego percentyla w czasie.

## 2. Czy ta zależność pojawia się dopiero po fakcie, czy narasta w trakcie horyzontu?

Następny krok sprawdza tę samą intuicję narastająco w trakcie trwania pozycji.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_alpha_live_progress_mean_score_percentile_correlations.png`

Wykres `long_term_200d_alpha_live_progress_mean_score_percentile_correlations` pokazuje korelację między dotychczasowym średnim score percentile a późniejszą alfą. Na początku horyzontu korelacja jest zbliżona do tej znanej z testów wejścia. W aktualnym wyniku Pearson zaczyna od ok. 0.259, po 25-30% horyzontu wynosi ok. 0.371, a przy końcu horyzontu dochodzi do ok. 0.545.

Oznacza to, że model coraz lepiej odróżnia spółki, które faktycznie będą miały dobrą alfę, gdy obserwujemy nie tylko punkt startowy, ale także ich dalszą ścieżkę oceny. To prowadzi do praktycznego pytania: czy w trakcie horyzontu istnieje moment, w którym sygnał z pogarszającego się score jest już wystarczająco silny, a jednocześnie do końca inwestycji zostaje jeszcze dość czasu, aby opłacało się zareagować.

Taka reakcja mogłaby polegać na usunięciu z ekspozycji spółek, które początkowo miały wysoką ocenę, ale później wyraźnie spadły w rankingu, i zastąpieniu ich benchmarkiem.

## 3. Dlaczego sam średni score nie wystarcza?

Sama średnia ścieżka score ma istotne ograniczenie. Koncentruje się wyłącznie na średnim poziomie score w trakcie analizowanego horyzontu, pomijając informację o jego zmianie względem wartości początkowej. W rezultacie nie pozwala określić, czy spółka, która początkowo otrzymała wysoką ocenę, utrzymała swoją pozycję, czy też wyraźnie spadła w rankingu.

Do tego celu wprowadzona została metryka:

```text
relative_score_percentile_change = (mean_score_percentile - entry_score_percentile) / entry_score_percentile
```

Metryka pokazuje relatywną zmianę średniego percentyla score względem percentyla z momentu wejścia. Wartość ujemna oznacza, że spółka pogorszyła swoją pozycję w rankingu; wartość dodatnia oznacza, że średnio poprawiła pozycję względem startu. Przy takim zapisie spadek może dojść do -100%, a wzrost nie ma sztywnego górnego ograniczenia.

Ponieważ test ma przede wszystkim odpowiadać na pytanie, kiedy warto wyjść ze spółki pierwotnie ocenionej wysoko, sensowne jest analizowanie głównie spółek, które na wejściu miały odpowiednio wysoki score percentile. W tym celu sprawdzany był próg M, czyli minimalny początkowy percentyl dopuszczający obserwacje do testu. Z dodatkowej analizy wariantów wynika, że stabilny i praktycznie użyteczny obszar pojawia się dla M = 70, czyli dla spółek startujących co najmniej z 70. percentyla score.

## 4. Czy spadek score w całym horyzoncie wiąże się ze słabszą alfą?

Po wprowadzeniu `relative_score_percentile_change` można sprawdzić, czy spółki, które traciły względem swojej początkowej oceny, faktycznie później przegrywały z benchmarkiem.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_relative_score_percentile_change_scatter.png`

Wykres `long_term_200d_alpha_relative_score_percentile_change_scatter` pokazuje zależność między annualizowaną alfą na końcu całego horyzontu a `relative_score_percentile_change` liczonym dla całego horyzontu. W praktyce widać, że gdy relatywna zmiana score percentile spadała poniżej ok. -40%, średnia alfa często przechodziła poniżej 0%. W aktualnych danych średnia alfa dla obserwacji z `relative_score_percentile_change <= -40%` wynosi ok. -13.4% rocznie.

Oznacza to, że spółki, które mocno straciły względem swojej początkowo wysokiej oceny, miały tendencję do przegrywania z benchmarkiem. Dla takich przypadków hipotetyczna zamiana pozycji na benchmark mogłaby poprawiać wynik.

To samo zjawisko w bardziej zagregowanej formie pokazuje heatmapa `long_term_200d_alpha_entry_percentile_by_relative_score_change_heatmap`.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/score_path_observations/long_term_200d_alpha_entry_percentile_by_relative_score_change_heatmap.png`

Wiersze odpowiadają początkowym przedziałom entry score percentile, a kolumny koszykom `relative_score_percentile_change`. Kolor pokazuje średnią alfę. Heatmapa pozwala zobaczyć, że negatywny efekt spadku score jest szczególnie istotny dla spółek, które startowały wysoko, a potem mocno pogorszyły swoją względną ocenę.

## 5. Kiedy w trakcie horyzontu sygnał spadku score zaczyna być użyteczny?

Sama analiza na końcu horyzontu jest wiedzą po fakcie. Dlatego kluczowy jest wykres `long_term_200d_alpha_live_progress_relative_score_percentile_change_correlations`.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_alpha_live_progress_relative_score_percentile_change_correlations.png`

Wykres pokazuje, jak w kolejnych fragmentach horyzontu zmienia się korelacja między `relative_score_percentile_change` a alfą. Jego cel jest praktyczny: znaleźć taki moment, w którym spadek score zaczyna już wyraźnie informować o słabszej przyszłej alfie, ale do końca horyzontu pozostaje jeszcze wystarczająco dużo czasu, aby zamiana na benchmark miała ekonomiczny sens.

W aktualnym wyniku korelacja dla `relative_score_percentile_change` jest na początku bardzo słaba, ale po 25-30% horyzontu Pearson wynosi ok. 0.237, a Spearman ok. 0.264. To nie jest sygnał samodzielnie wystarczający do pełnej strategii, ale jest wystarczająco czytelny, aby traktować go jako pomocniczą warstwę kontroli pozycji.

## 6. Jak dobrać konkretną regułę zamiany na benchmark?

Do wyboru konkretnej reguły rebalancingu powstały trzy główne heatmapy:

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_mean_switch_to_benchmark_annualized_gain_heatmap.png`

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_downside_deviation_heatmap.png`

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_downside_information_ratio_heatmap.png`

Heatmapy te łączą dwa parametry decyzji: procent upłyniętego horyzontu oraz próg `relative_score_percentile_change`, poniżej którego spółka byłaby zamieniana na benchmark. Metryka `mean_switch_to_benchmark_annualized_gain` pokazuje średni annualizowany zysk z takiej zamiany. Downside deviation mierzy bolesną stronę błędu, czyli przypadki, w których zamiana na benchmark okazałaby się gorsza niż dalsze trzymanie spółki. Downside information ratio łączy oba elementy: średni zysk z decyzji podzielony przez downside deviation.

Po analizie tych heatmap najciekawszy stabilny obszar pojawia się w okolicy 25-30% upłyniętego horyzontu oraz progu `relative_score_percentile_change` mniejszego niż ok. -55%. W aktualnym wyniku dla progu -55% po 25-30% horyzontu średni annualizowany zysk z zamiany na benchmark wynosi ok. 10.9%, downside deviation ok. 5.9%, a downside information ratio ok. 1.85. Jest to policzone na 82 przypadkach zamiany, czyli nie jest to tylko pojedyncza anomalia.

Nie jest to tak silny efekt jak sama selekcja najlepszych spółek przez model, ale jest to dodatkowe ulepszenie strategii: pozwala wcześniej ograniczać ekspozycję na spółki, które po dobrym starcie szybko tracą miejsce w rankingu i często zaczynają zachowywać się słabiej od rynku.

## 7. Co dokładnie dzieje się po 25-30% horyzontu?

Dla wybranego momentu 25-30% horyzontu przygotowano dwa wykresy rozproszenia:

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_relative_score_percentile_change_after_25_30pct_remaining_annualized_return_scatter.png`

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_relative_score_percentile_change_after_25_30pct_remaining_annualized_return_scatter_to_0pct.png`

Pokazują one zależność między `relative_score_percentile_change` obserwowanym po 25-30% horyzontu a pozostałą annualizowaną alfą do końca inwestycji. Drugi wariant przycina analizę do wartości `relative_score_percentile_change` maksymalnie równych 0%, bo nie ma praktycznego powodu, aby zamieniać na benchmark spółki, których score percentile wzrósł. W tym wariancie zależność jest czytelniejsza: im silniejszy spadek relatywnego score percentile, tym słabszy dalszy wynik względem benchmarku.

Podobną interpretację daje wykres `long_term_200d_hold_decision_by_score_drop_after_25_30pct`.

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_hold_decision_by_score_drop_after_25_30pct.png`

Zamiast pojedynczych punktów pokazuje on średnią i medianę dalszej annualizowanej alfy w koszykach `relative_score_percentile_change` po 25-30% czasu horyzontu. Dzięki temu łatwiej zobaczyć, że najbardziej ujemne koszyki, czyli największe spadki względnego percentyla score, są powiązane z gorszym dalszym zachowaniem spółki względem benchmarku.

Dla tej samej decyzji przygotowano również wykres przekrojowy progów po 25-30% horyzontu:

**PNG:** `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/switch_to_benchmark/long_term_200d_switch_to_benchmark_thresholds_after_25_30pct.png`

Ten wykres jest pomostem między analizą korelacji a gotową regułą decyzyjną: pokazuje, jak zmieniają się zysk z zamiany, downside deviation i downside information ratio dla różnych progów spadku score w konkretnym momencie horyzontu.

## 8. Dlaczego próg wejścia M = 70?

Ostatni etap dotyczy wyboru progu M. Przeprowadzono eksperyment, w którym ta sama logika zamiany na benchmark była liczona dla różnych początkowych poziomów entry score percentile oraz dla różnych momentów trwania horyzontu. Następnie szukano stabilnych obszarów wysokiego downside information ratio.

Najbardziej użyteczny obszar pojawiał się dla spółek startujących od ok. 70. percentyla score, dlatego wariant M = 70 jest racjonalnym kompromisem: obejmuje spółki, które początkowo były wystarczająco dobre, aby strategia faktycznie mogła je trzymać, ale jednocześnie pozwala odfiltrować te przypadki, w których późniejszy spadek score ma największe znaczenie decyzyjne.

## Interpretacja całości

Post Entry Score Path nie zastępuje głównego mechanizmu selekcji spółek, tylko dodaje warstwę kontroli pozycji po wejściu. Test sugeruje, że jeżeli spółka startuje z wysokiego percentyla score, ale po ok. 25-30% planowanego horyzontu jej średni score percentile spada relatywnie o ponad 55% względem wejścia, to dalsze trzymanie tej pozycji często ma gorszy profil niż zamiana jej na benchmark.

W praktyce może to być reguła pomocnicza do rebalancingu: model wybiera spółki na starcie, a Post Entry Score Path pomaga rozpoznać przypadki, w których pierwotnie dobra teza inwestycyjna zaczyna tracić potwierdzenie w kolejnych ocenach.
