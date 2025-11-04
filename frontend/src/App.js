// src/App.js
import React, { useState } from "react";
import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import UserSelector from "./components/UserSelector/UserSelector";
import "./App.css";

function App() {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  return (
    <div className="page-container">
      <header className="app-header">
        <div className="header-top">
          <UserSelector onSelectionChange={setSelectedUserIds} />
        </div>

        <h1>Portfolio History Viewer</h1>
        <h2>
          {selectedUserIds.length > 0
            ? `Selected users: ${selectedUserIds.join(", ")}`
            : "No users selected"}
        </h2>
      </header>

      {/* 🔹 Przekazujemy tablicę userId zamiast jednego */}
      <PortfolioChart userIds={selectedUserIds} onPointClick={setSelectedPoint} />

      {selectedPoint && (
        <div className="details-wrapper">
          <PortfolioDetails
            // np. pierwszy zaznaczony user – do szczegółów
            userId={selectedUserIds[0]}
            timestamp={selectedPoint.date}
            onClose={() => setSelectedPoint(null)}
          />
        </div>
      )}
    </div>
  );
}

export default App;
