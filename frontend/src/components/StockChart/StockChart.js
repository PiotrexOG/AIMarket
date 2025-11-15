import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import StockChartView from "./StockChartView";
import ChartRangeButtons from "../common/ChartRangeButtons";
import { fetchStockPrices, fetchTransactionsForTicker } from "./utils/fetchUtils";
import { useChartRange } from "../common/useChartRange";
import "../../App.css";

function StockChart({ onTransactionsSelect, selectedUserIds = [], colorPalette = [] }) {
  const { ticker } = useParams();
  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z");
  
  const { 
    range, 
    customRange, 
    handleRangeChange, 
    handleCustomRangeChange, 
    getEffectiveRange 
  } = useChartRange(totalStart, totalEnd);

  const [dataSets, setDataSets] = useState([]);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    if (!ticker || selectedUserIds.length === 0) {
      setDataSets([]);
      setTransactions([]);
      return;
    }

    const { start, end, interval } = getEffectiveRange();
    
    const fetchAll = async () => {
      try {
        // 🔹 1. Fetch ceny akcji (raz, wspólne)
        const priceData = await fetchStockPrices(ticker, start, end, interval);
        
        // 🔹 2. Fetch transakcji dla każdego usera osobno
        const allTransactions = await Promise.all(
          selectedUserIds.map((userId) => 
            fetchTransactionsForTicker(userId, ticker, start, end)
          )
        );

        // 🔹 3. Połącz dane użytkowników z kolorami
        const userTransactions = selectedUserIds.map((userId, idx) => ({
          userId,
          color: colorPalette[idx % colorPalette.length],
          transactions: allTransactions[idx],
        }));

        setDataSets([{ ticker, data: priceData, color: "#4a90e2" }]);
        setTransactions(userTransactions);
      } catch (err) {
        console.error("Error fetching stock or transaction data:", err);
      }
    };

    fetchAll();
  }, [ticker, range, customRange, selectedUserIds]);

const handleMarkerClick = (transactions = []) => {
    onTransactionsSelect?.(transactions);
};


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
            transactionsByUser={transactions} 
            onMarkerClick={handleMarkerClick} 
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