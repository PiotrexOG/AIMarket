// src/components/PortfolioChart/CustomTooltip.js
import React from "react";

const CustomTooltip = ({ active, payload }) => {
  if (active && payload?.length) {
    const data = payload[0].payload;
    const date = new Date(data.date);

    const formattedDate = date.toLocaleDateString("en-CA");
    const formattedTime = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-date">{formattedDate}</div>
        <div className="tooltip-time">
          {formattedTime} ({timeZone})
        </div>
        <div className="tooltip-value">
          Portfolio Value: <strong>${data.portfolio_value.toFixed(2)}</strong>
        </div>
        {data.cash && (
          <div className="tooltip-cash">
            Cash: <strong>${data.cash.toFixed(2)}</strong>
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default CustomTooltip;
