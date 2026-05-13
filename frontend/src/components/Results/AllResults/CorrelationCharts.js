import React, { useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  ZAxis // Dodane dla kontroli trendu
} from "recharts";

const CorrelationCharts = ({ data, archColorMap }) => {
  const benchmarkValue = useMemo(() => {
    const benchmarkPortfolios = data.filter(p => p.archetype_key === "benchmark");
    if (benchmarkPortfolios.length === 0) return null;
    const avgChangeRatio = benchmarkPortfolios.reduce((sum, p) => sum + p.change_ratio, 0) / benchmarkPortfolios.length;
    return avgChangeRatio * 100;
  }, [data]);

  const metrics = [
    { label: "Short Term Weight", key: "short_term_weight" },
    { label: "Mid Term Weight", key: "medium_term_weight" },
    { label: "Long Term Weight", key: "long_term_weight" },
    { label: "Min Exposure", key: "min_exposure" },
    { label: "Aggression Slope", key: "aggression_slope" },
    { label: "Expousure Baseline", key: "exposure_baseline" },
    { label: "Softmax Temp", key: "softmax_temp" },
    { label: "Asymmetry", key: "metric_weights.relative_asymmetry_profile" },
    { label: "Conviction", key: "metric_weights.relative_conviction" },
    { label: "Structural Risk", key: "metric_weights.relative_structural_risk" },
    { label: "Valuation", key: "metric_weights.relative_valuation_sustainability" },
    { label: "Fundamental", key: "metric_weights.relative_fundamental_support" },
    { label: "Technical", key: "metric_weights.relative_technical_strength" },
  ];

  const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

  // --- FUNKCJA LICZĄCA ŚREDNIE W KUBEŁKACH ---
  const calculateTrendLine = (chartData, numBuckets = 40) => {
    if (!chartData || chartData.length === 0) return [];

    const xs = chartData.map(d => d.x);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const range = maxX - minX;

    if (range === 0) return [];

    const buckets = Array.from({ length: numBuckets }, () => ({ sumY: 0, count: 0 }));

    chartData.forEach(p => {
      // Wyliczamy do którego kubełka wpada punkt
      let bucketIdx = Math.floor(((p.x - minX) / range) * numBuckets);
      if (bucketIdx >= numBuckets) bucketIdx = numBuckets - 1;
      
      buckets[bucketIdx].sumY += p.y;
      buckets[bucketIdx].count += 1;
    });

    return buckets
      .map((b, i) => {
        if (b.count === 0) return null;
        return {
          x: minX + (i + 0.5) * (range / numBuckets), // Środek kubełka na osi X
          y: b.sumY / b.count // Średnia na osi Y
        };
      })
      .filter(b => b !== null); // Usuwamy puste kubełki
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const p = payload[0].payload;
      // Nie pokazujemy tooltipa dla samej linii trendu (która nie ma 'name')
      if (!p.name) return null; 

      return (
        <div style={{ backgroundColor: "#fff", border: "1px solid #ccc", padding: "10px", fontSize: "12px", boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          <p style={{ fontWeight: "bold", margin: 0 }}>{p.name}</p>
          <p style={{ margin: 0 }}>Param: {p.x.toFixed(3)}</p>
          <p style={{ margin: 0, color: p.change_ratio >= 0 ? "green" : "red" }}>
            Result: {(p.change_ratio * 100).toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="correlation-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
      {metrics.map((m) => {
        const chartData = data.map((p) => ({
          x: getValue(p, m.key),
          y: p.change_ratio * 100,
          name: p.name,
          archetype_key: p.archetype_key,
          change_ratio: p.change_ratio
        }));

        // Obliczamy dane dla linii trendu
        const trendData = calculateTrendLine(chartData, 30);

        return (
          <div key={m.label} className="chart-container" style={{ background: '#f9f9f9', padding: '10px', borderRadius: '8px' }}>
            <h3 style={{ fontSize: '14px', marginBottom: '10px' }}>{m.label} vs Result (%)</h3>
            <div style={{ width: "100%", height: 250 }}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                  <XAxis type="number" dataKey="x" fontSize={10} tick={{fill: '#666'}} />
                  <YAxis type="number" dataKey="y" unit="%" fontSize={10} tick={{fill: '#666'}} />
                  <ZAxis range={[50, 50]} /> {/* Stały rozmiar kropki */}
                  <Tooltip content={<CustomTooltip />} />

                  {benchmarkValue !== null && (
                    <ReferenceLine y={benchmarkValue} stroke="#ff4d4f" strokeDasharray="5 5" />
                  )}
                  
                  {/* GŁÓWNE PUNKTY - z przezroczystością */}
                  <Scatter 
                    data={chartData} 
                    fillOpacity={0.4} // <--- Kluczowe dla czytelności masowej
                  >
                    {chartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={archColorMap[entry.archetype_key] || "#8884d8"} 
                      />
                    ))}
                  </Scatter>

                  {/* LINIA TRENDU (Średnie w kubełkach) */}
                  <Scatter 
                    data={trendData} 
                    line={{ stroke: '#ff4d4f', strokeWidth: 3 }} // Czerwona linia
                    shape={() => null} // Ukrywamy kropki dla samej linii
                    legendType="none"
                    isAnimationActive={false}
                  />
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