import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import UserSelector from "./components/UserSelector/UserSelector";
import TransactionsView from "./components/TransactionsView/TransactionsView";
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

  const handleSelectionChange = (updated) => {
    const sorted = [...updated].sort((a, b) => a - b);
    setSelectedUserIds(sorted);
  };

  return (
    <Router>
      <div className="page-container">
        <header className="app-header">
          <div className="header-top">
            <UserSelector onSelectionChange={handleSelectionChange} />
          </div>

          <h3>Portfolio History Viewer</h3>

          {/* 🔹 Proste menu zakładek */}
          <nav style={{ marginTop: "10px" }}>
            <Link to="/" style={{ marginRight: "15px" }}>📈 Portfolio</Link>
            <Link to="/transactions">💹 Transactions</Link>
          </nav>
        </header>

        {/* 🔹 Routing */}
        <Routes>
          {/* Strona główna */}
          <Route
            path="/"
            element={
              <>
                <PortfolioChart
                  userIds={selectedUserIds}
                  onPointClick={setSelectedPoint}
                  colorPalette={colorPalette}
                />

                {selectedPoint && (
                  <div className="details-wrapper">
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
              </>
            }
          />

          {/* 🔹 Strona transakcji – dostaje te same userIds */}
          <Route
            path="/transactions"
            element={
              <TransactionsView
                selectedUserIds={selectedUserIds}
                colorPalette={colorPalette}
              />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
