import React, { useMemo } from "react";
import {
  ComposedChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
  Cell,
  ReferenceLine,
  ErrorBar
} from "recharts";

const ArchetypePerformanceChart = ({ data, archetypes, archColorMap }) => {
  const chartData = useMemo(() => {
    // 1. Grupowanie danych i zbieranie wszystkich punktów
    const groups = data.reduce((acc, curr) => {
      const key = curr.archetype_key;
      if (!acc[key]) acc[key] = { key, results: [] };
      acc[key].results.push(curr.change_ratio * 100);
      return acc;
    }, {});

    // 2. Obliczanie statystyk
    return Object.values(groups)
      .map((group) => {
        const archInfo = archetypes.find((a) => a.key === group.key);
        const average = group.results.reduce((a, b) => a + b, 0) / group.results.length;
        const min = Math.min(...group.results);
        const max = Math.max(...group.results);

        return {
          key: group.key,
          name: archInfo?.name || group.key,
          averageResult: average,
          // Przygotowanie "widełek" dla linii pionowej (ErrorBar)
          // ErrorBar w Recharts przyjmuje wartości relatywne do punktu głównego
          errorRange: [average - min, max - average], 
          // Surowe dane dla małych kropek
          allPoints: group.results.map(val => ({ val, key: group.key })),
          count: group.results.length
        };
      })
      .sort((a, b) => a.averageResult - b.averageResult);
  }, [data, archetypes]);

  // Spłaszczona lista wszystkich punktów dla małych kropek
  const individualPoints = useMemo(() => {
    return chartData.flatMap(group => 
      group.allPoints.map(p => ({
        name: group.name,
        key: group.key,
        value: p.val,
        jitter: Math.random() * 0.4 - 0.2 // lekki rozrzut
      }))
    );
  }, [chartData]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      // Sprawdzamy czy to punkt zbiorczy czy pojedynczy
      const isGroup = d.averageResult !== undefined;
      
      return (
        <div style={{ backgroundColor: "#fff", border: "1px solid #ccc", padding: "10px", borderRadius: "4px" }}>
          <p style={{ fontWeight: "bold", margin: "0 0 5px 0" }}>{d.name}</p>
          <p style={{ margin: 0 }}>
            {isGroup ? "Średnia: " : "Wynik: "}
            <strong>{(isGroup ? d.averageResult : d.value).toFixed(2)}%</strong>
          </p>
          {isGroup && (
            <p style={{ margin: 0, fontSize: "11px", color: "#666" }}>
              Liczba portfeli: {d.count}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: "100%", height: 500, marginTop: "20px", padding: "20px", background: "#fff", borderRadius: "8px", border: "1px solid #eee" }}>
      <h3 style={{ textAlign: "center", marginBottom: "20px" }}>Rozkład Wyników wg Archetypu</h3>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
          <XAxis 
            dataKey="name" 
            angle={-45} 
            textAnchor="end" 
            interval={0} 
            height={80} 
            fontSize={12}
            type="category"
            allowDuplicatedCategory={false}
          />
          <YAxis 
            unit="%" 
            fontSize={12}
            label={{ value: 'Wynik (%)', angle: -90, position: 'insideLeft' }} 
          />
          <ZAxis type="number" range={[50, 400]} /> {/* Kontrola wielkości kropek */}
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <ReferenceLine y={0} stroke="#000" strokeWidth={1} />

          {/* 1. Małe kropki (pojedyncze przypadki) */}
          <Scatter
            data={individualPoints}
            dataKey="value"
            shape={(props) => {
                const { cx, cy, payload } = props;
                return (
                <circle
                    cx={cx + payload.jitter * 20} // przesunięcie poziome
                    cy={cy}
                    r={3}
                    fill={archColorMap[payload.key] || "#8884d8"}
                />
                );
            }}
            />

          {/* 2. Duże kropki (średnia) + Linia pionowa */}
          <Scatter 
            data={chartData} 
            dataKey="averageResult"
          >
            <ErrorBar 
              dataKey="errorRange" 
              width={4} 
              strokeWidth={2} 
              strokeOpacity={0.6}
            />
            {chartData.map((entry, index) => (
              <Cell 
                key={`avg-${index}`} 
                fill={archColorMap[entry.key] || "#8884d8"} 
                r={8} // Duża kropka
                stroke="#fff"
                strokeWidth={2}
              />
            ))}
          </Scatter>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ArchetypePerformanceChart;