// src/components/PortfolioChart/PortfolioChangeDisplay.js
import React from "react";

function PortfolioChangeDisplay({ data }) {
  const isPositive = data.percent_change >= 0;
  const sign = isPositive ? "+" : "";
  const colorClass = isPositive ? "positive" : "negative";

  return (
    <div className="portfolio-change-display">
      <h2 className={`change-value ${colorClass}`}>
        {`${sign}${data.percent_change}%`}
      </h2>
      <p className="change-label">Change in selected period</p>
    </div>
  );
}

export default PortfolioChangeDisplay;

