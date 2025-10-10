import React, { useState, useEffect } from "react";

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

  return (
  <div className="details-container">
    <button onClick={onClose}>Close</button>
    <h2>User {details.user_id} — {timestamp}</h2>
    <p><strong>Cash:</strong> ${details.cash.toFixed(2)}</p>
    <p><strong>Portfolio Value:</strong> ${details.portfolio_value.toFixed(2)}</p>
    <h3>Positions</h3>
    <ul>
      {details.positions.map((p, i) => (
        <li key={i}>
          {p.ticker} — {p.shares} shares @ ${p.price.toFixed(2)} = ${p.value.toFixed(2)}
        </li>
      ))}
    </ul>
  </div>
);

}

export default PortfolioDetails;
