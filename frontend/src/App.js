// src/App.js
import React, { useState } from "react";
import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import UserSelector from "./components/UserSelector/UserSelector";
import "./App.css";

function App() {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  const colorPalette = [
    "#4a90e2",
    "#34d399",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#10b981",
  ];

    // 🔹 Sortujemy po ID, żeby zawsze była spójna kolejność
  const handleSelectionChange = (updated) => {
    const sorted = [...updated].sort((a, b) => a - b);
    setSelectedUserIds(sorted);
  };

  return (
    <div className="page-container">
      <header className="app-header">
        <div className="header-top">
          <UserSelector onSelectionChange={handleSelectionChange} />
        </div>

        <h3>Portfolio History Viewer</h3>
      </header>

      {/* 🔹 Wykres */}
      <PortfolioChart
        userIds={selectedUserIds}
        onPointClick={setSelectedPoint}
        colorPalette={colorPalette}
      />


      {/* 🔹 Sekcja z datą i listą detali */}
      {selectedPoint && (
        <div className="details-wrapper">
          {/* Data / godzina / strefa czasowa */}
            <div className="timestamp-header">
            <div className="timestamp-date">
              {new Date(selectedPoint.date).toLocaleDateString("en-CA")}
            </div>
            <div className="timestamp-time">
              {new Date(selectedPoint.date).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}{" "}
              ({Intl.DateTimeFormat().resolvedOptions().timeZone})
            </div>
          </div>

          {/* Szczegóły userów */}
          <div className="details-grid">
            {selectedUserIds.map((id, idx) => (
              <PortfolioDetails
                key={id}
                userId={id}
                timestamp={selectedPoint.date}
                color={colorPalette[idx % colorPalette.length]}
                onClose={() => setSelectedPoint(null)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
