import React, { useMemo, useState } from "react";
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

// --- Pomocnicze funkcje statystyczne ---
const calculateMedian = (sortedArr) => {
  if (sortedArr.length === 0) return 0;
  const mid = Math.floor(sortedArr.length / 2);
  return sortedArr.length % 2 !== 0
    ? sortedArr[mid]
    : (sortedArr[mid - 1] + sortedArr[mid]) / 2;
};

// Downside Deviation względem zadanej wartości referencyjnej (Benchmarku)
const calculateDownsideDeviation = (results, benchmarkReturn) => {
  if (results.length === 0) return 0;
  const squaredDownsideDiffs = results.map((val) => {
    const diff = val - benchmarkReturn;
    return diff < 0 ? Math.pow(diff, 2) : 0;
  });
  const sum = squaredDownsideDiffs.reduce((a, b) => a + b, 0);
  return Math.sqrt(sum / results.length);
};

// Rysowanie gwiazdki dla Information Ratio
const StarShape = ({ cx, cy, fill, stroke }) => {
  const points = [];
  const outerRadius = 6;
  const innerRadius = 3.5;
  for (let i = 0; i < 10; i++) {
    const radius = i % 2 === 0 ? outerRadius : innerRadius;
    const angle = (i * Math.PI) / 5 - Math.PI / 2;
    points.push(`${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`);
  }
  return (
    <polygon
      points={points.join(" ")}
      fill={fill}
      stroke={stroke}
      strokeWidth={1.5}
      style={{ filter: "drop-shadow(0px 2px 3px rgba(0,0,0,0.3))" }}
    />
  );
};

// Rysowanie trójkąta dla Średniej
const TriangleShape = ({ cx, cy, fill, stroke }) => {
  const r = 5;
  const points = `${cx},${cy - r} ${cx - r},${cy + r} ${cx + r},${cy + r}`;
  return (
    <polygon
      points={points}
      fill={fill}
      stroke={stroke}
      strokeWidth={1.5}
      style={{ filter: "drop-shadow(0px 2px 3px rgba(0,0,0,0.3))" }}
    />
  );
};

