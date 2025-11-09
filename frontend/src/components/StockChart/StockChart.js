import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import StockChartView from "./StockChartView";
import ChartRangeButtons from "../common/ChartRangeButtons";
import { fetchStockPrices, fetchTransactionsForTicker } from "./utils/fetchUtils";
import { useChartRange } from "../common/useChartRange";
import "../../App.css";

function StockChart() {
  const { ticker } = useParams();
  const portfolioId = 1; // możesz później dynamicznie podać z kontekstu

  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z");

  const {
    range,
    customRange,
    handleRangeChange,
    handleCustomRangeChange,
    getEffectiveRange,
  } = useChartRange(totalStart, totalEnd);

  const [dataSets, setDataSets] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    if (!ticker) return;

    const { start, end, interval } = getEffectiveRange();

    const fetchData = async () => {
      try {
        const [priceData, transactionData] = await Promise.all([
          fetchStockPrices(ticker, start, end, interval),
          fetchTransactionsForTicker(portfolioId, ticker, start, end),
        ]);

        setDataSets([
          {
            ticker,
            data: priceData,
            color: "#4a90e2",
          },
        ]);
        setTransactions(transactionData);
      } catch (err) {
        console.error("Error fetching stock or transaction data:", err);
      }
    };

    fetchData();
  }, [ticker, range, customRange]);

  return (
    <div className="portfolio-chart-container">
      <h2 style={{ textAlign: "center", marginBottom: "10px" }}>
        {ticker?.toUpperCase()} — Stock Price History
      </h2>

      <div className="chart-layout">
        <div className="chart-section">
          <StockChartView
            dataSets={dataSets}
            range={range}
            transactions={transactions}
            disableClicks
          />
        </div>

        <div className="sidebar-section">
          <ChartRangeButtons
            range={range}
            onChange={handleRangeChange}
            onCustomRangeChange={handleCustomRangeChange}
          />
        </div>
      </div>
    </div>
  );
}

export default StockChart;
