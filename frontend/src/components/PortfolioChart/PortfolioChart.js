import React, { useState, useEffect } from "react";
import PortfolioChartView from "./PortfolioChartView";
import ChartRangeButtons from "../common/ChartRangeButtons";
import PortfolioChangeDisplay from "./PortfolioChangeDisplay";
import { fetchValuation } from "./utils/fetchUtils";
import { useChartRange } from "../common/useChartRange";
import "../../App.css";

function PortfolioChart({ onPointClick, userIds, colorPalette }) {
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

  useEffect(() => {
    if (!userIds.length) {
      setDataSets([]);
      return;
    }

    const { start, end, interval } = getEffectiveRange();

    const fetchAll = async () => {
      try {
        const results = await Promise.all(
          userIds.map((id) => fetchValuation(id, start, end, interval))
        );

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
  }, [range, customRange, userIds, colorPalette]);

  return (
    <div className="portfolio-chart-container">
      <div className="chart-layout">
        <div className="chart-section">
          <PortfolioChartView
            dataSets={dataSets}
            range={range}
            onPointClick={onPointClick}
            colorPalette={colorPalette}
          />
        </div>

        <div className="sidebar-section">
          <PortfolioChangeDisplay dataSets={dataSets} />
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

export default PortfolioChart;
