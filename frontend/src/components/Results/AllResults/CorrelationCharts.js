import React, { useEffect, useMemo, useState } from "react";
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
  ZAxis
} from "recharts";

const CorrelationCharts = ({ data, archetypes = [], archColorMap }) => {
  const [selectedRebalanceArchetypes, setSelectedRebalanceArchetypes] = useState([]);

  const benchmarkValue = useMemo(() => {
    const benchmarkPortfolios = data.filter(p => p.archetype_key === "benchmark");
    if (benchmarkPortfolios.length === 0) return null;
    const avgChangeRatio = benchmarkPortfolios.reduce((sum, p) => sum + p.change_ratio, 0) / benchmarkPortfolios.length;
    return avgChangeRatio * 100;
  }, [data]);

  // Zaktualizowana lista metryk - tylko wymagane pola
  const metrics = [
    { label: "Top M Share", key: "top_m_share" },
    { label: "Investment Time (Days)", key: "investment_time_days" },
    { label: "Rebalance Time Share", key: "rebalance_time_share" },
  ];

  const rebalanceArchetypeOptions = useMemo(() => {
    const archetypeNameByKey = new Map(archetypes.map((arch) => [arch.key, arch.name || arch.key]));
    const uniqueKeys = [...new Set(data.map((p) => p.archetype_key).filter(Boolean))].sort();

    return uniqueKeys.map((key) => ({
      key,
      name: archetypeNameByKey.get(key) || key,
      color: archColorMap[key] || "#8884d8"
    }));
  }, [data, archetypes, archColorMap]);

  const rebalanceArchetypeKeys = useMemo(
    () => rebalanceArchetypeOptions.map((option) => option.key),
    [rebalanceArchetypeOptions]
  );

  useEffect(() => {
    setSelectedRebalanceArchetypes((prev) => {
      const availableKeys = new Set(rebalanceArchetypeKeys);
      const validPrev = prev.filter((key) => availableKeys.has(key));

      if (validPrev.length > 0) return validPrev;
      return rebalanceArchetypeKeys;
    });
  }, [rebalanceArchetypeKeys]);

  const toggleRebalanceArchetype = (key) => {
    setSelectedRebalanceArchetypes((prev) =>
      prev.includes(key)
        ? prev.filter((selectedKey) => selectedKey !== key)
        : [...prev, key]
    );
  };

  const getValue = (obj, path) => path.split(".").reduce((o, key) => o?.[key], obj);

  const toFiniteNumber = (value) => {
    const numericValue = Number(value);
    return Number.isFinite(numericValue) ? numericValue : null;
  };

  const formatAxisTick = (value) => {
    const absValue = Math.abs(value);
    if (absValue >= 100) return value.toFixed(0);
    if (absValue >= 10) return value.toFixed(1);
    if (absValue >= 1) return value.toFixed(2);
    return value.toFixed(3);
  };

  const buildAxisTicks = (chartData, tickCount = 12) => {
    if (!chartData || chartData.length === 0) return [];

    const xs = chartData.map((point) => point.x);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);

    if (minX === maxX) return [minX];

    const step = (maxX - minX) / (tickCount - 1);
    return Array.from({ length: tickCount }, (_, index) => minX + step * index);
  };

  const calculateCorrelation = (chartData) => {
    if (!chartData || chartData.length < 2) return null;

    const meanX = chartData.reduce((sum, point) => sum + point.x, 0) / chartData.length;
    const meanY = chartData.reduce((sum, point) => sum + point.y, 0) / chartData.length;

    const { covariance, varianceX, varianceY } = chartData.reduce(
      (acc, point) => {
        const diffX = point.x - meanX;
        const diffY = point.y - meanY;
        return {
          covariance: acc.covariance + diffX * diffY,
          varianceX: acc.varianceX + diffX * diffX,
          varianceY: acc.varianceY + diffY * diffY
        };
      },
      { covariance: 0, varianceX: 0, varianceY: 0 }
    );

    if (varianceX === 0 || varianceY === 0) return null;
    return covariance / Math.sqrt(varianceX * varianceY);
  };

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
      let bucketIdx = Math.floor(((p.x - minX) / range) * numBuckets);
      if (bucketIdx >= numBuckets) bucketIdx = numBuckets - 1;

      buckets[bucketIdx].sumY += p.y;
      buckets[bucketIdx].count += 1;
    });

    return buckets
      .map((b, i) => {
        if (b.count === 0) return null;
        return {
          x: minX + (i + 0.5) * (range / numBuckets),
          y: b.sumY / b.count
        };
      })
      .filter(b => b !== null);
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const p = payload[0].payload;
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
    <div
      className="correlation-grid"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        width: "100%",
        background: "#fff",
        borderRadius: "8px",
        border: "1px solid #eee",
        padding: "16px",
        boxSizing: "border-box",
      }}
    >
      {metrics.map((m, index) => {
        const isRebalanceMetric = m.key === "rebalance_time_share";
        const selectedRebalanceKeySet = new Set(selectedRebalanceArchetypes);
        const visibleData = isRebalanceMetric
          ? data.filter((p) => selectedRebalanceKeySet.has(p.archetype_key))
          : data;

        const chartData = visibleData
          .map((p) => {
            const x = toFiniteNumber(getValue(p, m.key));
            const changeRatio = toFiniteNumber(p.change_ratio);

            if (x === null || changeRatio === null) return null;

            return {
              x,
              y: changeRatio * 100,
              name: p.name,
              archetype_key: p.archetype_key,
              change_ratio: changeRatio
            };
          })
          .filter(Boolean);

        const trendData = calculateTrendLine(chartData, 25);
        const correlation = calculateCorrelation(chartData);
        const xTicks = buildAxisTicks(chartData, 12);
        const xDomain = chartData.length > 0 ? ["dataMin", "dataMax"] : [0, 1];

        return (
          <div
            key={m.label}
            className="chart-container"
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              borderTop: index === 0 ? "none" : "1px solid #eee",
              borderRadius: 0,
              padding: index === 0 ? "0" : "16px 0 0",
              boxSizing: "border-box",
              boxShadow: "none",
            }}
          >
            <h3 style={{ textAlign: "center", marginBottom: "12px", lineHeight: 1.35 }}>
              {m.label} vs Result (%)
              <span style={{ display: "block", fontSize: "12px", fontWeight: 500, color: "#666" }}>
                Korelacja: {correlation === null ? "n/a" : correlation.toFixed(3)}
              </span>
            </h3>
            {isRebalanceMetric && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  justifyContent: "center",
                  gap: "8px",
                  marginBottom: "14px"
                }}
              >
                <button
                  type="button"
                  onClick={() => setSelectedRebalanceArchetypes(rebalanceArchetypeKeys)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "4px",
                    border: "1px solid #ccc",
                    background: "#fff",
                    color: "#333",
                    cursor: "pointer",
                    fontWeight: "bold",
                    fontSize: "12px"
                  }}
                >
                  Wszystkie
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRebalanceArchetypes([])}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "4px",
                    border: "1px solid #ccc",
                    background: "#f5f5f5",
                    color: "#666",
                    cursor: "pointer",
                    fontWeight: "bold",
                    fontSize: "12px"
                  }}
                >
                  Wyczyść
                </button>
                {rebalanceArchetypeOptions.map((option) => {
                  const isSelected = selectedRebalanceKeySet.has(option.key);

                  return (
                    <button
                      key={option.key}
                      type="button"
                      onClick={() => toggleRebalanceArchetype(option.key)}
                      style={{
                        padding: "6px 12px",
                        borderRadius: "4px",
                        border: isSelected ? `2px solid ${option.color}` : "1px solid #ccc",
                        background: isSelected ? "#f8f9fa" : "#fff",
                        color: isSelected ? "#222" : "#777",
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        fontWeight: isSelected ? "bold" : 500,
                        fontSize: "12px"
                      }}
                    >
                      <span
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          background: option.color,
                          display: "inline-block"
                        }}
                      />
                      {option.name}
                    </button>
                  );
                })}
              </div>
            )}
            <div style={{ width: "100%", height: 350 }}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    domain={xDomain}
                    ticks={xTicks}
                    fontSize={10}
                    tick={{ fill: '#666' }}
                    tickFormatter={formatAxisTick}
                  />
                  <YAxis type="number" dataKey="y" unit="%" fontSize={10} tick={{ fill: '#666' }} />
                  <ZAxis range={[50, 50]} />
                  <Tooltip content={<CustomTooltip />} />

                  {benchmarkValue !== null && (
                    <ReferenceLine y={benchmarkValue} stroke="#ff4d4f" strokeDasharray="5 5" />
                  )}

                  {/* GŁÓWNE PUNKTY */}
                  <Scatter
                    data={chartData}
                    fillOpacity={0.4}
                  >
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={archColorMap[entry.archetype_key] || "#8884d8"}
                      />
                    ))}
                  </Scatter>

                  {/* LINIA TRENDU */}
                  <Scatter
                    data={trendData}
                    line={{ stroke: '#ff4d4f', strokeWidth: 3 }}
                    shape={() => null}
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
