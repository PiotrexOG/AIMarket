import React, { useMemo } from "react";

// 🔹 Czyści dane (usuwa NaN / null / undefined)
const cleanPairs = (x, y) => {
  const pairs = x.map((xi, i) => [xi, y[i]]);
  return pairs.filter(
    ([xi, yi]) =>
      xi !== null &&
      yi !== null &&
      xi !== undefined &&
      yi !== undefined &&
      !isNaN(xi) &&
      !isNaN(yi)
  );
};

// 🔹 Stabilna korelacja (bez NaN)
const calculateCorrelation = (x, y) => {
  const pairs = cleanPairs(x, y);
  const n = pairs.length;

  if (n < 2) return 0;

  const xs = pairs.map(p => p[0]);
  const ys = pairs.map(p => p[1]);

  const muX = xs.reduce((a, b) => a + b, 0) / n;
  const muY = ys.reduce((a, b) => a + b, 0) / n;

  const varX = xs.reduce((sum, xi) => sum + Math.pow(xi - muX, 2), 0);
  const varY = ys.reduce((sum, yi) => sum + Math.pow(yi - muY, 2), 0);

  // brak wariancji → brak korelacji
  if (varX === 0 || varY === 0) return 0;

  const cov = xs.reduce(
    (sum, xi, i) => sum + (xi - muX) * (ys[i] - muY),
    0
  );

  return cov / Math.sqrt(varX * varY);
};

const ArchetypeCorrelationHeatmap = ({ data }) => {
  const params = [
    { label: "Asym", key: "metric_weights.relative_asymmetry_profile" },
    { label: "Conv", key: "metric_weights.relative_conviction" },
    { label: "Safety W.", key: "metric_weights.relative_structural_safety" },
    { label: "Val", key: "metric_weights.relative_valuation_sustainability" },
    { label: "Fund", key: "metric_weights.relative_fundamental_support" },
    { label: "Tech", key: "metric_weights.relative_technical_strength" },
    { label: "Time S", key: "short_term_weight" },
    { label: "Time M", key: "medium_term_weight" },
    { label: "Time L", key: "long_term_weight" },
    { label: "min_exposure", key: "min_exposure" },
    { label: "aggression_slope", key: "aggression_slope" },
    { label: "exposure_baseline", key: "exposure_baseline" },
    { label: "Rebal", key: "rebalance_threshold" },
    { label: "Softmax", key: "softmax_temp" },
  ];

  // 🔹 Bezpieczne pobieranie wartości (bez || 0)
  const getValue = (obj, path) => {
    const val = path.split(".").reduce((o, key) => o?.[key], obj);
    return val === undefined || val === null ? null : val;
  };

  const archetypes = [...new Set(data.map(p => p.archetype_key))];

  // 🔹 PER ARCHETYPE
  const heatmapData = useMemo(() => {
    return params.map(param => {
      const row = { param: param.label };

      archetypes.forEach(arch => {
        const archData = data.filter(p => p.archetype_key === arch);

        const x = archData.map(p => getValue(p, param.key));
        const y = archData.map(p => p.change_ratio);

        row[arch] = calculateCorrelation(x, y);
      });

      return row;
    });
  }, [data]);

  // 🔹 GLOBAL (ALL)
  const globalHeatmapData = useMemo(() => {
    return params.map(param => {
      const x = data.map(p => getValue(p, param.key));
      const y = data.map(p => p.change_ratio);

      return {
        param: param.label,
        value: calculateCorrelation(x, y),
      };
    });
  }, [data]);

  const getColor = (val) => {
    const alpha = Math.min(Math.abs(val), 1);
    return val > 0
      ? `rgba(0, 200, 0, ${alpha})`
      : `rgba(200, 0, 0, ${alpha})`;
  };

  return (
    <div style={{ padding: "20px", overflowX: "auto" }}>
      
      {/* 🔹 PER ARCHETYPE */}
      <h3>Korelacja Parametrów z Wynikiem per Archetyp</h3>
      <table style={{ borderCollapse: "collapse", fontSize: "12px", width: "100%" }}>
        <thead>
          <tr>
            <th style={thStyle}>Parametr</th>
            {archetypes.map(arch => (
              <th key={arch} style={thStyle}>{arch}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {heatmapData.map(row => (
            <tr key={row.param}>
              <td style={labelStyle}>{row.param}</td>
              {archetypes.map(arch => (
                <td
                  key={arch}
                  style={{
                    ...cellStyle,
                    backgroundColor: getColor(row[arch]),
                    color: Math.abs(row[arch]) > 0.5 ? "white" : "black"
                  }}
                >
                  {row[arch].toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* 🔹 GLOBAL */}
      <h3 style={{ marginTop: "30px" }}>
        Korelacja Globalna (ALL)
      </h3>
      <table style={{ borderCollapse: "collapse", fontSize: "12px", width: "300px" }}>
        <thead>
          <tr>
            <th style={thStyle}>Parametr</th>
            <th style={thStyle}>ALL</th>
          </tr>
        </thead>
        <tbody>
          {globalHeatmapData.map(row => (
            <tr key={row.param}>
              <td style={labelStyle}>{row.param}</td>
              <td
                style={{
                  ...cellStyle,
                  backgroundColor: getColor(row.value),
                  color: Math.abs(row.value) > 0.5 ? "white" : "black"
                }}
              >
                {row.value.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p style={{ fontSize: "11px", color: "#666", marginTop: "10px" }}>
        * 1.0 = silna pozytywna korelacja | -1.0 = silna negatywna
      </p>
    </div>
  );
};

// 🔹 Style
const thStyle = {
  border: "1px solid #ddd",
  padding: "8px",
  background: "#f5f5f5"
};

const cellStyle = {
  border: "1px solid #ddd",
  padding: "8px",
  textAlign: "center"
};

const labelStyle = {
  ...cellStyle,
  fontWeight: "bold"
};

export default ArchetypeCorrelationHeatmap;