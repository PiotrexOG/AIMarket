# Post Entry Score Path - Live Progress

**Wyniki PNG**

- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_alpha_live_progress_mean_score_percentile_correlations.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_alpha_live_progress_relative_score_percentile_change_correlations.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_relative_score_percentile_change_after_25_30pct_remaining_annualized_return_scatter.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_relative_score_percentile_change_after_25_30pct_remaining_annualized_return_scatter_to_0pct.png`
- `backend/data/results/post_entry_score_path/21-35w/entry_min_score_percentile_70/live_progress/long_term_200d_hold_decision_by_score_drop_after_25_30pct.png`

Wykres `long_term_200d_alpha_live_progress_mean_score_percentile_correlations` pokazuje zależność między dotychczasowym średnim score percentile a późniejszą alfą, liczoną narastająco w trakcie trwania horyzontu. Na początku horyzontu korelacja jest zbliżona do tej znanej z testów wejścia. W aktualnym wyniku Pearson zaczyna od ok. 0.259, po 25-30% horyzontu wynosi ok. 0.371, a przy końcu horyzontu dochodzi do ok. 0.545. Oznacza to, że model coraz lepiej odróżnia spółki, które faktycznie będą miały dobrą alfę, gdy obserwujemy nie tylko punkt startowy, ale także ich dalszą ścieżkę oceny.

Ten wniosek prowadzi do praktycznego pytania: czy w trakcie horyzontu istnieje moment, w którym sygnał z pogarszającego się score jest już wystarczająco silny, a jednocześnie do końca inwestycji zostaje jeszcze dość czasu, aby opłacało się zareagować. Taka reakcja mogłaby polegać na usunięciu z ekspozycji spółek, które początkowo miały wysoką ocenę, ale później wyraźnie spadły w rankingu, i zastąpieniu ich benchmarkiem.

Sama średnia ścieżka score ma jednak istotne ograniczenie. Koncentruje się wyłącznie na średnim poziomie score w trakcie analizowanego horyzontu, pomijając informację o jego zmianie względem wartości początkowej. W rezultacie nie pozwala określić, czy spółka, która początkowo otrzymała wysoką ocenę, utrzymała swoją pozycję, czy też wyraźnie spadła w rankingu.

Dlatego kluczowy jest wykres `long_term_200d_alpha_live_progress_relative_score_percentile_change_correlations`. Pokazuje on, jak w kolejnych fragmentach horyzontu zmienia się korelacja między `relative_score_percentile_change` a alfą. Jego cel jest praktyczny: znaleźć taki moment, w którym spadek score zaczyna już wyraźnie informować o słabszej przyszłej alfie, ale do końca horyzontu pozostaje jeszcze wystarczająco dużo czasu, aby zamiana na benchmark miała ekonomiczny sens.

W aktualnym wyniku korelacja dla `relative_score_percentile_change` jest na początku bardzo słaba, ale po 25-30% horyzontu Pearson wynosi ok. 0.237, a Spearman ok. 0.264. To nie jest sygnał samodzielnie wystarczający do pełnej strategii, ale jest wystarczająco czytelny, aby traktować go jako pomocniczą warstwę kontroli pozycji.

Dla wybranego momentu 25-30% horyzontu przygotowano dwa wykresy rozproszenia: `long_term_200d_relative_score_percentile_change_after_25_30pct_remaining_annualized_return_scatter` oraz wariant z przycięciem do wartości `relative_score_percentile_change <= 0%`. Pokazują one zależność między spadkiem względnego score po 25-30% horyzontu a pozostałą annualizowaną alfą do końca inwestycji. Drugi wariant jest praktycznie ważniejszy, bo nie ma powodu zamieniać na benchmark spółek, których score percentile wzrósł.

Podobną interpretację daje wykres `long_term_200d_hold_decision_by_score_drop_after_25_30pct`. Zamiast pojedynczych punktów pokazuje on średnią i medianę dalszej annualizowanej alfy w koszykach `relative_score_percentile_change` po 25-30% czasu horyzontu. Dzięki temu łatwiej zobaczyć, że najbardziej ujemne koszyki, czyli największe spadki względnego percentyla score, są powiązane z gorszym dalszym zachowaniem spółki względem benchmarku.
