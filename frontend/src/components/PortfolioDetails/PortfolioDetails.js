// src/components/PortfolioDetails/PortfolioDetails.js
import React, { useState, useEffect } from "react";
import PositionList from "./PositionList";
import { formatTimestamp } from "./utils/formatUtils";
import "../../App.css";

function PortfolioDetails({ userId, timestamp, userName, onClose, color }) {
  const [details, setDetails] = useState(null);

  useEffect(() => {
    const encodedTime = encodeURIComponent(timestamp);
    fetch(
      `http://localhost:8000/portfolios/${userId}/state?date=${encodedTime}&detailed=True`
    )
      .then((res) => res.json())
      .then((json) => setDetails(json))
      .catch((err) => console.error("DEBUG — fetch error:", err));
  }, [timestamp, userId]);

  if (!details) return <div className="portfolio-details-container">Loading details...</div>;

  return (
    <div className="portfolio-details-container" style={{ border: `3px solid ${color}` }}>
      <div className="user-label" style={{ backgroundColor: color }}>
        {userName}
      </div>

      <div className="user-summary">
        <div className="summary-row">
          <div className="summary-label">Portfolio Value</div>
          <div className="summary-value">${details.portfolio_value.toFixed(2)}</div>
        </div>

        <div className="summary-row">
          <div className="summary-label">Cash</div>
          <div className="summary-value">${details.cash.toFixed(2)}</div>
        </div>
      </div>


      <div className="header-row positions-header">
        <div>Ticker</div>
        <div>Shares</div>
        <div>Avg Price</div>
        <div>Value</div>
      </div>

      <PositionList positions={details.positions} />
    </div>

  );
}

export default PortfolioDetails;
