// src/components/PortfolioChart/CustomTooltip.js
import React from "react";

const CustomTooltip = ({ active, payload }) => {
  if (active && payload?.length) {
    const baseData = payload[0].payload;
    const date = new Date(baseData.date);

    const formattedDate = date.toLocaleDateString("en-CA");
    const formattedTime = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    return (
      <div className="custom-tooltip">
        <div className="tooltip-date">{formattedDate}</div>
        <div className="tooltip-time">
          {formattedTime} ({timeZone})
        </div>

        {/* 🔹 Iterujemy po wszystkich liniach */}
        <div className="tooltip-value">
          {payload.map((entry) => (
            <div key={entry.dataKey} style={{ color: entry.color }}>
              {entry.name}: <strong>${Number(entry.value).toFixed(2)}</strong>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
};

export default CustomTooltip;
