import React, { useState, useEffect } from "react";
import { useChartRange } from "../common/useChartRange";
import ChartRangeButtons from "../common/ChartRangeButtons";
import CorrelationCharts from "./CorrelationCharts";
import MetricCompositionChart from "./MetricCompositionChart";
import ArchetypePerformanceChart from "./ArchetypePerformanceChart";
import ArchetypeAverageChart from "./ArchetypeAverageChart";
import ArchetypeCorrelationHeatmap from "./ArchetypeCorrelationHeatmap";
import ArchetypeRadarAnalysis from "./ArchetypeRadarAnalysis";
import SuccessDistributionChart from "./SuccessDistributionChart";
import {PortfolioParallelPlot, ArchetypeParallelPlot} from "./ParallelPlot";
import { fetchPerformanceSummary, fetchArchetypes } from "./utils/fetchUtils";
import { generateDistinctColors } from "../common/utils"; 
import "./GlobalResults.css";

function AllResults({ totalStart, totalEnd }) {
  const [summaryData, setSummaryData] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [archColorMap, setArchColorMap] = useState({});

  const [sortConfig, setSortConfig] = useState({
    key: "change_ratio",
    direction: "desc"
  });

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

        // --- Logika obliczania vs Benchmark ---
        const benchmarkObj = perf.find(p => p.archetype_key === "benchmark");
        const benchmarkChange = benchmarkObj?.change_ratio ?? 0;

        const enhancedPerf = perf.map(p => {
          const archetype = arch.find(a => a.key === p.archetype_key);
          const bench = archetype?.benchmark_result ?? benchmarkChange;
          return {
            ...p,
            benchmark_diff: p.change_ratio - bench
          };
        });

        setSummaryData(enhancedPerf);
        setArchetypes(arch);

        // Kolory dla archetypów
        const uniqueKeys = [...new Set(perf.map(p => p.archetype_key))].sort();
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

  const keyMap = {
    short: "short_term_weight",
    mid: "medium_term_weight",
    long: "long_term_weight",
    risk: "risk_tolerance",
    rebal: "rebalance_threshold",
    min: "min_score_threshold",
    temp: "softmax_temp",
    asym: "metric_weights.relative_asymmetry_profile",
    conv: "metric_weights.relative_conviction",
    risk: "metric_weights.relative_structural_risk",
    val: "metric_weights.relative_valuation_sustainability",
    fund: "metric_weights.relative_fundamental_support",
    tech: "metric_weights.relative_technical_strength",
    change_ratio: "change_ratio",
    benchmark_diff: "benchmark_diff"
  };

  const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

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

  const getArchName = (key) => archetypes.find(a => a.key === key)?.name || key;

  if (loading) return <div className="loading">Ładowanie zestawienia zbiorczego...</div>;

  const sortedData = sortData(summaryData);

  return (
    <div className="container">
      <header className="header">
        <h1>Zbiorcze Zestawienie Portfeli</h1>
        <ChartRangeButtons
          totalStart={totalStart} totalEnd={totalEnd}
          range={range} onChange={handleRangeChange}
          onCustomRangeChange={handleCustomRangeChange}
        />
      <div className="date-wrapper">
        <span className="date-range-text">
          {new Date(start).toLocaleDateString('pl-PL')} - {new Date(end).toLocaleDateString('pl-PL')}
        </span>
      </div>
      </header>



      <div className="section">
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
                  <th key={key} onClick={() => handleSort(key)} className="sortable">
                    {key.charAt(0).toUpperCase() + key.slice(1)} 
                    {sortConfig.key === key && (sortConfig.direction === "asc" ? "▲" : "▼")}
                  </th>
                ))}
                <th onClick={() => handleSort("change_ratio")} className="sortable">% {sortConfig.key === "change_ratio" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
                <th onClick={() => handleSort("benchmark_diff")} className="sortable">vs Bench {sortConfig.key === "benchmark_diff" && (sortConfig.direction === "asc" ? "▲" : "▼")}</th>
              </tr>
            </thead>

            <tbody>
              {sortedData.map((p) => {
                const diffValue = (p.benchmark_diff || 0) * 100;
                return (
                    <tr 
                      key={p.id} 
                      style={{
                        backgroundColor: p.archetype_key === "benchmark" 
                          ? "#fff0f0"  // jasnoczerwone tło
                          : archColorMap[p.archetype_key]?.replace("hsl", "hsla").replace(")", ", 0.15)") || "transparent",
                        border: p.archetype_key === "benchmark" ? "2px solid #ff0000" : "none",
                      }}
                    >
                    <td className="sticky-col name-cell" style={{ borderLeft: `4px solid ${archColorMap[p.archetype_key] || "#ccc"}` }}>
                      <div style={{ fontWeight: 'bold' }}>{p.name.replace("Portfolio ", "")}</div>
                      <div className="id" style={{ fontSize: '10px', color: '#666' }}>{getArchName(p.archetype_key)}</div>
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
                    <td className={`performance ${p.change_ratio >= 0 ? "positive" : "negative"}`}>{(p.change_ratio * 100).toFixed(2)}%</td>
                    <td className={`benchmark ${diffValue >= 0 ? "positive" : "negative"}`}>
                      {diffValue > 0 ? "+" : ""}{diffValue.toFixed(2)}pp
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section">
        <h2>Ranking Archetypów</h2>
        <ArchetypePerformanceChart data={summaryData} archetypes={archetypes} archColorMap={archColorMap} />
      </div>

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <MetricCompositionChart data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <ArchetypeAverageChart data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <PortfolioParallelPlot data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <ArchetypeParallelPlot data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <ArchetypeCorrelationHeatmap data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <SuccessDistributionChart data={summaryData} archColorMap={archColorMap} />
        </div>
      )}

      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <ArchetypeRadarAnalysis data={summaryData} archColorMap={archColorMap} />
        </div>
      )}


      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <CorrelationCharts data={summaryData} archColorMap={archColorMap} />
        </div>
      )}
    </div>
  );
}

export default AllResults;