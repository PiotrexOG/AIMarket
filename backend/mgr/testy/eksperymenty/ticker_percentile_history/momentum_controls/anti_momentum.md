# Ticker Percentile History - Momentum Controls - Anti Momentum

**Wyniki PNG**

- `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/anti_momentum/score_to_future_annualized_return_correlation_by_ticker.png`
- `backend/data/results/ticker_percentile_history/long_term_200d/momentum_controls/anti_momentum/score_to_trailing_jegadeesh_titman_return_correlation_by_ticker.png`

Kolejnym testem była analiza w ramach pojedynczych spółek, przedstawiona na wykresie `score_to_future_annualized_return_correlation_by_ticker`. Tutaj pytanie jest inne niż w klasycznym IC. Nie sprawdzamy już, czy w danym tygodniu lepiej ocenione spółki zachowywały się lepiej od innych spółek, ale czy dla tej samej spółki wyższy score w jednym tygodniu oznaczał wyższy przyszły zwrot niż jej niższy score w innym tygodniu.

Wynik średnio okazał się słaby i ujemny: średnia korelacja po tickerach wynosi ok. -0.245. Nie jest to zaskakujące, ponieważ model był projektowany jako narzędzie przekrojowe: co tydzień porównuje spółki między sobą, ale nie musi mieć stabilnej absolutnej skali dla tej samej spółki w czasie.

To rozróżnienie jest ważne. Model może dobrze odpowiadać na pytanie "która spółka wygląda lepiej od innych w tym tygodniu", a jednocześnie słabiej odpowiadać na pytanie "czy ta sama spółka wygląda dzisiaj lepiej niż kilka tygodni temu". Ujemny wynik na `score_to_future_annualized_return_correlation_by_ticker` nie unieważnia więc głównego sygnału przekrojowego, ale ogranicza zastosowanie modelu jako narzędzia absolutnego timingu dla pojedynczego tickera.

Dodatkowo sprawdzono, czy score modelu nie jest po prostu ukrytym momentum. Wykres `score_to_trailing_jegadeesh_titman_return_correlation_by_ticker` pokazuje korelację między score danej spółki a jej trailing return liczonym według podejścia Jegadeesha-Titmana, z pominięciem ostatnich 4 tygodni. Wynik wskazuje na umiarkowany związek: średnia korelacja po tickerach wynosi ok. 0.260. Model w pewnym stopniu może więc korzystać z informacji podobnej do momentum, czyli lepiej oceniać spółki, które wcześniej zachowywały się dobrze. Sama korelacja z momentum nie wystarcza jednak, aby uznać, że model jest tylko prostym momentum.
