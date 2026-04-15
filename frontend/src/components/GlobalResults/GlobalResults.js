import React, { useState, useEffect } from "react";
import { useChartRange } from "../common/useChartRange";
import ChartRangeButtons from "../common/ChartRangeButtons";
import { fetchPerformanceSummary, fetchArchetypes } from "./utils/fetchUtils";
import "./GlobalResults.css";

function GlobalResults({ totalStart, totalEnd }) {
  const [summaryData, setSummaryData] = useState([]);
  const [archetypes, setArchetypes] = useState([]);
  const [loading, setLoading] = useState(true);

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

  const fmtRange = (arr) =>
    `${(arr[0] * 100).toFixed(0)}-${(arr[1] * 100).toFixed(0)}%`;

  const handleSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === "asc" ? "desc" : "asc"
        };
      }
      return { key, direction: "desc" };
    });
  };

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

  const calculateStats = (data, path) => {
    if (!data.length) return { avg: 0, std: 0 };
    const values = data.map(item => getValue(item, path) || 0);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const squareDiffs = values.map(v => Math.pow(v - avg, 2));
    const std = Math.sqrt(squareDiffs.reduce((a, b) => a + b, 0) / values.length);
    return { avg, std };
  };

  const renderStatsCell = (data, path, isPercent = true, decimals = 1) => {
    const { avg, std } = calculateStats(data, path);
    const multiplier = isPercent ? 100 : 1;
    const unit = isPercent ? "%" : "";
    return (
      <td>
        <strong>{(avg * multiplier).toFixed(decimals)}{unit}</strong>
        <span className="std-dev">±{(std * multiplier).toFixed(decimals)}</span>
      </td>
    );
  };

  const sortData = (data) => {
    const sorted = [...data];

    sorted.sort((a, b) => {
      const valA = getValue(a, keyMap[sortConfig.key]);
      const valB = getValue(b, keyMap[sortConfig.key]);

      if (valA < valB) return sortConfig.direction === "asc" ? -1 : 1;
      if (valA > valB) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });

    return sorted;
  };

  if (loading) return <div className="loading">Ładowanie danych...</div>;

  return (
    <div className="container">
      <header className="header">
        <h1>Panel Analityczny Archetypów</h1>
        <ChartRangeButtons
          totalStart={totalStart}
          totalEnd={totalEnd}
          range={range}
          onChange={handleRangeChange}
          onCustomRangeChange={handleCustomRangeChange}
        />
      </header>

      {archetypes.map((arch) => {
        const relatedPortfolios = summaryData.filter(
          (p) => p.archetype_key === arch.key
        );

        return (
          <section key={arch.key} className="section">
            <div className="arch-header">
              <h2>{arch.name}</h2>
              <p>{arch.summary}</p>
            </div>

            <div className="table-wrapper">
              <table className="results-table">
                <colgroup>
                  <col className="col-name" />
                  <col span="3" className="col-equal" />
                  <col span="4" className="col-equal" />
                  <col span="6" className="col-equal" />
                  <col className="col-equal" />
                </colgroup>

                <thead>
                  <tr className="header-group">
                    <th className="sticky-col">Info</th>
                    <th colSpan="3">Time Weights (%)</th>
                    <th colSpan="4">Config</th>
                    <th colSpan="6">Metric Weights (%)</th>
                    <th>Result</th>
                  </tr>

                  <tr className="th-row">
                    <th className="sticky-col">ID / Name</th>

                    <th onClick={() => handleSort("short")} className="sortable">
                      Short {sortConfig.key === "short" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("mid")} className="sortable">
                      Mid {sortConfig.key === "mid" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("long")} className="sortable">
                      Long {sortConfig.key === "long" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("risk")} className="sortable">
                      Risk {sortConfig.key === "risk" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("rebalance")} className="sortable">
                      Rebal {sortConfig.key === "rebalance" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("min_score")} className="sortable">
                      Min {sortConfig.key === "min_score" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("temp")} className="sortable">
                      Temp {sortConfig.key === "temp" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("asym")} className="sortable">
                      Asym {sortConfig.key === "asym" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("conv")} className="sortable">
                      Conv {sortConfig.key === "conv" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("struct_risk")} className="sortable">
                      Risk {sortConfig.key === "struct_risk" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("val")} className="sortable">
                      Val {sortConfig.key === "val" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("fund")} className="sortable">
                      Fund {sortConfig.key === "fund" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("tech")} className="sortable">
                      Tech {sortConfig.key === "tech" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("change_ratio")} className="sortable">
                      % {sortConfig.key === "change_ratio" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>
                  </tr>

                  <tr className="range-row">
                    <td className="sticky-col">TARGET</td>
                    <td>{fmtRange(arch.time_weights.short)}</td>
                    <td>{fmtRange(arch.time_weights.medium)}</td>
                    <td>{fmtRange(arch.time_weights.long)}</td>
                    <td>{fmtRange(arch.risk_tolerance)}</td>
                    <td>{fmtRange(arch.rebalance_range)}</td>
                    <td>{arch.min_score[0]}-{arch.min_score[1]}</td>
                    <td>{arch.temp[0]}-{arch.temp[1]}</td>
                    <td>{fmtRange(arch.metric_weights.asym)}</td>
                    <td>{fmtRange(arch.metric_weights.conv)}</td>
                    <td>{fmtRange(arch.metric_weights.risk)}</td>
                    <td>{fmtRange(arch.metric_weights.val)}</td>
                    <td>{fmtRange(arch.metric_weights.fund)}</td>
                    <td>{fmtRange(arch.metric_weights.tech)}</td>
                    <td></td>
                  </tr>
                </thead>

                <tbody>
                  {sortData(relatedPortfolios).map((p) => (
                    <tr key={p.id}>
                      <td className="sticky-col name-cell">
                        <strong>{p.name.replace("Portfolio ", "")}</strong>{" "}
                        <span className="id">({p.id})</span>
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

                                        {/* DODAJ TO TUTAJ - Kolejny wiersz bezpośrednio w tbody */}
                    <tr className="summary-row-simple">
                        <td className="sticky-col summary-label">ŚREDNIA (σ)</td>
                        {renderStatsCell(relatedPortfolios, keyMap.short)}
                        {renderStatsCell(relatedPortfolios, keyMap.mid)}
                        {renderStatsCell(relatedPortfolios, keyMap.long)}
                        {renderStatsCell(relatedPortfolios, keyMap.risk)}
                        {renderStatsCell(relatedPortfolios, keyMap.rebalance)}
                        {renderStatsCell(relatedPortfolios, keyMap.min_score, false, 2)}
                        {renderStatsCell(relatedPortfolios, keyMap.temp, false, 2)}
                        {renderStatsCell(relatedPortfolios, keyMap.asym)}
                        {renderStatsCell(relatedPortfolios, keyMap.conv)}
                        {renderStatsCell(relatedPortfolios, keyMap.struct_risk)}
                        {renderStatsCell(relatedPortfolios, keyMap.val)}
                        {renderStatsCell(relatedPortfolios, keyMap.fund)}
                        {renderStatsCell(relatedPortfolios, keyMap.tech)}
                        {renderStatsCell(relatedPortfolios, "change_ratio")}
                    </tr>
                </tbody>

            
              </table>
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default GlobalResults;