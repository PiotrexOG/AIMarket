import React from "react";

function StockChangeDisplay({ dataSets }) {
  if (!dataSets || dataSets.length === 0 || !dataSets[0]?.data) {
    return (
      <div className="portfolio-change-display">
        <p className="change-label">No data</p>
      </div>
    );
  }

  const stockData = dataSets[0].data;
  const change = Number(stockData.percent_change ?? 0);
  const safeChange = isNaN(change) ? 0 : change;
  const sign = safeChange >= 0 ? "+" : "";
  const isPositive = safeChange >= 0;

  return (
    <div className="portfolio-change-display">
      <h3>Stock Performance</h3>
      
      <p className={`change-value ${isPositive ? "positive" : "negative"}`}>
        {sign}{safeChange.toFixed(2)}%
      </p>
    
    </div>
  );
}

export default StockChangeDisplay;