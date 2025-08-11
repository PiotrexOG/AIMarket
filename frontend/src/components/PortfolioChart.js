import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function PortfolioChart({ onPointClick }) {
  const [data, setData] = useState([]);
  const userId = 2; // przykładowy user

  useEffect(() => {
    fetch(`http://localhost:8000/users/${userId}/portfolio-history`)
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error(err));
  }, []);

  return (
    <LineChart
      width={900}
      height={400}
      data={data}
      margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      onClick={(e) => {
        if (e && e.activePayload) {
          onPointClick(e.activePayload[0].payload);
        }
      }}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="timestamp" />
      <YAxis />
      <Tooltip />
      <Line
        type="monotone"
        dataKey="portfolio_value"
        stroke="#8884d8"
        activeDot={{
          r: 8,
          onClick: (event, payload) => {
            console.log("DEBUG — payload on click:", payload);
            onPointClick(payload.payload); // tu payload.payload to obiekt punktu z timestamp
          }
        }}
      />


    </LineChart>
  );
}

export default PortfolioChart;
