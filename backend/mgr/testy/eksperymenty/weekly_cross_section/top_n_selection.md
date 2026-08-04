# Weekly Cross Section - Top N Selection

**Wyniki PNG**

- `backend/data/results/weekly_cross_section/top_n_selection/long_term_200d_top_n_annualized_return.png`

Test Top N Selection pokazuje, jak zmienia się roczny zwrot strategii kupującej co tydzień Top N najwyżej ocenionych spółek. Dla każdego horyzontu inwestycyjnego brane są wszystkie dostępne tygodnie startowe. W każdym takim tygodniu spółki są sortowane według score, wybierane jest Top N, liczony jest ich średni przyszły zwrot, a następnie wyniki są uśredniane i annualizowane.

Top 18 pełni rolę benchmarku, ponieważ oznacza kupno wszystkich 18 spółek po równo. Pozostałe linie pokazują coraz bardziej selektywne strategie: Top 14, Top 9, Top 7, aż do Top 1.

Eksperyment w aktualnej konfiguracji jest liczony dla horyzontu `long_term_200d`, czyli zakresu 21-35 tygodni. Dla long-term liczba obserwacji maleje wraz z horyzontem: dla 21 tygodni było 51 tygodniowych próbek, a dla 35 tygodni 37 próbek. Jest to naturalne, bo im dłuższy horyzont przyszłego zwrotu, tym mniej dat startowych ma jeszcze kompletny przyszły okres zwrotu.

Wyniki dla zakresu 21-35 tygodni:

- Top 1: średnio ok. 60.7% rocznie,
- Top 2: ok. 41.8% rocznie,
- Top 3: ok. 36.3% rocznie,
- Top 5: ok. 32.2% rocznie,
- Top 7: ok. 28.3% rocznie,
- Top 9: ok. 26.9% rocznie,
- Top 14: ok. 21.2% rocznie,
- Top 18: ok. 19.5% rocznie.

Interpretacja: im bardziej elitarna selekcja, tym wyższy średni zwrot, ale też większa zmienność między horyzontami. Top 1 daje najwyższy wynik, ale jest najbardziej wrażliwy na pojedyncze trafienia. Top 18 jest najstabilniejsze, ale najbliższe benchmarkowi całego koszyka.
