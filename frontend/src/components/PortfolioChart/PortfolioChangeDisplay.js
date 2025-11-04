// src/components/PortfolioChart/PortfolioChangeDisplay.js
import React from "react";

function PortfolioChangeDisplay({ dataSets }) {
  if (!dataSets || dataSets.length === 0) {
    return (
      <div className="portfolio-change-display">
        <p className="change-label">No data</p>
      </div>
    );
  }

  return (
    <div className="portfolio-change-display">
      <h3 style={{ marginBottom: "8px" }}>Changes by user</h3>
      {dataSets.map((set) => {
        const change = Number(set.data?.percent_change ?? 0);
        const safeChange = isNaN(change) ? 0 : change; // fallback na 0
        const isPositive = safeChange >= 0;
        const sign = isPositive ? "+" : "";
        const colorClass = isPositive ? "positive" : "negative";

        return (
          <p key={set.userId} className={`change-value ${colorClass}`}>
            User {set.userId}: {`${sign}${safeChange.toFixed(2)}%`}
          </p>
        );
      })}

    </div>
  );
}

export default PortfolioChangeDisplay;