const ArchetypePerformanceChart = ({ data, archetypes, archColorMap }) => {
  const [sortBy, setSortBy] = useState("median"); // 'median' | 'average' | 'information'

  // Stan dla widoczności poszczególnych elementów (od 0 do 3 aktywnych opcji)
  const [visibleElements, setVisibleElements] = useState({
    median: true,
    average: true,
    information: true
  });

  const toggleVisibility = (key) => {
    setVisibleElements((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // 1. Wyznaczenie jednolitej wartości benchmarku dla WSZYSTKICH archetypów
  // Szukamy w danych wpisów przypisanych do archetypu 'benchmark'
  const benchmarkValue = useMemo(() => {
    const benchGroup = data.filter(
      (d) => d.archetype_key === "benchmark" || d.archetype_key === "Benchmark"
    );
    if (benchGroup.length === 0) return 0;
    const sortedBench = benchGroup.map((d) => d.change_ratio * 100).sort((a, b) => a - b);
    return calculateMedian(sortedBench);
  }, [data]);

  // 2. Przetworzenie danych archetypów
  const chartData = useMemo(() => {
    const groups = data.reduce((acc, curr) => {
      const key = curr.archetype_key;
      if (!acc[key]) acc[key] = { key, results: [] };
      acc[key].results.push(curr.change_ratio * 100);
      return acc;
    }, {});

    const processed = Object.values(groups).map((group) => {
      const archInfo = archetypes.find((a) => a.key === group.key);
      const sortedResults = [...group.results].sort((a, b) => a - b);

      const average = sortedResults.reduce((a, b) => a + b, 0) / sortedResults.length;
      const median = calculateMedian(sortedResults);

      // Downside Deviation wyliczane ZAWSZE względem wyznaczonego benchmarkValue
      const downsideDev = calculateDownsideDeviation(sortedResults, benchmarkValue);

      // Information Ratio = (Mediana Archetypu - Wartość Benchmarku) / Downside Deviation
      const informationRatio = downsideDev !== 0 ? (median - benchmarkValue) / downsideDev : 0;

      const min = sortedResults[0];
      const max = sortedResults[sortedResults.length - 1];

      return {
        key: group.key,
        name: archInfo?.name || group.key,
        averageResult: average,
        medianResult: median,
        downsideDev: downsideDev,
        informationRatio: informationRatio,
        errorRange: [median - min, max - median],
        sortedResults: sortedResults,
        count: group.results.length,
        isAverage: true
      };
    });

    return processed.sort((a, b) => {
      if (sortBy === "median") return a.medianResult - b.medianResult;
      if (sortBy === "average") return a.averageResult - b.averageResult;
      if (sortBy === "information") return a.informationRatio - b.informationRatio;
      return 0;
    });
  }, [data, archetypes, sortBy, benchmarkValue]);

  const individualPoints = useMemo(() => {
    return chartData.flatMap((group) =>
      group.sortedResults.map((val, index) => ({
        name: group.name,
        key: group.key,
        value: val,
        index: index,
        totalInGroup: group.count,
        isAverage: false
      }))
    );
  }, [chartData]);

  const CustomTick = ({ x, y, payload }) => {
    const dataItem = chartData.find((d) => d.name === payload.value);
    const color = dataItem ? archColorMap[dataItem.key] : "#666";

    return (
      <g transform={`translate(${x},${y})`}>
        <text
          x={0}
          y={0}
          dy={16}
          textAnchor="end"
          fill={color}
          transform="rotate(-45)"
          style={{ fontSize: "12px", fontWeight: "bold" }}
        >
          {payload.value}
        </text>
      </g>
    );
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const groupPayload = payload.find((p) => p.payload.isAverage);
      if (!groupPayload) return null;

      const d = groupPayload.payload;

      return (
        <div
          style={{
            backgroundColor: "#fff",
            border: "1px solid #ccc",
            padding: "12px",
            borderRadius: "6px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
          }}
        >
          <p style={{ fontWeight: "bold", margin: "0 0 8px 0", color: archColorMap[d.key] }}>
            {d.name}
          </p>
          <p style={{ margin: "2px 0", fontSize: "13px" }}>
            ● Mediana: <strong>{d.medianResult.toFixed(2)}%</strong>
          </p>
          <p style={{ margin: "2px 0", fontSize: "13px" }}>
            ▲ Średnia: <strong>{d.averageResult.toFixed(2)}%</strong>
          </p>
          <p style={{ margin: "2px 0", fontSize: "13px", color: "#0275d8" }}>
            ★ Information Ratio (vs Bench): <strong>{d.informationRatio.toFixed(2)}</strong>
          </p>
          <p style={{ margin: "2px 0", fontSize: "11px", color: "#d9534f" }}>
            Downside Dev (vs Bench): {d.downsideDev.toFixed(2)}%
          </p>
          <p style={{ margin: "6px 0 0 0", fontSize: "11px", color: "#666" }}>
            Liczba portfeli: {d.count}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      style={{
        width: "98%",
        background: "#fff",
        borderRadius: "8px",
        border: "1px solid #eee",
        padding: "16px"
      }}
    >
      <h3 style={{ textAlign: "center", marginBottom: "12px" }}>
        Rozkład Wyników wg Archetypu
      </h3>

      {/* Kontrolki: Sortowanie i Wyświetlanie */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "12px",
          marginBottom: "16px"
        }}
      >
        {/* Przełącznik sortowania */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "13px", fontWeight: "bold" }}>Sortuj po:</span>
          <button
            onClick={() => setSortBy("median")}
            style={{
              padding: "6px 14px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              background: sortBy === "median" ? "#1890ff" : "#fff",
              color: sortBy === "median" ? "#fff" : "#333",
              cursor: "pointer",
              fontWeight: "bold"
            }}
          >
            ● Medianie
          </button>
          <button
            onClick={() => setSortBy("average")}
            style={{
              padding: "6px 14px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              background: sortBy === "average" ? "#1890ff" : "#fff",
              color: sortBy === "average" ? "#fff" : "#333",
              cursor: "pointer",
              fontWeight: "bold"
            }}
          >
            ▲ Średniej
          </button>
          <button
            onClick={() => setSortBy("information")}
            style={{
              padding: "6px 14px",
              borderRadius: "4px",
              border: "1px solid #ccc",
              background: sortBy === "information" ? "#1890ff" : "#fff",
              color: sortBy === "information" ? "#fff" : "#333",
              cursor: "pointer",
              fontWeight: "bold"
            }}
          >
            ★ Information Ratio
          </button>
        </div>

        {/* Przełączniki widoczności wskaźników (Wielokrotny wybór 0-3) */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "13px", fontWeight: "bold" }}>Pokaż na wykresie:</span>
          <button
            onClick={() => toggleVisibility("median")}
            style={{
              padding: "5px 12px",
              borderRadius: "20px",
              border: visibleElements.median ? "2px solid #52c41a" : "1px solid #ccc",
              background: visibleElements.median ? "#f6ffed" : "#f5f5f5",
              color: visibleElements.median ? "#278000" : "#888",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "12px"
            }}
          >
            {visibleElements.median ? "✓" : "+"} ● Mediana
          </button>
          <button
            onClick={() => toggleVisibility("average")}
            style={{
              padding: "5px 12px",
              borderRadius: "20px",
              border: visibleElements.average ? "2px solid #fa8c16" : "1px solid #ccc",
              background: visibleElements.average ? "#fff7e6" : "#f5f5f5",
              color: visibleElements.average ? "#d46b08" : "#888",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "12px"
            }}
          >
            {visibleElements.average ? "✓" : "+"} ▲ Średnia
          </button>
          <button
            onClick={() => toggleVisibility("information")}
            style={{
              padding: "5px 12px",
              borderRadius: "20px",
              border: visibleElements.information ? "2px solid #1890ff" : "1px solid #ccc",
              background: visibleElements.information ? "#e6f7ff" : "#f5f5f5",
              color: visibleElements.information ? "#096dd9" : "#888",
              cursor: "pointer",
              fontWeight: "bold",
              fontSize: "12px"
            }}
          >
            {visibleElements.information ? "✓" : "+"} ★ Information Ratio
          </button>
        </div>
      </div>

      <div style={{ width: "100%", height: 800 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 20, right: 60, left: 20, bottom: 120 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              interval={0}
              height={80}
              type="category"
              allowDuplicatedCategory={false}
              padding={{ left: 50, right: 50 }}
              tick={<CustomTick />}
            />
            {/* Oś lewa dla wartości procentowych (% stóp zwrotu) */}
            <YAxis
              yAxisId="percent"
              unit="%"
              label={{ value: "Wynik (%)", angle: -90, position: "insideLeft" }}
            />
            {/* Oś prawa dla bezwymiarowego wskaźnika Information Ratio */}
            <YAxis
              yAxisId="information"
              orientation="right"
              label={{ value: "Information Ratio", angle: 90, position: "insideRight" }}
            />

            <ZAxis type="number" range={[50, 400]} />
            <Tooltip content={<CustomTooltip />} cursor={false} shared={false} />

            {benchmarkValue !== null && (
              <ReferenceLine
                yAxisId="percent"
                y={benchmarkValue}
                stroke="#ff4d4f"
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{
                  position: "right",
                  value: "BENCHMARK",
                  fill: "#ff4d4f",
                  fontSize: 10,
                  fontWeight: "bold"
                }}
              />
            )}

            <ReferenceLine yAxisId="percent" y={0} stroke="#000" />

            {/* Indywidualne punkty portfeli */}
            <Scatter
              yAxisId="percent"
              data={individualPoints}
              dataKey="value"
              isAnimationActive={false}
              tooltipType="none"
              shape={(props) => {
                const { cx, cy, payload } = props;
                const { index, totalInGroup } = payload;
                const availableWidth = 80;
                let xOffset = 0;

                if (totalInGroup > 1) {
                  xOffset = (index / (totalInGroup - 1)) * availableWidth - availableWidth / 2;
                }

                return (
                  <circle
                    cx={cx + xOffset}
                    cy={cy}
                    r={3.5}
                    fill={archColorMap[payload.key] || "#8884d8"}
                    fillOpacity={0.3}
                  />
                );
              }}
            />

            {/* 1. Mediana (KÓŁKO ●) z zakresem błędu min-max */}
            {visibleElements.median && (
              <Scatter yAxisId="percent" data={chartData} dataKey="medianResult">
                <ErrorBar
                  dataKey="errorRange"
                  width={10}
                  strokeWidth={2}
                  stroke="#333"
                  strokeOpacity={0.3}
                />
                {chartData.map((entry, index) => (
                  <Cell
                    key={`med-${index}`}
                    fill={archColorMap[entry.key] || "#8884d8"}
                    stroke="#fff"
                    strokeWidth={2}
                    style={{
                      filter: "drop-shadow(0px 2px 3px rgba(0,0,0,0.3))",
                      cursor: "pointer"
                    }}
                  />
                ))}
              </Scatter>
            )}

            {/* 2. Średnia (TRÓJKĄT ▲) */}
            {visibleElements.average && (
              <Scatter
                yAxisId="percent"
                data={chartData}
                dataKey="averageResult"
                shape={(props) => {
                  const color = archColorMap[props.payload.key] || "#8884d8";
                  return <TriangleShape cx={props.cx} cy={props.cy} fill={color} stroke="#fff" />;
                }}
              />
            )}

            {/* 3. Information Ratio (GWIAZDKA ★) po prawej osi Y */}
            {visibleElements.information && (
              <Scatter
                yAxisId="information"
                data={chartData}
                dataKey="informationRatio"
                shape={(props) => {
                  const color = archColorMap[props.payload.key] || "#8884d8";
                  return <StarShape cx={props.cx} cy={props.cy} fill={color} stroke="#fff" />;
                }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ArchetypePerformanceChart;