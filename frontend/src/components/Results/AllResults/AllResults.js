import { useEffect, useState } from "react";
import { fetchArchetypes, fetchPerformanceSummary } from "./../utils/fetchUtils";
import { generateDistinctColors } from "./../../common/utils";
import "../GlobalResults/GlobalResults.css";
import ArchetypeCorrelationHeatmap from "./ArchetypeCorrelationHeatmap";
import ArchetypePerformanceChart from "./ArchetypePerformanceChart";
import ArchetypeRadarAnalysis from "./ArchetypeRadarAnalysis";
import CorrelationCharts from "./CorrelationCharts";
import ResultsTable from "./ResultsTable";
import ChartRangeButtons from "./../../common/ChartRangeButtons";
import { useChartRange } from "./../../common/useChartRange";

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



      {/* <div className="section">
        <ResultsTable 
          data={sortedData} 
          sortConfig={sortConfig} 
          onSort={handleSort} 
          archColorMap={archColorMap} 
          getArchName={getArchName} 
          keyMap={keyMap}
        />
      </div> */}

      <div className="section">
        <h2>Ranking Archetypów</h2>
        <ArchetypePerformanceChart data={summaryData} archetypes={archetypes} archColorMap={archColorMap} />
      </div>


      {!loading && summaryData.length > 0 && (
        <div className="section">
          <h2 style={{ padding: '0 20px' }}>Analiza Korelacji Parametrów</h2>
          <ArchetypeCorrelationHeatmap data={summaryData} archColorMap={archColorMap} />
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