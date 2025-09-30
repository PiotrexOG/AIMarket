// src/components/PortfolioChart.js
import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
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

  // funkcja pobierająca dane
  const fetchHistory = () => {
    fetch(`http://localhost:8000/portfolios/${userId}/history/summary`)
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Fetch history error:", err));
  };

  // pobierz dane na start i odświeżaj co 5 sekund
  useEffect(() => {
    fetchHistory(); // pierwsze pobranie

    const interval = setInterval(() => {
      fetchHistory();
    }, 5000); // co 5s (5000ms)

    return () => clearInterval(interval); // cleanup gdy komponent się odmontuje
  }, [userId]);

  // fallback handler gdy ktoś kliknie w obszar wykresu (niekoniecznie dokładnie w kropkę)
  const handleChartClick = (e) => {
    if (!e) return;
    if (e.activePayload && e.activePayload.length > 0) {
      console.log("Chart click payload:", e.activePayload[0].payload);
      onPointClick(e.activePayload[0].payload);
      return;
    }
    if (e.activeLabel) {
      // próbujemy znaleźć punkt po etykiecie (date)
      const found = data.find((d) => d.date === e.activeLabel);
      if (found) {
        console.log("Chart click found by label:", found);
        onPointClick(found);
      }
    }
  };

  return (
    <div className="chart-container">
      <ResponsiveContainer width="95%" height={400}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          onClick={handleChartClick}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="portfolio_value"
            stroke="#4a90e2"
            strokeWidth={2}
            // zwykłe kropki (małe) z kursorem wskazującym że są klikalne
            dot={{ r: 4, cursor: "pointer" }}
            // aktywna kropka (po najechaniu/hover) — tutaj najpewniej złapiemy kliknięcie
            activeDot={{
              r: 7,
              onClick: (event, payload) => {
                console.log("activeDot click payload:", payload);
                if (payload && payload.payload) {
                  onPointClick(payload.payload);
                }
              },
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PortfolioChart;
