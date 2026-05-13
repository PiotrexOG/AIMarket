import React, { useMemo } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, 
  Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from "recharts";

const SuccessDistributionChart = ({ data }) => {
  // 1. Wybieramy top 20% wyników
  const analysisData = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.change_ratio - a.change_ratio);
    const topThreshold = sorted[Math.floor(data.length * 0.2)]?.change_ratio;

    return data.map(p => ({
      ...p,
      isTop: p.change_ratio >= topThreshold,
      // Spłaszczamy strukturę dla łatwiejszego dostępu
      tech: p.metric_weights.relative_technical_strength * 100,
      fund: p.metric_weights.relative_fundamental_support * 100,
      result: p.change_ratio * 100
    }));
  }, [data]);

  const paramsToAnalyze = [
    { label: "Technical Weight (%)", key: "tech" },
    { label: "Fundamental Weight (%)", key: "fund" },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', padding: '20px' }}>
      {paramsToAnalyze.map(param => (
        <div key={param.key} style={{ background: '#f9f9f9', padding: '15px', borderRadius: '8px' }}>
          <h4>{param.label} vs Result</h4>
          <div style={{ width: '100%', height: 250 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <XAxis type="number" dataKey={param.key} name={param.label} fontSize={11} />
                <YAxis type="number" dataKey="result" name="Result" unit="%" fontSize={11} />
                <ZAxis type="number" range={[50, 400]} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter data={analysisData}>
                  {analysisData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.isTop ? "#52c41a" : "#d9d9d9"} // Zielony dla TOP 20%
                      fillOpacity={entry.isTop ? 0.8 : 0.3}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <p style={{ fontSize: '10px', color: '#666' }}>Zielone punkty to Top 20% wyników.</p>
        </div>
      ))}
    </div>
  );
};

export default SuccessDistributionChart;