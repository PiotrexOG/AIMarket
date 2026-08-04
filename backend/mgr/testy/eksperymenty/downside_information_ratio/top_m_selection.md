# Downside Information Ratio - Top M Selection

**Wyniki PNG**

- `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_mean_annualized_return.png`
- `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_mean_downside_deviation.png`
- `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_downside_information_ratio.png`

Test Downside Information Ratio sprawdza, jak zachowuje się strategia kupowania co tydzień Top M% najwyżej ocenionych spółek, jeżeli oceniamy ją nie tylko przez średnioroczny zwrot, ale również przez ryzyko przegrania z benchmarkiem. Benchmarkiem jest Top 100%, czyli strategia kupowania w każdym tygodniu wszystkich dostępnych spółek po równo.

Dla każdego tygodnia spółki są sortowane według score od najlepszej do najsłabszej. Następnie liczony jest zwrot strategii Top M%. Wartości M zaczynają się od 1/18 koszyka, czyli ok. 5.56%, a potem rosną co 5 punktów procentowych aż do 100%. Oznacza to, że pierwsza strategia odpowiada mniej więcej kupowaniu tylko najlepszej spółki, a kolejne stopniowo rozszerzają portfel o słabsze pozycje rankingu.

Ważenie jest frakcyjne. Jeżeli wybrany procent nie kończy się dokładnie na pełnej liczbie spółek, ostatnia spółka w rankingu dostaje tylko częściową wagę. Przykładowo dla intuicyjnego M = 15% i 18 spółek pełne miejsce w koszyku mają pierwsze dwie spółki, bo każda odpowiada za ok. 5.56% całego rynku. Trzecia spółka dostaje tylko brakującą część: 15% - 5.56% - 5.56% = ok. 3.89%. Potem te udziały są normalizowane do 100% kapitału strategii.

Test jest liczony dla zakresu long-term 21-35 tygodni. Dla każdego horyzontu osobno brane są wszystkie tygodnie startowe, dla których istnieje kompletny przyszły zwrot. Naturalnie krótsze horyzonty mają więcej obserwacji: w tym uruchomieniu horyzont 21 tygodni miał 51 obserwacji tygodniowych, a horyzont 35 tygodni miał 37 obserwacji. W głównym podsumowaniu horyzonty są jednak uśredniane po równo, zgodnie z metodą `equal_weight_mean_across_horizons`.

Pierwszy wykres pokazuje średnioroczny zwrot strategii Top M% oraz benchmarku Top 100%. Benchmark osiągnął ok. 20.0% rocznie. Dla Top 5.56%, czyli praktycznie wyboru jednej najlepszej spółki tygodnia, średnioroczny zwrot wyniósł ok. 64.0%. Dla Top 10.56% było to ok. 44.0%, dla Top 15.56% ok. 37.9%, a dla Top 25.56% ok. 32.8%. Im mniejszy koszyk, tym wyższy średni zwrot, ale jednocześnie tym większa wrażliwość na pojedyncze trafienia i okresy, w których ranking nie zadziałał.

Sam średnioroczny zysk nie wystarcza jednak do oceny strategii. Dlatego drugi wykres pokazuje downside deviation, czyli odchylenie liczone tylko dla przypadków, w których strategia Top M% wypadła gorzej niż benchmark. To celowo lepsza miara niż zwykłe odchylenie standardowe, bo nie karze strategii za ekstremalnie dobre wyniki. Interesuje nas przede wszystkim bolesna strona zmienności: kiedy selekcja przegrywa z kupowaniem całego rynku.

Trzeci wykres łączy oba elementy w downside information ratio. Metryka jest liczona jako średnia annualizowana alfa podzielona przez downside deviation. Pokazuje więc, ile jednostek dodatkowego zysku strategia generuje na każdą jednostkę ryzyka przegrania z benchmarkiem.

Wyniki pokazują dwa różne profile strategii. Najbardziej agresywna selekcja, czyli Top 5.56%, daje najwyższy średnioroczny zwrot: ok. 64.0% rocznie, z alfą ok. 44.1 punktu procentowego ponad benchmark. Jednocześnie ma wysokie downside deviation, ok. 14.9 punktu procentowego, więc jej DIR wynosi ok. 3.01. To bardzo dobry wynik, ale okupiony dużym ryzykiem koncentracji.

Najwyższe downside information ratio pojawia się przy Top 65.56% i wynosi ok. 3.44. Stabilna rekomendacja wypada przy Top 60.56%, gdzie strategia osiąga ok. 25.3% rocznie, alfę ok. 5.34 punktu procentowego i downside deviation ok. 1.82 punktu procentowego, przy DIR ok. 3.37. Ten zakres nie maksymalizuje samego zysku, ale daje najlepszą relację dodatkowego zwrotu do ryzyka przegrania z benchmarkiem.

Interpretacja: test potwierdza, że score ma użyteczną siłę selekcyjną w horyzoncie 21-35 tygodni. Jeżeli celem inwestora jest maksymalizacja średniorocznego zwrotu i akceptuje on duże ryzyko koncentracji, sensowne jest patrzenie na najbardziej selektywne koszyki, szczególnie okolice Top 5.56%-15.56%. Jeżeli celem jest bardziej stabilna przewaga nad benchmarkiem, lepszym punktem odniesienia jest obszar Top 60.56%-65.56%, gdzie alfa jest mniejsza, ale ryzyko downside względem benchmarku spada jeszcze mocniej.
