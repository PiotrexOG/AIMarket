// PortfolioDetails.js

import React, { useState, useEffect, useMemo } from "react";
import PositionList from "./PositionList";
import PortfolioPieChart from "./PortfolioPieChart";
import "./PortfolioDetails.css";
import "../../App.css";

function PortfolioDetails({
  userId,
  timestamp,
  userName,
  onClose,
  color,
}) {
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

  const pieData = useMemo(() => {
    if (!details?.positions) return [];

    const grouped = [];
    let otherValue = 0;

    details.positions.forEach((p) => {
      const percentage = p.value_of_portfolio * 100;

      if (percentage < 3) {
        otherValue += p.value;
      } else {
        grouped.push({
          name: p.ticker,
          value: p.value,
        });
      }
    });

    if (otherValue > 0) {
      grouped.push({
        name: "Other",
        value: otherValue,
      });
    }

    return grouped;
  }, [details]);

  if (!details) {
    return (
      <div className="portfolio-details-container">
        Loading details...
      </div>
    );
  }

  return (
    <div
      className="portfolio-details-container"
      style={{ border: `3px solid ${color}` }}
    >
      <div className="user-label" style={{ backgroundColor: color }}>
        {userName}
      </div>

      <PortfolioPieChart
        positions={details.positions}
        portfolioValue={details.portfolio_value}
        cash={details.cash}
      />

      <div className="user-summary">
        <div className="summary-row">
          <div className="summary-label">Portfolio Value</div>
          <div className="summary-value">
            ${details.portfolio_value.toFixed(2)}
          </div>
        </div>

        <div className="summary-row">
          <div className="summary-label">Cash</div>
          <div className="summary-value">
            ${details.cash.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="header-row positions-header">
        <div>Ticker</div>
        <div>Shares</div>
        <div>Avg Price</div>
        <div>Value</div>
        <div>Part of Portfolio %</div>
      </div>

      <PositionList positions={details.positions} />
    </div>
  );
}

export default PortfolioDetails;