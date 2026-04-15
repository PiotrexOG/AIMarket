import React, { useState, useEffect } from "react";
import { useChartRange } from "../common/useChartRange";
import ChartRangeButtons from "../common/ChartRangeButtons";
import CorrelationCharts from "./CorrelationCharts";
import ArchetypePerformanceChart from "./ArchetypePerformanceChart";
import { fetchPerformanceSummary, fetchArchetypes } from "./utils/fetchUtils";
import { generateDistinctColors } from "../common/utils"; // dopasuj ścieżkę
import "./GlobalResults.css"; // Używamy tego samego CSS

function AllResults({ totalStart, totalEnd }) {
  const [summaryData, setSummaryData] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [loading, setLoading] = useState(true);

  const [sortConfig, setSortConfig] = useState({
    key: "change_ratio",
    direction: "desc"
  });

  const [archColorMap, setArchColorMap] = useState({});

  const { range, handleRangeChange, handleCustomRangeChange, getEffectiveRange } =
    useChartRange(totalStart, totalEnd);
  const { start, end } = getEffectiveRange();

  useEffect(() => {
    const loadAllData = async () => {
      setLoading(true);
      try {
        const [perf, arch] = await Promise.all([
          fetchPerformanceSummary(start, end),
          fetchArchetypes()
        ]);
        setSummaryData(perf);
        setArchetypes(arch);
      } catch (err) {
        console.error("Błąd ładowania:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAllData();
  }, [start, end]);

  useEffect(() => {
    const loadAllData = async () => {
      setLoading(true);
      try {
        const [perf, arch] = await Promise.all([
          fetchPerformanceSummary(start, end),
          fetchArchetypes()
        ]);
  
        setSummaryData(perf);
        setArchetypes(arch);
  
        // 🔥 NOWE: kolory dla archetypów
        const uniqueKeys = [...new Set(perf.map(p => p.archetype_key))];
        const colors = generateDistinctColors(uniqueKeys.length);
  
        const map = {};
        uniqueKeys.forEach((key, index) => {
          map[key] = colors[index];
        });
  
        setArchColorMap(map);
  
      } catch (err) {
        console.error("Błąd ładowania:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAllData();
  }, [start, end]);

  // Mapowanie kluczy do sortowania (takie samo jak w oryginale)
  const keyMap = {
    short: "short_term_weight",
    mid: "medium_term_weight",
    long: "long_term_weight",
    risk: "risk_tolerance",
    rebalance: "rebalance_threshold",
    min_score: "min_score_threshold",
    temp: "softmax_temp",
    asym: "metric_weights.relative_asymmetry_profile",
    conv: "metric_weights.relative_conviction",
    struct_risk: "metric_weights.relative_structural_risk",
    val: "metric_weights.relative_valuation_sustainability",
    fund: "metric_weights.relative_fundamental_support",
    tech: "metric_weights.relative_technical_strength",
    change_ratio: "change_ratio"
  };

  const getValue = (obj, path) =>
    path.split(".").reduce((o, key) => o?.[key], obj);

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc"
    }));
  };

  const sortData = (data) => {
    return [...data].sort((a, b) => {
      const valA = getValue(a, keyMap[sortConfig.key] || sortConfig.key);
      const valB = getValue(b, keyMap[sortConfig.key] || sortConfig.key);
      if (valA < valB) return sortConfig.direction === "asc" ? -1 : 1;
      if (valA > valB) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });
  };

  // Helper do wyciągania nazwy archetypu dla danego portfela
  const getArchName = (key) => archetypes.find(a => a.key === key)?.name || key;

  if (loading) return <div className="loading">Ładowanie zestawienia zbiorczego...</div>;

  return (
    <div className="container">
      <header className="header">
        <h1>Zbiorcze Zestawienie Portfeli</h1>
        <ChartRangeButtons
          totalStart={totalStart}
          totalEnd={totalEnd}
          range={range}
          onChange={handleRangeChange}
          onCustomRangeChange={handleCustomRangeChange}
        />
      </header>

      <div className="section">
        <div className="table-wrapper">
          <table className="results-table">
            <colgroup>
              <col style={{ width: "200px" }} /> {/* Szersza kolumna na ID/Arch */}
              <col span="3" className="col-equal" />
              <col span="4" className="col-equal" />
              <col span="6" className="col-equal" />
              <col className="col-equal" />
            </colgroup>

            <thead>
              <tr className="header-group">
                <th className="sticky-col">Portfolio Info</th>
                <th colSpan="3">Time Weights (%)</th>
                <th colSpan="4">Config</th>
                <th colSpan="6">Metric Weights (%)</th>
                <th>Result</th>
              </tr>
              <tr className="th-row">
                <th className="sticky-col">ID / Archetype</th>
                <th onClick={() => handleSort("short")} className="sortable">Short {sortConfig.key === "short" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("mid")} className="sortable">Mid {sortConfig.key === "mid" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("long")} className="sortable">Long {sortConfig.key === "long" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("risk")} className="sortable">Risk {sortConfig.key === "risk" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("rebalance")} className="sortable">Rebal {sortConfig.key === "rebalance" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("min_score")} className="sortable">Min {sortConfig.key === "min_score" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("temp")} className="sortable">Temp {sortConfig.key === "temp" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("asym")} className="sortable">Asym {sortConfig.key === "asym" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("conv")} className="sortable">Conv {sortConfig.key === "conv" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("struct_risk")} className="sortable">Risk {sortConfig.key === "struct_risk" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("val")} className="sortable">Val {sortConfig.key === "val" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("fund")} className="sortable">Fund {sortConfig.key === "fund" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("tech")} className="sortable">Tech {sortConfig.key === "tech" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("change_ratio")} className="sortable">% {sortConfig.key === "change_ratio" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
              </tr>
            </thead>

            <tbody>
              {sortData(summaryData).map((p) => (
                  <tr
                  key={p.id}
                  style={{
                    backgroundColor: archColorMap[p.archetype_key]
                      ? archColorMap[p.archetype_key].replace("hsl", "hsla").replace(")", ", 0.2)")
                      : "transparent"
                  }}
                >
                  <td
                    className="sticky-col name-cell"
                    style={{ borderLeft: `4px solid ${archColorMap[p.archetype_key] || "#ccc"}` }}
                  >
                    <div style={{ fontWeight: 'bold' }}>{p.name.replace("Portfolio ", "")}</div>
                    <div className="id" style={{ fontSize: '9px', color: '#666' }}>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    <div className="section">
      <h2>Ranking Archetypów</h2>
      <ArchetypePerformanceChart 
        data={summaryData} 
        archetypes={archetypes} 
        archColorMap={archColorMap} 
      />
    </div>


    {/* NOWA SEKCJA Z WYKRESAMI */}
    {!loading && summaryData.length > 0 && (
      <div className="section">
        <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
        <CorrelationCharts 
          data={summaryData} 
          archColorMap={archColorMap} 
        />
      </div>
    )}
  </div>
);

}

export default AllResults;