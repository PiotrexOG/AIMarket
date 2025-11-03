// src/components/PortfolioChart/PortfolioChart.js
import React, { useState, useEffect } from "react";
import ChartView from "./ChartView";
import ChartRangeButtons from "./ChartRangeButtons";
import PortfolioChangeDisplay from "./PortfolioChangeDisplay";
import { getRangeDates, getIntervalForRange } from "./utils/intervalUtils";
import { fetchValuation } from "./utils/fetchUtils";
import "../../App.css";


function PortfolioChart({ onPointClick }) {
  const [data, setData] = useState([]);
  const [range, setRange] = useState("1M");
  const userId = 2;

  // pełny zakres symulacji
  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z");

  useEffect(() => {
    const { start, end } = getRangeDates(range, totalStart, totalEnd);
    const interval = getIntervalForRange(range);

    fetchValuation(userId, start, end, interval)
      .then((json) => setData(json))
      .catch((err) => console.error("Fetch valuation error:", err));
  }, [range, userId]);

  const handlePointClick = (point) => {
    if (onPointClick) onPointClick(point);
  };

return (
  <div className="portfolio-chart-container">
    <div className="chart-layout">
      {/* 🔹 Lewa sekcja: wykres */}
      <div className="chart-section">
        <ChartView data={data} range={range} onPointClick={handlePointClick} />
      </div>

      {/* 🔹 Prawa sekcja: zmiana i przyciski */}
      <div className="sidebar-section">
        <PortfolioChangeDisplay data={data} />
        <ChartRangeButtons range={range} onChange={setRange} />
      </div>
    </div>
  </div>
);

}

export default PortfolioChart;
