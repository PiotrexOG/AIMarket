import React, { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const ArchetypeAverageChart = ({ data }) => {
  // Te same definicje metryk dla spójności
  const metrics = [
    { label: "Asymmetry", key: "metric_weights.relative_asymmetry_profile", color: "#8884d8" },
    { label: "Conviction", key: "metric_weights.relative_conviction", color: "#82ca9d" },
    { label: "Structural Safety", key: "metric_weights.relative_structural_safety", color: "#ffc658" },
    { label: "Valuation", key: "metric_weights.relative_valuation_sustainability", color: "#ff8042" },
    { label: "Fundamental", key: "metric_weights.relative_fundamental_support", color: "#0088FE" },
    { label: "Technical", key: "metric_weights.relative_technical_strength", color: "#00C49F" },
  ];

  const getValue = (obj, path) =>
    path.split(".").reduce((o, key) => o?.[key], obj);

  const aggregatedData = useMemo(() => {
    // 1. Grupowanie danych per archetyp
    const groups = data.reduce((acc, curr) => {
      const key = curr.archetype_key || "unknown";
      if (!acc[key]) {
        acc[key] = { name: key, count: 0, totalResult: 0, metricSums: {} };
        metrics.forEach(m => acc[key].metricSums[m.label] = 0);
      }
      
      acc[key].count += 1;
      acc[key].totalResult += curr.change_ratio;
      metrics.forEach(m => {
        acc[key].metricSums[m.label] += getValue(curr, m.key) || 0;
      });
      
      return acc;
    }, {});

    // 2. Obliczanie średnich i formatowanie pod wykres
    return Object.values(groups)
      .map(group => {
        const avgResult = (group.totalResult / group.count) * 100;
        const item = {
          archetype: group.name,
          avgResult: avgResult.toFixed(2) + "%",
          rawResult: avgResult,
          count: group.count
        };

        metrics.forEach(m => {
          // Średnia waga danej metryki w archetypie (w %)
          item[m.label] = (group.metricSums[m.label] / group.count) * 100;
        });

        return item;
      })
      // 3. Sortowanie według średniego wyniku
      .sort((a, b) => a.rawResult - b.rawResult);
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ 
          backgroundColor: "#fff", 
          border: "1px solid #ccc", 
          padding: "12px", 
          fontSize: "13px",
          boxShadow: "3px 3px 10px rgba(0,0,0,0.15)"
        }}>
          <p style={{ fontWeight: "bold", margin: "0 0 5px 0", color: "#333" }}>
            Archetyp: {label.toUpperCase()}
          </p>
          <p style={{ margin: "0 0 10px 0", fontSize: "12px", color: "#666" }}>
            Liczba próbek: {data.count}
          </p>
          <p style={{ marginBottom: "10px" }}>
            Średni wynik: <strong style={{ color: data.rawResult >= 0 ? "green" : "red" }}>
              {data.avgResult}
            </strong>
          </p>
          <hr style={{ border: "0.5px solid #eee" }} />
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, margin: "2px 0" }}>
              {entry.name}: {entry.value.toFixed(1)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: "100%", height: 500, padding: "20px" }}>
      <h3>Średnie Proporcje Metryk per Archetyp</h3>
      <p style={{ fontSize: "12px", color: "#666", marginTop: "-10px" }}>
        (Posortowane od najsłabszego do najlepszego średniego wyniku)
      </p>
      <div style={{ width: "100%", height: "90%" }}>
        <ResponsiveContainer>
          <BarChart
            data={aggregatedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="archetype" 
              tick={{ fontSize: 12, fontWeight: 'bold' }}
              dy={10}
            />
            <YAxis 
              unit="%" 
              domain={[0, 100]} 
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: "20px" }} />
            
            {metrics.map((m) => (
              <Bar 
                key={m.label}
                dataKey={m.label} 
                stackId="a" 
                fill={m.color} 
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ArchetypeAverageChart;