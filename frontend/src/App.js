import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import UserSelector from "./components/UserSelector/UserSelector";
import TransactionsView from "./components/TransactionsView/TransactionsView";
import StockList from "./components/StockList/StockList";
import StockChart from "./components/StockChart/StockChart";
import "./App.css";

function App() {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [selectedTransactions, setSelectedTransactions] = useState(null);


  const colorPalette = [
    "#8b5cf6",
    "#ef4444",
    "#f59e0b",
    "#34d399",
    "#ec4899",
    "#10b981",
    "#4a90e2",
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

          {/* 🔹 Menu zakładek */}
          <nav style={{ marginTop: "10px" }}>
            <Link to="/" style={{ marginRight: "15px" }}>📈 Portfolio</Link>
            <Link to="/transactions" style={{ marginRight: "15px" }}>💹 Transactions</Link>
            <Link to="/stocks">📊 Stocks</Link>
          </nav>
        </header>

        <Routes>
          {/* 🔹 Strona główna (portfolio) */}
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

          {/* 🔹 Transakcje */}
          <Route
            path="/transactions"
            element={
              <TransactionsView
                selectedUserIds={selectedUserIds}
                colorPalette={colorPalette}
              />
            }
          />

          {/* 🔹 Lista spółek */}
          <Route path="/stocks" element={<StockList />} />

          {/* 🔹 Wykres konkretnej spółki */}
          <Route
            path="/stocks/:ticker"
            element={
              <StockChart
                onTransactionsSelect={setSelectedTransactions}
                selectedUserIds={selectedUserIds}
                colorPalette={colorPalette}
              />
            }
          />

        </Routes>
      </div>

        {selectedTransactions && selectedTransactions.length > 0 && (
          <div className="transaction-details-panel">
            <h3>📋 Selected Transactions</h3>
              {selectedTransactions.map((t, i) => (
                <div key={i} className="transaction-item" style={{borderLeft:`4px solid ${t.color}`}}>
                  <strong>User {t.userId}</strong> <br />
                  <span>{new Date(t.datetime).toLocaleString()}</span>
                  <div>Quantity: {t.quantity}</div>
                  <div>Ratio: {(t.ratio * 100).toFixed(2)}%</div>
                </div>
            ))}
        </div>
      )}

    </Router>
  );
}

export default App;
