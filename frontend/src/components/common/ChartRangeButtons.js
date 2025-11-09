// src/components/PortfolioChart/ChartRangeButtons.js
import React, { useState } from "react";
import "./ChartRangeButtons.css";

const ranges = ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y", "Custom"];
const intervals = ["30m", "1h", "4h", "1d", "1w"];

function ChartRangeButtons({ range, onChange, onCustomRangeChange }) {
  const [showCustom, setShowCustom] = useState(false);

  const [customStart, setCustomStart] = useState("2024-10-02");
  const [customEnd, setCustomEnd] = useState("2024-12-04");
  const [customInterval, setCustomInterval] = useState("1h");

  const handleRangeClick = (r) => {
    onChange(r);
    if (r === "Custom") {
      setShowCustom(true);
    } else {
      setShowCustom(false);
    }
  };

  const handleApplyCustom = () => {
    const startDate = new Date(`${customStart}T01:00:00`);
    const endDate = new Date(`${customEnd}T01:00:00`);
    onCustomRangeChange({
      start: startDate.toISOString(),
      end: endDate.toISOString(),
      interval: customInterval,
    });
  };

  return (
    <div className="range-controls flex flex-col gap-3">
      {/* przyciski zakresów */}
      <div className="flex flex-wrap gap-2">
        {ranges.map((r) => (
          <button
            key={r}
            className={`range-btn px-3 py-1 rounded-md border ${
              range === r ? "bg-blue-600 text-white" : "bg-gray-100"
            }`}
            onClick={() => handleRangeClick(r)}
          >
            {r}
          </button>
        ))}
      </div>

      {/* sekcja Customgo zakresu */}
      {showCustom && (
        <div className="custom-range bg-gray-50 p-4 rounded-lg shadow-sm flex flex-col gap-3 mt-2">
          <div className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="flex flex-col">
              <label className="text-sm text-gray-700">Data początkowa:</label>
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="border rounded-md px-2 py-1"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-700">Data końcowa:</label>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="border rounded-md px-2 py-1"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-700">Interwał:</label>
              <select
                value={customInterval}
                onChange={(e) => setCustomInterval(e.target.value)}
                className="border rounded-md px-2 py-1"
              >
                {intervals.map((i) => (
                  <option key={i} value={i}>
                    {i}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={handleApplyCustom}
            className="self-start bg-blue-600 text-white px-4 py-1 rounded-md mt-2"
          >
            Zastosuj
          </button>
        </div>
      )}
    </div>
  );
}

export default ChartRangeButtons;
