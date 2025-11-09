// src/components/StockChart/utils/fetchUtils.js
export const fetchStockPrices = async (ticker, start, end, interval) => {
  const url = `http://localhost:8000/market-data/${ticker}/valuation?start=${encodeURIComponent(
    start
  )}&end=${encodeURIComponent(end)}&interval=${interval}`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch stock price data");
  return response.json();
};

export const fetchTickers = async () => {
  const url = "http://localhost:8000/market-data/tickers";
  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch tickers");
  return response.json();
};

export const fetchTransactionsForTicker = async (portfolioId, ticker, start, end) => {
  const url = `http://localhost:8000/portfolios/${portfolioId}/transactions/${ticker}?start=${encodeURIComponent(
    start
  )}&end=${encodeURIComponent(end)}`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch transaction data");
  return response.json(); // lista obiektów { datetime, quantity, ratio }
};
