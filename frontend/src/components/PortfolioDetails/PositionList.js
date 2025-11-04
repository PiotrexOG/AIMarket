// src/components/PortfolioDetails/PositionList.js
import React from "react";

function PositionList({ positions }) {
  if (!positions || positions.length === 0) {
    return <p>No open positions.</p>;
  }

  return (
    <ul className="position-list">
      {positions.map((p, i) => (
        <li key={i} className="position-item">
          <span className="ticker">{p.ticker}</span>
          <span className="shares">{p.shares}</span>
          <span className="symbol">@</span>
          <span className="price">${p.price.toFixed(2)}</span>
          <span className="symbol">=</span>
          <span className="value">${p.value.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
}

export default PositionList;