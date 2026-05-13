import React, { useMemo, useState } from "react";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Legend, Tooltip
} from "recharts";

const ArchetypeRadarAnalysis = ({ data }) => {
  const [selectedArch, setSelectedArch] = useState(
    Object.keys(data[0] || {})[0] || ""
  );

  const paramConfig = [
    { label: "Tech", key: "metric_weights.relative_technical_strength", max: 1 },
    { label: "Fund", key: "metric_weights.relative_fundamental_support", max: 1 },
    { label: "Val", key: "metric_weights.relative_valuation_sustainability", max: 1 },
    { label: "Risk W.", key: "metric_weights.relative_structural_risk", max: 1 },
    { label: "Conv", key: "metric_weights.relative_conviction", max: 1 },
    { label: "Asym", key: "metric_weights.relative_asymmetry_profile", max: 1 },
    { label: "S-Term", key: "short_term_weight", max: 1 },
    { label: "L-Term", key: "long_term_weight", max: 1 },
    { label: "min_exposure", key: "min_exposure", max: 1 },
    { label: "aggression_slope", key: "aggression_slope", max: 1 },
    { label: "exposure_baseline", key: "exposure_baseline", max: 10 },
  ];

  const getValue = (obj, path) =>
    path.split(".").reduce((o, key) => o?.[key], obj);

  const archetypes = [...new Set(data.map(p => p.archetype_key))];

  const radarData = useMemo(() => {
    const archData = data.filter(p => p.archetype_key === selectedArch);
    if (archData.length === 0) return [];

    // sort malejąco po wyniku
    const sorted = [...archData].sort((a, b) => b.change_ratio - a.change_ratio);

    const chunkSize = Math.max(1, Math.floor(sorted.length * 0.3));

    const topPerformers = sorted.slice(0, chunkSize);
    const allPerformers = sorted;

    const result = paramConfig.map(cfg => {
      const avgTop =
        topPerformers.reduce((sum, p) => sum + (getValue(p, cfg.key) || 0), 0) /
        topPerformers.length;

        const avgAll =
        allPerformers.reduce((sum, p) => sum + (getValue(p, cfg.key) || 0), 0) /
        allPerformers.length;

      // 🔥 KLUCZ: względna różnica %
      let relDiff = 0;

      if (avgAll === 0 && avgTop > 0) {
        relDiff = 200;
      } else if (avgAll === 0) {
        relDiff = 0;
      } else {
        relDiff = ((avgTop - avgAll) / avgAll) * 100;
      }

      return {
        subject: cfg.label,
        "Przewaga %": relDiff,
        fullMark: 200, // max skali
      };
    });

    // 🔥 sortuj po sile wpływu (najważniejsze pierwsze)
    return result.sort((a, b) => b["Przewaga %"] - a["Przewaga %"]);

  }, [data, selectedArch]);

  return (
    <div style={{
      width: "100%",
      padding: "20px",
      background: "#fff",
      borderRadius: "12px"
    }}>
      <h3>
        Sygnatura Sukcesu (REL): {selectedArch.replace('_', ' ').toUpperCase()}
      </h3>

      <div style={{ marginBottom: "20px" }}>
        <label>Wybierz archetyp: </label>
        <select
          value={selectedArch}
          onChange={(e) => setSelectedArch(e.target.value)}
        >
          {archetypes.map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <div style={{ width: "100%", height: 450 }}>
        <ResponsiveContainer>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" />

            <PolarRadiusAxis
              angle={30}
              domain={[-50, 50]}
              tickFormatter={(t) => `${t}%`}
            />

            <Radar
              name="Przewaga TOP vs AVG (%)"
              dataKey="Przewaga %"
              stroke="#00b894"
              fill="#00b894"
              fillOpacity={0.6}
            />

            <Tooltip
              formatter={(value) => `${value.toFixed(1)}%`}
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <p style={{
        fontSize: "12px",
        color: "#666",
        fontStyle: "italic"
      }}>
        * Wartości pokazują względną przewagę TOP 30% nad WORST 30%.
        <br />
        Dodatnie = cecha sprzyja wynikom.
        <br />
        Ujemne = cecha szkodzi wynikom.
      </p>
    </div>
  );
};

export default ArchetypeRadarAnalysis;