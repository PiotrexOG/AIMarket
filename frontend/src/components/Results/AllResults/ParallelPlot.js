import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// --- WSPÓLNE METRYKI ---
const METRIC_CONFIG = [
  { label: "Asymmetry", key: "metric_weights.relative_asymmetry_profile" },
  { label: "Conviction", key: "metric_weights.relative_conviction" },
  { label: "Structural Safety", key: "metric_weights.relative_structural_safety" },
  { label: "Valuation", key: "metric_weights.relative_valuation_sustainability" },
  { label: "Fundamental", key: "metric_weights.relative_fundamental_support" },
  { label: "Technical", key: "metric_weights.relative_technical_strength" },
  { label: "RESULT", key: "change_ratio" }, // Dodajemy wynik jako ostatni punkt linii
];

const getValue = (obj, path) =>
  path.split(".").reduce((o, key) => o?.[key], obj);

/**
 * POMOCNICZA FUNKCJA DO TRANSFORMACJI DANYCH POD PARALLEL PLOT
 * Recharts potrzebuje danych w formacie:
 * [
 *   { name: 'Asymmetry', portfolio1: 10, portfolio2: 20 },
 *   { name: 'Conviction', portfolio1: 5, portfolio2: 15 },
 * ]
 */
const prepareParallelData = (dataItems, nameKey) => {
  return METRIC_CONFIG.map((m) => {
    const point = { name: m.label };
    dataItems.forEach((item) => {
      let val = getValue(item, m.key);
      // Jeśli to wynik (change_ratio), zamień na procenty, jeśli wagi, też na 100
      point[item[nameKey]] = val * 100;
    });
    return point;
  });
};

// --- 1. WYKRES DLA WSZYSTKICH PORTFELI (COMPOSITION) ---
export const PortfolioParallelPlot = ({ data, archColorMap }) => {
  const chartData = useMemo(() => prepareParallelData(data, "name"), [data]);
  const portfolioNames = data.map((p) => ({ name: p.name, arch: p.archetype_key }));

  return (
    <div style={{ width: "100%", height: 500, padding: "20px" }}>
      <h3>Portfolio Parallel Coordinates (Individual)</h3>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="name" interval={0} fontSize={12} fontWeight="bold" />
          <YAxis unit="%" domain={[0, 'auto']} />
          <Tooltip />
          {portfolioNames.map((p) => (
            <Line
              key={p.name}
              type="monotone"
              dataKey={p.name}
              stroke={archColorMap[p.arch] || "#8884d8"}
              strokeWidth={1}
              dot={{ r: 3 }}
              activeDot={{ r: 6 }}
              connectNulls
              opacity={0.6}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// --- 2. WYKRES DLA ŚREDNICH Z ARCHETYPÓW ---
export const ArchetypeParallelPlot = ({ data, archColorMap }) => {
  const aggregatedData = useMemo(() => {
    // Grupowanie
    const groups = data.reduce((acc, curr) => {
      const key = curr.archetype_key || "unknown";
      if (!acc[key]) acc[key] = { archetype_key: key, count: 0, sums: {} };
      acc[key].count += 1;
      METRIC_CONFIG.forEach(m => {
        acc[key].sums[m.key] = (acc[key].sums[m.key] || 0) + getValue(curr, m.key);
      });
      return acc;
    }, {});

    // Średnie
    return Object.values(groups).map(g => {
      const result = { archetype_key: g.archetype_key };
      METRIC_CONFIG.forEach(m => {
        result[m.key] = g.sums[m.key] / g.count;
      });
      return result;
    });
  }, [data]);

  // Transformacja pod format Recharts (kluczem w liniach jest teraz archetype_key)
  const chartData = useMemo(() => prepareParallelData(aggregatedData, "archetype_key"), [aggregatedData]);
  const archetypeKeys = aggregatedData.map(g => g.archetype_key);

  return (
    <div style={{ width: "100%", height: 500, padding: "20px" }}>
      <h3>Archetype Average "Signatures" (Parallel Plot)</h3>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" interval={0} fontSize={12} fontWeight="bold" />
          <YAxis unit="%" domain={[0, 'auto']} />
          <Tooltip />
          <Legend />
          {archetypeKeys.map((key) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={archColorMap[key] || "#8884d8"}
              strokeWidth={4} // Grubsza linia dla średnich
              dot={{ r: 5 }}
              activeDot={{ r: 8 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};