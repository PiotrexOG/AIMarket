# Downside Information Ratio

Test Downside Information Ratio sprawdza, jak zachowuje się strategia kupowania co tydzień Top M% najwyżej ocenionych spółek, jeżeli oceniamy ją nie tylko przez średnioroczny zwrot, ale również przez ryzyko przegrania z benchmarkiem. Benchmarkiem jest Top 100%, czyli strategia kupowania w każdym tygodniu wszystkich dostępnych spółek po równo.

Dla każdego tygodnia spółki są sortowane według score od najlepszej do najsłabszej. Następnie liczony jest zwrot strategii Top M%. Wartości M zaczynają się od 1/18 koszyka, czyli ok. 5.56%, a potem rosną co 5 punktów procentowych aż do 100%. Oznacza to, że pierwsza strategia odpowiada mniej więcej kupowaniu tylko najlepszej spółki, a kolejne stopniowo rozszerzają portfel o słabsze pozycje rankingu.

Ważenie jest frakcyjne. Jeżeli wybrany procent nie kończy się dokładnie na pełnej liczbie spółek, ostatnia spółka w rankingu dostaje tylko częściową wagę. Przykładowo dla intuicyjnego M = 15% i 18 spółek pełne miejsce w koszyku mają pierwsze dwie spółki, bo każda odpowiada za ok. 5.56% całego rynku. Trzecia spółka dostaje tylko brakującą część: 15% - 5.56% - 5.56% = ok. 3.89%. Potem te udziały są normalizowane do 100% kapitału strategii.

Test jest liczony dla zakresu long-term 21-35 tygodni. Dla każdego horyzontu osobno brane są wszystkie tygodnie startowe, dla których istnieje kompletny przyszły zwrot. Naturalnie krótsze horyzonty mają więcej obserwacji: horyzont 21 tygodni miał 51 obserwacji tygodniowych, a horyzont 35 tygodni miał 37 obserwacji.  Jest to kompromis: wykorzystujemy cały możliwy zakres badania, ale nie pozwalamy, żeby sam fakt większej liczby obserwacji dla krótszych horyzontów całkowicie zdominował wynik.

## 1. Czy selektywna strategia Top M daje wyższy zwrot?

Pierwszy wykres pokazuje średnioroczny zwrot strategii Top M% oraz benchmarku Top 100%.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_mean_annualized_return.png`

Widać na nim wyraźną alfę dla bardziej selektywnych strategii. Benchmark, czyli Top 100%, osiągnął ok. 20.0% rocznie. Dla Top 5.56%, czyli praktycznie wyboru jednej najlepszej spółki tygodnia, średnioroczny zwrot wyniósł ok. 64.0%. Dla Top 10.56% było to ok. 44.0%, dla Top 15.56% ok. 37.9%, a dla Top 25.56% ok. 32.8%.

Im mniejszy koszyk, tym wyższy średni zwrot, ale jednocześnie tym większa wrażliwość na pojedyncze trafienia i okresy, w których ranking nie zadziałał. Dlatego sam średnioroczny zysk nie wystarcza do oceny strategii.

## 2. Gdzie pojawia się bolesna strona błędu?

Drugi wykres pokazuje downside deviation, czyli odchylenie liczone tylko dla przypadków, w których strategia Top M% wypadła gorzej niż benchmark.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_mean_downside_deviation.png`

To celowo lepsza miara niż zwykłe odchylenie standardowe, bo nie karze strategii za ekstremalnie dobre wyniki. W tym systemie duża część przewagi może powstawać właśnie w takich dodatnich odchyleniach, więc interesuje nas przede wszystkim bolesna strona zmienności: kiedy selekcja przegrywa z kupowaniem całego rynku.

Wyniki pokazują dwa różne profile strategii. Najbardziej agresywna selekcja, czyli Top 5.56%, daje najwyższy średnioroczny zwrot: ok. 64.0% rocznie, z alfą ok. 44.1 punktu procentowego ponad benchmark. Jednocześnie ma jednak wysokie downside deviation, ok. 14.9 punktu procentowego. To bardzo dobry wariant zwrotu, ale okupiony dużym ryzykiem koncentracji.

## 3. Który Top M ma najlepszą relację zysku do downside risk?

