// PortfolioPieChart.js

import React, { useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

/* =========================================
   🎨 STAŁE KOLORY
========================================= */

const TICKER_COLORS = {
  AAPL: "#3b82f6",
  NVDA: "#10b981",
  MSFT: "#f59e0b",
  JPM: "#ef4444",
  XOM: "#8b5cf6",
  JNJ: "#06b6d4",
  BA: "#ec4899",
  COST: "#84cc16",
  TSM: "#f97316",
  NKE: "#14b8a6",
  V: "#6366f1",
  DIS: "#eab308",
  NFLX: "#dc2626",
  PFE: "#0ea5e9",
  WMT: "#9333ea",
  CVX: "#65a30d",
  GE: "#fb7185",
  SBUX: "#78716c",

  /* 🔽 specjalne grupy */
  Other: "#c084fc",
  Cash: "#9ca3af",
};

function PortfolioPieChart({ positions, portfolioValue, cash }) {
  const pieData = useMemo(() => {
    if (!positions || positions.length === 0) return [];

    let otherValue = 0;

    const grouped = positions
      .filter((p) => {
        const percentage = p.value_of_portfolio * 100;

        if (percentage < 3) {
          otherValue += p.value;
          return false;
        }

        return true;
      })

      .sort((a, b) => b.value - a.value)

      .map((p) => ({
        name: p.ticker,
        value: p.value,
      }));

    /* 🔽 small positions */
    if (otherValue > 0) {
      grouped.push({
        name: "Other",
        value: otherValue,
      });
    }

    /* 🔽 niezainwestowana gotówka */
    if (cash > 0) {
      grouped.push({
        name: "Cash",
        value: cash,
      });
    }

    return grouped;
  }, [positions, portfolioValue, cash]);

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            outerRadius={70}
            innerRadius={28}
            label={false}
            paddingAngle={2}
          >
            {pieData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  TICKER_COLORS[entry.name] || "#d1d5db"
                }
              />
            ))}
          </Pie>

          <Tooltip
            formatter={(value) => [
              `$${value.toFixed(2)}`,
              "Value",
            ]}
          />

          <Legend
            layout="horizontal"
            verticalAlign="bottom"
            align="center"
            payload={pieData.map((item) => ({
              value: item.name,
              type: "square",
              color:
                TICKER_COLORS[item.name] || "#d1d5db",
            }))}
            wrapperStyle={{
              fontSize: "12px",
              paddingTop: "10px",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PortfolioPieChart;