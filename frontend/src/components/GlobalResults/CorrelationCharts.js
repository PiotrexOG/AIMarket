import React, { useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Label,
  Cell,
  ReferenceLine
} from "recharts";

const CorrelationCharts = ({ data, archColorMap }) => {

  const benchmarkValue = useMemo(() => {
    const benchmarkPortfolios = data.filter(p => p.archetype_key === "benchmark");
    if (benchmarkPortfolios.length === 0) return null;
    
    const avgChangeRatio = benchmarkPortfolios.reduce((sum, p) => sum + p.change_ratio, 0) / benchmarkPortfolios.length;
    return avgChangeRatio * 100; // na procenty
  }, [data]);

  // Lista parametrów do zmapowania (klucz z danych -> etykieta na wykresie)
  const metrics = [
    { label: "Short Term Weight", key: "short_term_weight" },
    { label: "Mid Term Weight", key: "medium_term_weight" },
    { label: "Long Term Weight", key: "long_term_weight" },
    { label: "Risk Tolerance", key: "risk_tolerance" },
    { label: "Rebalance Threshold", key: "rebalance_threshold" },
    { label: "Min Score Threshold", key: "min_score_threshold" },
    { label: "Softmax Temp", key: "softmax_temp" },
    { label: "Asymmetry", key: "metric_weights.relative_asymmetry_profile" },
    { label: "Conviction", key: "metric_weights.relative_conviction" },
    { label: "Structural Risk", key: "metric_weights.relative_structural_risk" },
    { label: "Valuation", key: "metric_weights.relative_valuation_sustainability" },
    { label: "Fundamental", key: "metric_weights.relative_fundamental_support" },
    { label: "Technical", key: "metric_weights.relative_technical_strength" },
  ];

  // Helper do pobierania wartości (obsługuje zagnieżdżone klucze jak metric_weights.xxx)
  const getValue = (obj, path) =>
    path.split(".").reduce((o, key) => o?.[key], obj);

  // Customowy Tooltip, aby pokazać nazwę portfela
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const p = payload[0].payload;
      return (
        <div style={{ backgroundColor: "#fff", border: "1px solid #ccc", padding: "10px", fontSize: "12px" }}>
          <p style={{ fontWeight: "bold", margin: 0 }}>{p.name}</p>
          <p style={{ margin: 0 }}>Parametr: {payload[0].value.toFixed(3)}</p>
          <p style={{ margin: 0, color: p.change_ratio >= 0 ? "green" : "red" }}>
            Result: {(p.change_ratio * 100).toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="correlation-grid"
    style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)', // zmień 3 na dowolną liczbę N
      gap: '20px'
    }}
    >
      {metrics.map((m) => {
        // Przygotowanie danych pod konkretny wykres
        const chartData = data.map((p) => ({
          x: getValue(p, m.key),
          y: p.change_ratio * 100, // zamieniamy na procenty dla czytelności Y
          name: p.name,
          archetype_key: p.archetype_key,
          change_ratio: p.change_ratio
        }));

        return (
          <div key={m.label} className="chart-container">
            <h3>{m.label} vs Result (%)</h3>
            <div style={{ width: "100%", height: 250 }}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis 
                    type="number" 
                    dataKey="x" 
                    name={m.label} 
                    fontSize={11}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    name="Result" 
                    unit="%" 
                    fontSize={11}
                  />
                  <Tooltip content={<CustomTooltip />} />

                      {/* 🔥 DODAJEMY POZIOMĄ LINIĘ BENCHMARKU */}
                  {benchmarkValue !== null && (
                    <ReferenceLine
                      y={benchmarkValue}
                      stroke="#ff4d4f"
                      strokeDasharray="5 5"
                      strokeWidth={2}
                      label={{
                        position: "insideTopRight",
                        value: `Benchmark`,
                        fill: "#ff4d4f",
                        fontSize: 9,
                        fontWeight: "bold"
                      }}
                    />
                  )}
                  
                  <Scatter name={m.label} data={chartData}>
                    {chartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={archColorMap[entry.archetype_key] || "#8884d8"} 
                        stroke="#fff"
                        strokeWidth={1}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CorrelationCharts;