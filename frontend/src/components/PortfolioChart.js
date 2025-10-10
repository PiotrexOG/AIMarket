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
  const [range, setRange] = useState("1M"); // domyślnie 1 miesiąc
  const userId = 2; // przykładowy user

  // 🔹 Ustalony pełny zakres symulacji
  const totalStart = new Date("2024-10-02T13:30:00Z");
  const totalEnd = new Date("2024-12-04T20:30:00Z"); // lub new Date() jeśli ma być dynamicznie

  // 🔹 funkcja pomocnicza – wylicza początek okresu względem totalEnd
  const clampDate = (date, min, max) =>
    new Date(Math.min(Math.max(date.getTime(), min.getTime()), max.getTime()));

  const getRangeDates = (range) => {
    const end = totalEnd; // zawsze ostatni punkt danych
    let start = new Date(end);

    switch (range) {
      case "1D":
        start.setDate(end.getDate() - 1);
        break;
      case "1W":
        start.setDate(end.getDate() - 7);
        break;
      case "1M":
        start.setMonth(end.getMonth() - 1);
        break;
      case "3M":
        start.setMonth(end.getMonth() - 3);
        break;
      case "6M":
        start.setMonth(end.getMonth() - 6);
        break;
      case "YTD":
        start.setFullYear(end.getFullYear(), 0, 1);
        break;
      case "1Y":
        start.setFullYear(end.getFullYear() - 1);
        break;
    }

    // przycięcie tylko startu — end zostaje
    start = clampDate(start, totalStart, totalEnd);

    return {
      start: start.toISOString(),
      end: end.toISOString(),
    };
  };


  // 🔹 pobieranie danych z backendu
  const fetchValuation = () => {
    const { start, end } = getRangeDates(range);
    const url = `http://localhost:8000/portfolios/${userId}/valuation?start=${encodeURIComponent(
      start
    )}&end=${encodeURIComponent(end)}&interval=1d&detailed=false`;

    fetch(url)
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Fetch valuation error:", err));
  };

  // 🔹 efekt — pobiera dane przy starcie i zmianie zakresu
  useEffect(() => {
    fetchValuation();
  }, [range, userId]);

  // 🔹 kliknięcie na wykres (bez zmian)
  const handleChartClick = (e) => {
    if (!e) return;
    if (e.activePayload && e.activePayload.length > 0) {
      onPointClick(e.activePayload[0].payload);
      return;
    }
    if (e.activeLabel) {
      const found = data.find((d) => d.date === e.activeLabel);
      if (found) onPointClick(found);
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
          <XAxis
            dataKey="date"
            tickFormatter={(tick) => tick.split("T")[0]} // pokazuje tylko datę
          />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="portfolio_value"
            stroke="#4a90e2"
            strokeWidth={2}
            dot={{ r: 4, cursor: "pointer" }}
            activeDot={{
              r: 7,
              onClick: (event, payload) => {
                if (payload && payload.payload) {
                  onPointClick(payload.payload);
                }
              },
            }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* 🔹 Przyciski zakresów czasu */}
      <div style={{ marginTop: "12px", display: "flex", justifyContent: "center", gap: "8px" }}>
        {["1D", "1W", "1M", "3M", "6M", "YTD", "1Y"].map((r) => (
          <button
            key={r}
            onClick={() => setRange(r)}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "1px solid #ccc",
              backgroundColor: range === r ? "#4a90e2" : "white",
              color: range === r ? "white" : "black",
              cursor: "pointer",
              fontWeight: range === r ? "bold" : "normal",
            }}
          >
            {r}
          </button>
        ))}
      </div>
    </div>
  );
}

export default PortfolioChart;