Trzeci wykres łączy oba elementy w downside information ratio.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/top_m_selection/long_term_200d_downside_information_ratio.png`

Metryka jest liczona jako średnia annualizowana alfa podzielona przez downside deviation. Pokazuje więc, ile jednostek dodatkowego zysku strategia generuje na każdą jednostkę ryzyka przegrania z benchmarkiem. Wartości powyżej 1 są bardzo dobre, bo oznaczają, że premia za selekcję jest większa niż typowy negatywny błąd względem benchmarku.

Dla Top 5.56% DIR wynosi ok. 3.01. Najwyższe downside information ratio pojawia się przy Top 65.56% i wynosi ok. 3.44. Stabilna rekomendacja wypada przy Top 60.56%, gdzie strategia osiąga ok. 25.3% rocznie, alfę ok. 5.34 punktu procentowego i downside deviation ok. 1.82 punktu procentowego, przy DIR ok. 3.37.

Ten zakres nie maksymalizuje samego zysku, ale daje najlepszą relację dodatkowego zwrotu do ryzyka przegrania z benchmarkiem. Innymi słowy: agresywne koszyki Top 5.56%-15.56% są najlepsze, jeśli celem jest maksymalizacja średniego zwrotu, natomiast okolice Top 60.56%-65.56% są lepszym punktem odniesienia, jeśli celem jest stabilniejsza przewaga nad benchmarkiem.

## 4. Czy wynik zależy od kilku specyficznych okresów rynku?

Po głównym teście przeprowadzono dodatkowy eksperyment, w którym chodziło o sprawdzenie, czy dobre wyniki downside information ratio wynikają z kilku przypadkowych sytuacji rynkowych, czy są stabilne dla różnych poziomów zwrotu benchmarku.

Obserwacje zostały podzielone na 10 koszyków według średniego annualizowanego zwrotu benchmarku w danym okresie. Bucket 01 obejmuje najsłabsze okresy benchmarku, od ok. -3.35% do 6.92% rocznie, a Bucket 10 obejmuje najmocniejsze okresy, od ok. 39.89% do 103.96% rocznie. Każdy koszyk zawiera 66 obserwacji.

Następnie dla każdego koszyka benchmarku i każdego Top M equivalent policzono trzy metryki:

- średnią annualizowaną alfę strategii względem benchmarku,
- downside deviation,
- downside information ratio.

Dzięki temu powstały heatmapy, w których jeden wymiar pokazuje koszyk zwrotu benchmarku, a drugi pokazuje wariant strategii Top M. To pozwala zobaczyć, czy przewaga strategii pojawia się tylko w jednym typie rynku, czy utrzymuje się szerzej.

## 5. Benchmark buckets: średnia alfa

Pierwsza heatmapa pokazuje średnią annualizowaną alfę strategii w podziale na koszyk zwrotu benchmarku i Top M equivalent.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/benchmark_return_buckets/long_term_200d_heatmap_annualized_alpha.png`

Ten wykres odpowiada na pytanie: czy strategia generuje dodatni nadmiarowy zwrot tylko wtedy, gdy benchmark zachowuje się w określony sposób, czy raczej jej przewaga jest widoczna w różnych warunkach rynku.

W aktualnych wynikach dla Top 60.56% oraz Top 65.56% alfa jest dodatnia we wszystkich 10 koszykach benchmarku. Dla Top 60.56% najniższa średnia alfa w pojedynczym koszyku wynosi ok. 2.7 punktu procentowego, a dla Top 65.56% ok. 1.9 punktu procentowego. To ważne, bo sugeruje, że stabilna rekomendacja nie opiera się wyłącznie na jednym wyjątkowym typie okresu rynkowego.

## 6. Benchmark buckets: downside deviation

Druga heatmapa pokazuje downside deviation w tym samym podziale.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/benchmark_return_buckets/long_term_200d_heatmap_downside_deviation.png`

Ten wykres pozwala sprawdzić, czy niska wartość downside deviation w głównym teście nie wynika tylko z uśrednienia bardzo różnych sytuacji. Innymi słowy: interesuje nas, czy strategia ma rozsądny profil przegranych także w poszczególnych koszykach benchmarku, a nie tylko w agregacie.

Widać, że downside deviation zmienia się między koszykami i strategiami, co jest naturalne: inne ryzyko ma bardzo skoncentrowany Top 5.56%, a inne szeroki Top 60.56%-65.56%. Mimo tego w obszarze stabilnej rekomendacji downside deviation pozostaje relatywnie niskie w wielu koszykach benchmarku. To wzmacnia interpretację, że stabilność DIR nie jest wyłącznie efektem kilku bardzo dobrych trafień.

## 7. Benchmark buckets: downside information ratio

Trzecia heatmapa pokazuje downside information ratio w podziale na koszyk benchmarku i Top M equivalent.

**PNG:** `backend/data/results/downside_information_ratio/21-35w/benchmark_return_buckets/long_term_200d_heatmap_downside_information_ratio.png`

Ten wykres jest najbliższy głównej tezie testu. Pokazuje, gdzie dodatkowy zwrot strategii jest korzystny względem downside risk. Jeżeli wysokie wartości DIR pojawiałyby się tylko w jednym koszyku benchmarku, wtedy wynik głównego testu byłby mniej przekonujący. Jeżeli natomiast dodatnie i wysokie wartości pojawiają się w wielu koszykach, to znaczy, że przewaga modelu jest bardziej stabilna.

W aktualnym wyniku obszar Top 60.56%-65.56% pozostaje dodatni we wszystkich koszykach benchmarku, a miejscami osiąga bardzo wysokie DIR, szczególnie tam, gdzie downside deviation jest niskie. Takie bardzo wysokie wartości należy interpretować ostrożnie, bo mały mianownik może mocno podbijać ratio, ale sam fakt dodatniej alfy i niskiego downside risk w wielu koszykach jest ważniejszy niż pojedyncze ekstremalne maksimum.

## Interpretacja całości

Test potwierdza, że score ma użyteczną siłę selekcyjną w horyzoncie 21-35 tygodni. Jeżeli celem inwestora jest maksymalizacja średniorocznego zwrotu i akceptuje on duże ryzyko koncentracji, sensowne jest patrzenie na najbardziej selektywne koszyki, szczególnie okolice Top 5.56%-15.56%.

Jeżeli celem jest bardziej stabilna przewaga nad benchmarkiem, lepszym punktem odniesienia jest obszar Top 60.56%-65.56%, gdzie alfa jest mniejsza, ale ryzyko downside względem benchmarku spada jeszcze mocniej. Dodatkowy eksperyment wzmacnia ten wniosek: dodatnia alfa i korzystny profil DIR nie wynikają wyłącznie z jednego przypadkowego typu rynku, tylko pojawiają się w różnych koszykach zwrotu benchmarku.
