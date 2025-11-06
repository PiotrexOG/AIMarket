import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import ChartView from "../PortfolioChart/ChartView";
import ChartRangeButtons from "../PortfolioChart/ChartRangeButtons";
import { getRangeDates, getIntervalForRange } from "../PortfolioChart/utils/intervalUtils";
import { fetchStockPrices } from "./utils/fetchUtils";
import "../../App.css";

function StockChart() {
  const { ticker } = useParams();
  const [dataSet, setDataSet] = useState(null);
  const [range, setRange] = useState("1M");

  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z");

  useEffect(() => {
    if (!ticker) return;

    const { start, end } = getRangeDates(range, totalStart, totalEnd);
    const interval = getIntervalForRange(range);

    const fetchData = async () => {
      try {
        const data = await fetchStockPrices(ticker, start, end, interval);
        setDataSet({
          ticker,
          data,
          color: "#4a90e2",
        });
      } catch (err) {
        console.error("Error fetching stock data:", err);
      }
    };

    fetchData();
  }, [ticker, range]);

  return (
    <div className="portfolio-chart-container">
      <h2 style={{ textAlign: "center", marginBottom: "10px" }}>
        {ticker.toUpperCase()} — Stock Price History
      </h2>

      <div className="chart-layout">
        <div className="chart-section">
          {dataSet ? (
            <ChartView dataSets={[dataSet]} range={range} disableClicks />
          ) : (
            <p style={{ textAlign: "center" }}>Loading data...</p>
          )}
        </div>

        <div className="sidebar-section">
          <div className="portfolio-change-display">
            {dataSet?.data?.percent_change !== undefined && (
              <>
                <h3>Change</h3>
                <p
                  className={`change-value ${
                    dataSet.data.percent_change >= 0 ? "positive" : "negative"
                  }`}
                >
                  {dataSet.data.percent_change >= 0 ? "+" : ""}
                  {dataSet.data.percent_change.toFixed(2)}%
                </p>
              </>
            )}
          </div>

          <ChartRangeButtons range={range} onChange={setRange} />
        </div>
      </div>
    </div>
  );
}

export default StockChart;
