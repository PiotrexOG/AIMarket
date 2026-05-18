import { useEffect, useState } from "react";
import ChartRangeButtons from "./../../common/ChartRangeButtons";
import { useChartRange } from "./../../common/useChartRange";
import "./GlobalResults.css";
import { fetchArchetypes, fetchPerformanceSummary } from "./../utils/fetchUtils";

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
        
        // Obliczamy diff od razu przy ładowaniu, żeby łatwiej było sortować
        // znajdź benchmark
        const benchmarkObj = perf.find(p => p.archetype_key === "benchmark");
        const benchmarkChange = benchmarkObj?.change_ratio ?? 0;

        // potem licz diff
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
    min_exposure: "min_exposure",
    aggression_slope: "aggression_slope",
    exposure_baseline: "exposure_baseline",
    rebalance_threshold: "rebalance_threshold",
    temp: "softmax_temp",
    asym: "metric_weights.relative_asymmetry_profile",
    conv: "metric_weights.relative_conviction",
    struct_safety: "metric_weights.relative_structural_safety",
    val: "metric_weights.relative_valuation_sustainability",
    fund: "metric_weights.relative_fundamental_support",
    tech: "metric_weights.relative_technical_strength",
    change_ratio: "change_ratio",
    benchmark_diff: "benchmark_diff" // Dodane do sortowania
  };

  const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

  const calculateStats = (data, path, centyl) => {
    if (!data.length) return { avg: 0, std: 0 };
  
    // 🔥 sort po wyniku
    const sorted = [...data].sort((a, b) => b.change_ratio - a.change_ratio);
  
    // 🔥 wybór części danych (TOP X%)
    const size = Math.max(1, Math.floor(sorted.length * centyl));
    const selectedData = sorted.slice(0, size);
  
    // 🔥 wartości
    const values = selectedData.map(item => getValue(item, path) || 0);
  
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
  
    const variance =
      values.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / values.length;
  
    const std = Math.sqrt(variance);
  
    return { avg, std };
  };


  const renderStatsCell = (data, path, isPercent = true, decimals = 2, isPp = false, centyl = 1) => {
    const { avg, std } = calculateStats(data, path, centyl);
    const multiplier = isPercent || isPp ? 100 : 1;
    const unit = isPp ? "pp" : (isPercent ? "%" : "");
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

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc"
    }));
  };

  const fmtRange = (arr, isPercent = true) => {
    if (!arr || (arr[0] === 0 && arr[1] === 0)) return "NaN";
    return isPercent 
      ? `${(arr[0] * 100).toFixed(0)}-${(arr[1] * 100).toFixed(0)}%`
      : `${arr[0]}-${arr[1]}`;
  };

  if (loading) return <div className="loading">Ładowanie danych...</div>;

  return (
    <div className="container">
      <header className="header">
        <h1>Panel Analityczny Archetypów</h1>
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

      {archetypes.map((arch) => {
        const relatedPortfolios = summaryData.filter(p => p.archetype_key === arch.key);

        return (
          <section key={arch.key} className="section">
            <div className="arch-header">
              <h2>{arch.name}</h2>
              <p>{arch.summary}</p>
            </div>

            <div className="table-wrapper">
              <table className="results-table">
                <thead>
                  <tr className="header-group">
                    <th className="sticky-col">Info</th>
                    <th colSpan="3">Time Weights (%)</th>
                    <th colSpan="5">Config</th>
                    <th colSpan="6">Metric Weights (%)</th>
                    <th colSpan="2">Results</th>
                  </tr>
                  <tr className="th-row">
                    <th className="sticky-col">ID / Name</th>
                    {/* ... (inne nagłówki bez zmian) ... */}
                    <th onClick={() => handleSort("short")} className="sortable">
                      Short {sortConfig.key === "short" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("mid")} className="sortable">
                      Mid {sortConfig.key === "mid" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("long")} className="sortable">
                      Long {sortConfig.key === "long" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("min_exposure")} className="sortable">
                    Min {sortConfig.key === "min_exposure" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("aggression_slope")} className="sortable">
                    Slope {sortConfig.key === "aggression_slope" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("exposure_baseline")} className="sortable">
                    Baseline {sortConfig.key === "exposure_baseline" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("rebalance_threshold")} className="sortable">
                      Rebal {sortConfig.key === "rebalance_threshold" && (sortConfig.direction === "asc" ? "▲" : "▼")}
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

                    <th onClick={() => handleSort("struct_safety")} className="sortable">
                      Safety {sortConfig.key === "struct_safety" && (sortConfig.direction === "asc" ? "▲" : "▼")}
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
                    <th onClick={() => handleSort("benchmark_diff")} className="sortable">
                      vs Bench {sortConfig.key === "benchmark_diff" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>
                  </tr>

                  <tr className="range-row">
                    <td className="sticky-col">TARGET</td>
                    <td>{fmtRange(arch.time_weights.short)}</td>
                    <td>{fmtRange(arch.time_weights.medium)}</td>
                    <td>{fmtRange(arch.time_weights.long)}</td>
                    <td>{fmtRange(arch.min_exposure)}</td>
                    <td>{fmtRange(arch.aggression_slope)}</td>
                    <td>{fmtRange(arch.exposure_baseline, false)}</td>
                    <td>{fmtRange(arch.rebalance_threshold)}</td>
                    <td>{fmtRange(arch.temp, false)}</td>
                    <td>{fmtRange(arch.metric_weights.asym)}</td>
                    <td>{fmtRange(arch.metric_weights.conv)}</td>
                    <td>{fmtRange(arch.metric_weights.safe)}</td>
                    <td>{fmtRange(arch.metric_weights.val)}</td>
                    <td>{fmtRange(arch.metric_weights.fund)}</td>
                    <td>{fmtRange(arch.metric_weights.tech)}</td>
                    <td></td>
                    <td></td>
                  </tr>
                </thead>

                <tbody>
                  {sortData(relatedPortfolios).map((p) => {
                    const diffValue = p.benchmark_diff * 100;
                    return (
                      <tr key={p.id}>
                        <td className="sticky-col name-cell">
                          <strong>{p.name.replace("Portfolio ", "")}</strong> <span className="id">({p.id})</span>
                        </td>
                        {/* Wartości configu */}
                        <td>{(p.short_term_weight * 100).toFixed(1)}%</td>
                        <td>{(p.medium_term_weight * 100).toFixed(1)}%</td>
                        <td>{(p.long_term_weight * 100).toFixed(1)}%</td>
                        <td>{p.min_exposure}</td>
                        <td>{p.aggression_slope}</td>
                        <td>{p.exposure_baseline}</td>
                        <td>{(p.rebalance_threshold * 100).toFixed(1)}%</td>
                        <td>{p.softmax_temp}</td>
                        <td>{(p.metric_weights.relative_asymmetry_profile * 100).toFixed(1)}%</td>
                        <td>{(p.metric_weights.relative_conviction * 100).toFixed(1)}%</td>
                        <td>{(p.metric_weights.relative_structural_safety * 100).toFixed(1)}%</td>
                        <td>{(p.metric_weights.relative_valuation_sustainability * 100).toFixed(1)}%</td>
                        <td>{(p.metric_weights.relative_fundamental_support * 100).toFixed(1)}%</td>
                        <td>{(p.metric_weights.relative_technical_strength * 100).toFixed(1)}%</td>

                        {/* Wynik % */}
                        <td className={`performance ${p.change_ratio >= 0 ? "positive" : "negative"}`}>
                          {(p.change_ratio * 100).toFixed(2)}%
                        </td>

                        {/* Różnica benchmarkowa */}
                        <td className={`benchmark ${diffValue >= 0 ? "positive" : "negative"}`}>
                          {diffValue > 0 ? "+" : ""}{diffValue.toFixed(2)}pp
                        </td>
                      </tr>
                    );
                  })}

                  <tr className="summary-row-simple">
                    <td className="sticky-col summary-label">ŚREDNIA (σ)</td>
                    {renderStatsCell(relatedPortfolios, keyMap.short)}
                    {renderStatsCell(relatedPortfolios, keyMap.mid)}
                    {renderStatsCell(relatedPortfolios, keyMap.long)}
                    {renderStatsCell(relatedPortfolios, keyMap.min_exposure)}
                    {renderStatsCell(relatedPortfolios, keyMap.aggression_slope)}
                    {renderStatsCell(relatedPortfolios, keyMap.exposure_baseline, false)}
                    {renderStatsCell(relatedPortfolios, keyMap.rebalance_threshold)}
                    {renderStatsCell(relatedPortfolios, keyMap.temp, false)}
                    {renderStatsCell(relatedPortfolios, keyMap.asym)}
                    {renderStatsCell(relatedPortfolios, keyMap.conv)}
                    {renderStatsCell(relatedPortfolios, keyMap.struct_safety)}
                    {renderStatsCell(relatedPortfolios, keyMap.val)}
                    {renderStatsCell(relatedPortfolios, keyMap.fund)}
                    {renderStatsCell(relatedPortfolios, keyMap.tech)}
                    {renderStatsCell(relatedPortfolios, "change_ratio")}
                    {renderStatsCell(relatedPortfolios, "benchmark_diff", false, 2, true)}
                  </tr>


                  <tr className="summary-row-simple">
                    <td className="sticky-col summary-label">ŚREDNIA TOP 30%(σ)</td>
                    {renderStatsCell(relatedPortfolios, keyMap.short, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.mid, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.long, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.min_exposure, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.aggression_slope, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.exposure_baseline, false, 2, false, 0.3)}

                    {renderStatsCell(relatedPortfolios, keyMap.rebalance_threshold, true, 2, false, 0.3)}


                    {renderStatsCell(relatedPortfolios, keyMap.temp, false, 2, false, 0.3)}

                    {renderStatsCell(relatedPortfolios, keyMap.asym, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.conv, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.struct_safety, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.val, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.fund, true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, keyMap.tech, true, 2, false, 0.3)}

                    {renderStatsCell(relatedPortfolios, "change_ratio", true, 2, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, "benchmark_diff", false, 2, true, 0.3)}
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