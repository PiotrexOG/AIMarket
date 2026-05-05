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

const MetricCompositionChart = ({ data }) => {
  // Helper do pobierania zagnieżdżonych wartości
  const getValue = (obj, path) =>
    path.split(".").reduce((o, key) => o?.[key], obj);

  // Definicja metryk i ich kolorów
  const metrics = [
    { label: "Asymmetry", key: "metric_weights.relative_asymmetry_profile", color: "#8884d8" },
    { label: "Conviction", key: "metric_weights.relative_conviction", color: "#82ca9d" },
    { label: "Structural Risk", key: "metric_weights.relative_structural_risk", color: "#ffc658" },
    { label: "Valuation", key: "metric_weights.relative_valuation_sustainability", color: "#ff8042" },
    { label: "Fundamental", key: "metric_weights.relative_fundamental_support", color: "#0088FE" },
    { label: "Technical", key: "metric_weights.relative_technical_strength", color: "#00C49F" },
  ];

  const processedData = useMemo(() => {
    return [...data]
      // 1. Sortujemy od najgorszego do najlepszego wyniku, żeby widzieć trend
      .sort((a, b) => a.change_ratio - b.change_ratio)
      .map((p) => {
        const item = {
          name: p.name,
          result: (p.change_ratio * 100).toFixed(2) + "%",
          rawResult: p.change_ratio,
        };
        
        // 2. Mapujemy metryki na wartości procentowe (zakładając, że są w formacie 0.0-1.0)
        metrics.forEach((m) => {
          const val = getValue(p, m.key);
          item[m.label] = val * 100; 
        });
        
        return item;
      });
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ 
          backgroundColor: "#fff", 
          border: "1px solid #ccc", 
          padding: "10px", 
          fontSize: "12px",
          boxShadow: "2px 2px 5px rgba(0,0,0,0.1)"
        }}>
          <p style={{ fontWeight: "bold", marginBottom: "5px" }}>{label}</p>
          <p style={{ color: "#333", marginBottom: "10px" }}>
            Wynik: <strong>{payload[0].payload.result}</strong>
          </p>
          <hr />
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, margin: 0 }}>
              {entry.name}: {entry.value.toFixed(1)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-wrapper" style={{ width: "100%", height: 500, padding: "20px" }}>
      <h3>Proporcje Metryk vs Wynik (posortowane od najniższego wyniku)</h3>
      <div style={{ width: "100%", height: "100%" }}>
        <ResponsiveContainer>
          <BarChart
            data={processedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              interval={0} 
              fontSize={10} 
            />
            <YAxis 
              unit="%" 
              domain={[0, 100]} 
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: "20px" }} />
            
            {/* Generujemy słupki automatycznie na podstawie listy metryk */}
            {metrics.map((m) => (
              <Bar 
                key={m.label}
                dataKey={m.label} 
                stackId="a" // To sprawia, że są skumulowane
                fill={m.color} 
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MetricCompositionChart;