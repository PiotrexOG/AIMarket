import React from "react";

function PositionList({ positions }) {
  if (!positions || positions.length === 0) {
    return <div className="no-positions">No open positions.</div>;
  }

  return (
    <div className="positions-list">
      {positions.map((p, i) => (
        <div key={i} className="position-row">
          <div className="col-ticker">{p.ticker}</div>
          <div className="col-shares">{p.shares}</div>
          <div className="col-price">${p.price.toFixed(2)}</div>
          <div className="col-value">${p.value.toFixed(2)}</div>
          <div className="col-value">{(p.value_of_portfolio * 100).toFixed(2)}</div>
        </div>
      ))}
    </div>
  );
}

export default PositionList;
