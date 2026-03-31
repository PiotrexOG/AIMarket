import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import UserSelector from "./components/UserSelector/UserSelector";
import TransactionsView from "./components/TransactionsView/TransactionsView";
import StockList from "./components/StockList/StockList";
import StockChart from "./components/StockChart/StockChart";
import StockTransactionPanel from "./components/StockTransactionPanel/StockTransactionPanel";

import { fetchSimulationConfig } from "./api/fetchSimulationConfig";

import "./App.css";

function App() {

  const [selectedPoint, setSelectedPoint] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState({});
  const [selectedTransactions, setSelectedTransactions] = useState(null);

  const [simulationConfig, setSimulationConfig] = useState(null);

  const colorPalette = [
    "#8b5cf6",
    "#ef4444",
    "#f59e0b",
    "#34d399",
    "#ec4899",
    "#10b981",
    "#4a90e2",
  ];

  // 🔹 pobranie konfiguracji symulacji z backendu
  useEffect(() => {
    const loadConfig = async () => {
      try {

        const config = await fetchSimulationConfig();

        setSimulationConfig({
          totalStart: new Date(config.start_date),
          totalEnd: new Date(config.end_date)
        });

      } catch (err) {
        console.error("Failed to fetch simulation config", err);
      }
    };

    loadConfig();
  }, []);


  const handleSelectionChange = (usersDict) => {

    const sortedDict = Object.keys(usersDict)
      .sort((a, b) => parseInt(a) - parseInt(b))
      .reduce((acc, key) => {
        acc[key] = usersDict[key];
        return acc;
      }, {});

    console.log("Selected users (sorted):", sortedDict);

    setSelectedUsers(sortedDict);
  };

  // 🔹 loading zanim backend odda daty
  if (!simulationConfig) {
    return <div style={{ padding: "30px" }}>Loading simulation configuration...</div>;
  }

  const { totalStart, totalEnd } = simulationConfig;

  return (
    <Router>

      <div className="page-container">

        <header className="app-header">

          <div className="header-top">
            <UserSelector onSelectionChange={handleSelectionChange} />
          </div>

          <h3>Portfolio History Viewer</h3>

          <nav style={{ marginTop: "10px" }}>
            <Link to="/" style={{ marginRight: "15px" }}>📈 Portfolio</Link>
            <Link to="/transactions" style={{ marginRight: "15px" }}>💹 Transactions</Link>
            <Link to="/stocks">📊 Stocks</Link>
          </nav>

        </header>


        <Routes>

          {/* 🔹 Portfolio */}
          <Route
            path="/"
            element={
              <>
                <PortfolioChart
                  totalStart={totalStart}
                  totalEnd={totalEnd}
                  selectedUsers={selectedUsers}
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

                      {Object.keys(selectedUsers).map((id, idx) => (
                        <PortfolioDetails
                          key={id}
                          userId={id}
                          userName={selectedUsers[id]}
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


          {/* 🔹 Transactions */}
          <Route
            path="/transactions"
            element={
              <TransactionsView
                selectedUsers={selectedUsers}
                colorPalette={colorPalette}
              />
            }
          />


          {/* 🔹 Lista spółek */}
          <Route path="/stocks" element={<StockList />} />


          {/* 🔹 Wykres spółki */}
          <Route
            path="/stocks/:ticker"
            element={
              <>
                <StockChart
                  totalStart={totalStart}
                  totalEnd={totalEnd}
                  onTransactionsSelect={setSelectedTransactions}
                  selectedUsers={selectedUsers}
                  colorPalette={colorPalette}
                />

                {selectedTransactions && (
                  <div className="details-wrapper">

                    <StockTransactionPanel
                      transactions={selectedTransactions}
                      onClose={() => setSelectedTransactions(null)}
                      selectedUsers={selectedUsers}
                      colorPalette={colorPalette}
                    />

                  </div>
                )}

              </>
            }
          />

        </Routes>

      </div>

    </Router>
  );
}

export default App;