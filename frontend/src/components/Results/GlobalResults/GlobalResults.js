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
        
        // Obliczamy diff od razu przy ładowaniu
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
      } catch (err) {
        console.error("Błąd ładowania:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAllData();
  }, [start, end]);

  // Mapowanie kluczy do sortowania dla dostępnych pól
  const keyMap = {
    top_m_share: "top_m_share",
    investment_time_days: "investment_time_days",
    rebalance_time_share: "rebalance_time_share",
    change_ratio: "change_ratio",
    benchmark_diff: "benchmark_diff"
  };

  const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

  const calculateStats = (data, path, centyl) => {
    if (!data.length) return { avg: 0, std: 0 };
  
    const sorted = [...data].sort((a, b) => b.change_ratio - a.change_ratio);
    const size = Math.max(1, Math.floor(sorted.length * centyl));
    const selectedData = sorted.slice(0, size);
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
                    <th colSpan="3">Config</th>
                    <th colSpan="2">Results</th>
                  </tr>
                  <tr className="th-row">
                    <th className="sticky-col">ID / Name</th>

                    <th onClick={() => handleSort("top_m_share")} className="sortable">
                      Top M Share {sortConfig.key === "top_m_share" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("investment_time_days")} className="sortable">
                      Inv. Time (Days) {sortConfig.key === "investment_time_days" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("rebalance_time_share")} className="sortable">
                      Rebalance Share {sortConfig.key === "rebalance_time_share" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>

                    <th onClick={() => handleSort("change_ratio")} className="sortable">
                      % {sortConfig.key === "change_ratio" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>
                    
                    <th onClick={() => handleSort("benchmark_diff")} className="sortable">
                      vs Bench {sortConfig.key === "benchmark_diff" && (sortConfig.direction === "asc" ? "▲" : "▼")}
                    </th>
                  </tr>

                  {/* Wiersz TARGET wyświetlający zakresy z obiektu archetype */}
                  <tr className="range-row">
                    <td className="sticky-col">TARGET</td>
                    <td>{fmtRange(arch.top_m_share, true)}</td>
                    <td>{fmtRange(arch.investment_time_days, false)}</td>
                    <td>{fmtRange(arch.rebalance_time_share, true)}</td>
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
                        
                        {/* Wartości parametrów konfiguracyjnych */}
                        <td>{(p.top_m_share * 100).toFixed(1)}%</td>
                        <td>{p.investment_time_days}d</td>
                        <td>{(p.rebalance_time_share * 100).toFixed(1)}%</td>

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

                  {/* Statystyki: Średnia ogólna */}
                  <tr className="summary-row-simple">
                    <td className="sticky-col summary-label">ŚREDNIA (σ)</td>
                    {renderStatsCell(relatedPortfolios, "top_m_share", true, 1)}
                    {renderStatsCell(relatedPortfolios, "investment_time_days", false, 0)}
                    {renderStatsCell(relatedPortfolios, "rebalance_time_share", true, 1)}
                    {renderStatsCell(relatedPortfolios, "change_ratio", true, 2)}
                    {renderStatsCell(relatedPortfolios, "benchmark_diff", false, 2, true)}
                  </tr>

                  {/* Statystyki: Średnia dla Top 30% */}
                  <tr className="summary-row-simple">
                    <td className="sticky-col summary-label">ŚREDNIA TOP 30%(σ)</td>
                    {renderStatsCell(relatedPortfolios, "top_m_share", true, 1, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, "investment_time_days", false, 0, false, 0.3)}
                    {renderStatsCell(relatedPortfolios, "rebalance_time_share", true, 1, false, 0.3)}
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