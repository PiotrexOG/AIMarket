import React, { useState } from "react";
import PortfolioChart from "./components/PortfolioChart";
import PortfolioDetails from "./components/PortfolioDetails";
import "./App.css";

function App() {
  const [selectedPoint, setSelectedPoint] = useState(null);

  return (
    <div className="App">
      <h1>Portfolio History Viewer</h1>

      <PortfolioChart onPointClick={setSelectedPoint} />

      {selectedPoint && (
        <PortfolioDetails
          userId={2}
          timestamp={selectedPoint.date}
          onClose={() => setSelectedPoint(null)}
        />
      )}
    </div>
  );
}

export default App;
