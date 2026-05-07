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
    const groups = data.reduce((acc, curr) => {
      const key = curr.archetype_key;
      if (!acc[key]) acc[key] = { key, results: [] };
      acc[key].results.push(curr.change_ratio * 100);
      return acc;
    }, {});

    return Object.values(groups)
      .map((group) => {
        const archInfo = archetypes.find((a) => a.key === group.key);
        const sortedResults = [...group.results].sort((a, b) => a - b);
        const average =
          sortedResults.reduce((a, b) => a + b, 0) / sortedResults.length;
        const min = sortedResults[0];
        const max = sortedResults[sortedResults.length - 1];

        return {
          key: group.key,
          name: archInfo?.name || group.key,
          averageResult: average,
          errorRange: [average - min, max - average],
          sortedResults: sortedResults,
          count: group.results.length,
          isAverage: true // 🔑 kluczowe
        };
      })
      .sort((a, b) => a.averageResult - b.averageResult);
  }, [data, archetypes]);

  const benchmarkValue = useMemo(() => {
    const bench = chartData.find((d) => d.key === "benchmark");
    return bench ? bench.averageResult : null;
  }, [chartData]);

  const individualPoints = useMemo(() => {
    return chartData.flatMap((group) =>
      group.sortedResults.map((val, index) => {
        // Zmieniamy logikę: przekazujemy index i całkowitą liczbę punktów
        return {
          name: group.name,
          key: group.key,
          value: val,
          index: index, // pozycja kropki (0, 1, 2...)
          totalInGroup: group.count, // ile ich jest w sumie w tym archetypie
          isAverage: false
        };
      })
    );
  }, [chartData]);

  const CustomTick = ({ x, y, payload, chartData, archColorMap }) => {
    // Znajdujemy dane archetypu na podstawie nazwy wyświetlanej na osi
    const dataItem = chartData.find((d) => d.name === payload.value);
    const color = dataItem ? archColorMap[dataItem.key] : "#666";
  
    return (
      <g transform={`translate(${x},${y})`}>
        <text
          x={0}
          y={0}
          dy={16}
          textAnchor="end"
          fill={color} // <--- Dynamiczny kolor
          transform="rotate(-45)"
          style={{ fontSize: "12px", fontWeight: "bold" }}
        >
          {payload.value}
        </text>
      </g>
    );
  };

  // ✅ POPRAWIONY TOOLTIP
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      // 🔴 bierzemy TYLKO średnią
      const groupPayload = payload.find((p) => p.payload.isAverage);

      if (!groupPayload) return null;

      const d = groupPayload.payload;

      return (
        <div
          style={{
            backgroundColor: "#fff",
            border: "1px solid #ccc",
            padding: "10px",
            borderRadius: "4px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.1)"
          }}
        >
          <p style={{ fontWeight: "bold", margin: "0 0 5px 0" }}>
            {d.name}
          </p>
          <p style={{ margin: 0 }}>
            Średnia: <strong>{d.averageResult.toFixed(2)}%</strong>
          </p>
          <p style={{ margin: 0, fontSize: "11px", color: "#666" }}>
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
        width: "100%",
        height: 500,
        background: "#fff",
        borderRadius: "8px",
        border: "1px solid #eee"
      }}
    >
      <h3 style={{ textAlign: "center", marginBottom: "20px" }}>
        Rozkład Wyników wg Archetypu
      </h3>

      <div style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "12px",
        marginTop: "10px",
        padding: "10px 20px"
      }}>
        {chartData.map((item) => (
          <div
            key={item.key}
            style={{
              display: "flex",
              alignItems: "center",
              fontSize: "11px",
              minWidth: "120px"
            }}
          >
            <div
              style={{
                width: "12px",
                height: "12px",
                backgroundColor: archColorMap[item.key],
                borderRadius: "50%",
                marginRight: "6px"
              }}
            />
            <span style={{ fontWeight: "bold", marginRight: "4px" }}>
              {item.name}
            </span>
            <span style={{ color: "#666" }}>
              ({item.averageResult.toFixed(2)}%)
            </span>
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          margin={{ top: 10, right: 80, left: 20, bottom: 120 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#f0f0f0"
          />

          <XAxis
            dataKey="name"
            interval={0}
            height={80}
            type="category"
            //scale="point" // Zmienia sposób rozkładu punktów na osi
            allowDuplicatedCategory={false}
            // Dodaj to:
            padding={{ left: 50, right: 50 }} 
            tick={
              <CustomTick 
                chartData={chartData} 
                archColorMap={archColorMap} 
              />
            }
          />

          <YAxis
            unit="%"
            label={{
              value: "Wynik (%)",
              angle: -90,
              position: "insideLeft"
            }}
          />

          <ZAxis type="number" range={[50, 400]} />

          <Tooltip
            content={<CustomTooltip />}
            cursor={false}
            shared={false}
          />

          {benchmarkValue !== null && (
            <ReferenceLine
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

          <ReferenceLine y={0} stroke="#000" />

          {/* 🔵 INDYWIDUALNE PUNKTY (BEZ TOOLTIPA) */}
          <Scatter
            data={individualPoints}
            dataKey="value"
            isAnimationActive={false}
            tooltipType="none"
            shape={(props) => {
              const { cx, cy, payload } = props;
              const { index, totalInGroup } = payload;

              const availableWidth = 100;
              let xOffset = 0;

              if (totalInGroup > 1) {
                xOffset = (index / (totalInGroup - 1)) * availableWidth - (availableWidth / 2);
              } else {
                xOffset = 0;
              }

              const xPos = cx + xOffset;

              return (
                <circle
                  cx={xPos}
                  cy={cy}
                  r={3.5}
                  fill={archColorMap[payload.key] || "#8884d8"}
                  fillOpacity={0.3}
                />
              );
            }}
          />

          {/* 🔴 ŚREDNIE */}
          <Scatter data={chartData} dataKey="averageResult">
            <ErrorBar
              dataKey="errorRange"
              width={10}
              strokeWidth={2}
              stroke="#333"
              strokeOpacity={0.4}
            />
            {chartData.map((entry, index) => (
              <Cell
                key={`avg-${index}`}
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



        </ComposedChart>


      </ResponsiveContainer>


    </div>
  );
};

export default ArchetypePerformanceChart;