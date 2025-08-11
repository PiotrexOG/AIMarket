import React, { useState, useEffect } from "react";

function PortfolioDetails({ userId, timestamp, onClose }) {
  const [details, setDetails] = useState(null);

useEffect(() => {
  console.log("DEBUG — timestamp received in PortfolioDetails:", timestamp);
  console.log("DEBUG — encoded timestamp for fetch:", encodeURIComponent(timestamp));
  
  const encodedTime = encodeURIComponent(timestamp);
  fetch(`http://localhost:8000/users/${userId}/daily-portfolio/${encodedTime}`)
    .then((res) => res.json())
    .then((json) => {
      console.log("DEBUG — fetched details:", json);
      setDetails(json);
    })
    .catch((err) => console.error("DEBUG — fetch error:", err));
}, [timestamp, userId]);


  if (!details) return <div>Loading details...</div>;

  return (
    <div style={{ marginTop: "20px", border: "1px solid #ccc", padding: "10px" }}>
      <button onClick={onClose}>Close</button>
      <h2>User {details.user_id} — {timestamp}</h2>
      <p>Cash: ${details.cash.toFixed(2)}</p>
      <p>Portfolio Value: ${details.portfolio_value.toFixed(2)}</p>
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
