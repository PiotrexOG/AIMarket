// src/components/PortfolioChart/PortfolioChart.js
import React, { useState, useEffect } from "react";
import ChartView from "./ChartView";
import ChartRangeButtons from "./ChartRangeButtons";
import PortfolioChangeDisplay from "./PortfolioChangeDisplay";
import { getRangeDates, getIntervalForRange } from "./utils/intervalUtils";
import { fetchValuation } from "./utils/fetchUtils";
import "../../App.css";


function PortfolioChart({ onPointClick, userIds, colorPalette }) {
  const [dataSets, setDataSets] = useState([]); // wiele wykresów
  const [range, setRange] = useState("1M");

  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z");

  useEffect(() => {
      if (userIds.length === 0) {
        setDataSets([]);
        return;
      }

      const { start, end } = getRangeDates(range, totalStart, totalEnd);
      const interval = getIntervalForRange(range);

      const fetchAll = async () => {
        try {
          const results = await Promise.all(
            userIds.map((id) => fetchValuation(id, start, end, interval))
          );

          // 🔹 Przypisujemy kolor każdemu userowi
          const merged = results.map((data, idx) => ({
            userId: userIds[idx],
            data,
            color: colorPalette[idx % colorPalette.length],
          }));

          setDataSets(merged);
        } catch (err) {
          console.error("Fetch valuation error:", err);
        }
      };

      fetchAll();
  }, [range, userIds, colorPalette]);

  const handlePointClick = (point) => {
    if (onPointClick) onPointClick(point);
  };

  return (
    <div className="portfolio-chart-container">
      <div className="chart-layout">
        <div className="chart-section">
          <ChartView dataSets={dataSets} range={range} onPointClick={handlePointClick} colorPalette={colorPalette} />
        </div>

        <div className="sidebar-section">
          <PortfolioChangeDisplay dataSets={dataSets} />
          <ChartRangeButtons range={range} onChange={setRange} />
        </div>
      </div>
    </div>
  );
}


export default PortfolioChart;
