import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { handleChartClick } from "./utils/chartClickUtils";
import { formatXAxisTick, getXAxisInterval } from "./utils/intervalUtils";
import CustomTooltip from "./CustomTooltip";

function PortfolioChartView({ dataSets = [], range, onPointClick, colorPalette = [] }) {
  if (!dataSets || dataSets.length === 0 || !Array.isArray(dataSets[0]?.data?.history)) {
    return <p style={{ textAlign: "center" }}>No data available</p>;
  }

  // 🔹 Łączenie danych po dacie
  const mergedData = dataSets[0].data.history.map((point, i) => {
    const date = point.date || point.datetime;
    const mergedPoint = { date };

    dataSets.forEach((set) => {
      const history = set.data?.history;
      if (Array.isArray(history) && history[i]) {
        mergedPoint[`user_${set.userId}`] = history[i].portfolio_value;
      }
    });

    return mergedPoint;
  });

  return (
    <ResponsiveContainer width="100%" aspect={2.6}>
      <LineChart
        data={mergedData}
        margin={{ top: 20, right: 20, left: 20, bottom: 5 }}
        onClick={(e) => handleChartClick(e, mergedData, onPointClick)}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(tick) => formatXAxisTick(tick, range)}
          interval={getXAxisInterval(range)}
        />
        <YAxis domain={["auto", "auto"]} padding={{ top: 30, bottom: 30 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />

        {dataSets.map((set, idx) => {
          const key = `user_${set.userId}`;
          const color = colorPalette[idx % colorPalette.length] || set.color || "#4a90e2";

          return (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              strokeWidth={2.5}
              dot={{ r: 1.2, cursor: "pointer" }}
              activeDot={{
                r: 7,
                onClick: (event, payload) => payload?.payload && onPointClick(payload.payload),
              }}
              name={`User ${set.userId}`}
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default PortfolioChartView;
