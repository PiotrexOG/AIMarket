// src/components/PortfolioDetails/PortfolioDetails.js
import React, { useState, useEffect } from "react";
import PositionList from "./PositionList";
import { formatTimestamp } from "./utils/formatUtils";
import "../../App.css";


function PortfolioDetails({ userId, timestamp, onClose }) {
  const [details, setDetails] = useState(null);

  useEffect(() => {
    const encodedTime = encodeURIComponent(timestamp);
    fetch(`http://localhost:8000/portfolios/${userId}/state?date=${encodedTime}&detailed=True`)
      .then((res) => res.json())
      .then((json) => setDetails(json))
      .catch((err) => console.error("DEBUG — fetch error:", err));
  }, [timestamp, userId]);

  if (!details) return <div>Loading details...</div>;

  const formatted = formatTimestamp(timestamp);

  return (
    <div className="details-container">
      <button className="close-btn" onClick={onClose}>✕ Close</button>

      <div className="timestamp-info">
        <div className="date">{formatted.date}</div>
        <div className="time">
          {formatted.time} ({formatted.timeZone})
        </div>
      </div>

      <div className="summary">
        <p><strong>💵 Cash:</strong> ${details.cash.toFixed(2)}</p>
        <p><strong>📊 Portfolio Value:</strong> ${details.portfolio_value.toFixed(2)}</p>
      </div>

      <h3>Positions</h3>
      <PositionList positions={details.positions} />
    </div>
  );
}

export default PortfolioDetails;
