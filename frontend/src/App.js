import React, { useState } from "react";
import PortfolioChart from "./components/PortfolioChart/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails/PortfolioDetails";
import "./App.css";

function App() {
  const [selectedPoint, setSelectedPoint] = useState(null);
  const userId = 2;

  return (
    <div className="page-container">
      <header className="app-header">
        <h1>Portfolio History Viewer</h1>
        <h2>User {userId}</h2>
      </header>

      <PortfolioChart onPointClick={setSelectedPoint} />

      {selectedPoint && (
        <div className="details-wrapper">
          <PortfolioDetails
            userId={userId}
            timestamp={selectedPoint.date}
            onClose={() => setSelectedPoint(null)}
          />
        </div>
      )}
    </div>
  );
}

export default App;
