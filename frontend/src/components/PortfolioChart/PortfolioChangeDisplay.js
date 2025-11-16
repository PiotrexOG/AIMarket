import React from "react";

function PortfolioChangeDisplay({ dataSets, selectedUsers }) {
  if (!dataSets || dataSets.length === 0) {
    return (
      <div className="portfolio-change-display">
        <p className="change-label">No data</p>
      </div>
    );
  }

  // 🔹 Sortowanie malejąco po procentowej zmianie
  const sortedData = [...dataSets].sort((a, b) => {
    const aChange = Number(a.data?.percent_change ?? 0);
    const bChange = Number(b.data?.percent_change ?? 0);
    return bChange - aChange;
  });

  return (
    <div className="portfolio-change-display">
      <h3 style={{ marginBottom: "8px" }}>Changes by user</h3>

      {sortedData.map((set) => {
        const change = Number(set.data?.percent_change ?? 0);
        const safeChange = isNaN(change) ? 0 : change;
        const sign = safeChange >= 0 ? "+" : "";
        const isPositive = safeChange >= 0;
        const userName = selectedUsers[set.userId] || `User ${set.userId}`;

        return (
          <p
            key={set.userId}
            className={`change-value ${isPositive ? "positive" : "negative"}`}
          >
            <span style={{ color: set.color }}>{userName}:</span>{" "}
            {`${sign}${safeChange.toFixed(2)}%`}
          </p>
        );
      })}
    </div>
  );
}

export default PortfolioChangeDisplay;