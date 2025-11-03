// src/components/PortfolioChart/ChartRangeButtons.js
import React from "react";

const ranges = ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y"];

function ChartRangeButtons({ range, onChange }) {
  return (
    <div className="range-controls">
      {ranges.map((r) => (
        <button
          key={r}
          className={`range-btn ${range === r ? "active" : ""}`}
          onClick={() => onChange(r)}
        >
          {r}
        </button>
      ))}
    </div>
  );
}

export default ChartRangeButtons;
