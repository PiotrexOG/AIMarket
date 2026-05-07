import React from "react";

const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

const ResultsTable = ({ 
  data, 
  sortConfig, 
  onSort, 
  archColorMap, 
  getArchName, 
  keyMap 
}) => {
  return (
    <div className="table-wrapper">
      <table className="results-table">
        <thead>
          <tr className="header-group">
            <th className="sticky-col">Portfolio Info</th>
            <th colSpan="3">Time Weights (%)</th>
            <th colSpan="4">Config</th>
            <th colSpan="6">Metric Weights (%)</th>
            <th colSpan="2">Results</th>
          </tr>
          <tr className="th-row">
            <th className="sticky-col">ID / Archetype</th>
            {["short", "mid", "long", "risk", "rebal", "min", "temp", "asym", "conv", "risk", "val", "fund", "tech"].map(key => (
              <th key={key} onClick={() => onSort(key)} className="sortable">
                {key.charAt(0).toUpperCase() + key.slice(1)} 
                {sortConfig.key === key && (sortConfig.direction === "asc" ? " ▲" : " ▼")}
              </th>
            ))}
            <th onClick={() => onSort("change_ratio")} className="sortable">
              % {sortConfig.key === "change_ratio" && (sortConfig.direction === "asc" ? " ▲" : " ▼")}
            </th>
            <th onClick={() => onSort("benchmark_diff")} className="sortable">
              vs Bench {sortConfig.key === "benchmark_diff" && (sortConfig.direction === "asc" ? " ▲" : " ▼")}
            </th>
          </tr>
        </thead>

        <tbody>
          {data.map((p) => {
            const diffValue = (p.benchmark_diff || 0) * 100;
            const isBenchmark = p.archetype_key === "benchmark";
            
            // Logika koloru tła
            const rowStyle = {
              backgroundColor: isBenchmark 
                ? "#fff0f0" 
                : archColorMap[p.archetype_key]?.replace("hsl", "hsla").replace(")", ", 0.15)") || "transparent",
              border: isBenchmark ? "2px solid #ff0000" : "none",
            };

            return (
              <tr key={p.id} style={rowStyle}>
                <td 
                  className="sticky-col name-cell" 
                  style={{ borderLeft: `4px solid ${archColorMap[p.archetype_key] || "#ccc"}` }}
                >
                  <div style={{ fontWeight: 'bold' }}>{p.name.replace("Portfolio ", "")}</div>
                  <div className="id" style={{ fontSize: '10px', color: '#666' }}>
                    {getArchName(p.archetype_key)}
                  </div>
                </td>
                <td>{(p.short_term_weight * 100).toFixed(1)}%</td>
                <td>{(p.medium_term_weight * 100).toFixed(1)}%</td>
                <td>{(p.long_term_weight * 100).toFixed(1)}%</td>
                <td>{(p.risk_tolerance * 100).toFixed(1)}%</td>
                <td>{(p.rebalance_threshold * 100).toFixed(1)}%</td>
                <td>{p.min_score_threshold}</td>
                <td>{p.softmax_temp}</td>
                <td>{(p.metric_weights.relative_asymmetry_profile * 100).toFixed(1)}%</td>
                <td>{(p.metric_weights.relative_conviction * 100).toFixed(1)}%</td>
                <td>{(p.metric_weights.relative_structural_risk * 100).toFixed(1)}%</td>
                <td>{(p.metric_weights.relative_valuation_sustainability * 100).toFixed(1)}%</td>
                <td>{(p.metric_weights.relative_fundamental_support * 100).toFixed(1)}%</td>
                <td>{(p.metric_weights.relative_technical_strength * 100).toFixed(1)}%</td>
                <td className={`performance ${p.change_ratio >= 0 ? "positive" : "negative"}`}>
                  {(p.change_ratio * 100).toFixed(2)}%
                </td>
                <td className={`benchmark ${diffValue >= 0 ? "positive" : "negative"}`}>
                  {diffValue > 0 ? "+" : ""}{diffValue.toFixed(2)}pp
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;