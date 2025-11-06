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

function ChartView({ dataSets = [], range, onPointClick, colorPalette = [], disableClicks = false }) {
  if (!dataSets || dataSets.length === 0 || !Array.isArray(dataSets[0]?.data?.history)) {
    return <p style={{ textAlign: "center" }}>No data available</p>;
  }

  // 🔹 Zbierz wspólne dane (po dacie)
  const mergedData = dataSets[0].data.history.map((point, i) => {
    const date = point.date || point.datetime;
    const mergedPoint = { date };

    dataSets.forEach((set) => {
      const history = set.data?.history;
      if (Array.isArray(history) && history[i]) {
        // obsługa portfolio_value (dla userów) i value (dla akcji)
        const val = history[i].portfolio_value ?? history[i].value;
        mergedPoint[`user_${set.userId ?? set.ticker}`] = val;
      }
    });

    return mergedPoint;
  });

  return (
    <ResponsiveContainer width="100%" aspect={2.6}>
      <LineChart
        data={mergedData}
        margin={{ top: 20, right: 20, left: 20, bottom: 5 }}
        {...(!disableClicks && { onClick: (e) => handleChartClick(e, mergedData, onPointClick) })}
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

        {/* 🔹 Linie użytkowników lub akcji */}
        {dataSets.map((set, idx) => {
          const key = `user_${set.userId ?? set.ticker}`;
          const color = colorPalette[idx % colorPalette.length] || set.color || "#4a90e2";

          return (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              strokeWidth={2.5}
              dot={disableClicks ? false : { r: 1.2, cursor: "pointer" }}
              activeDot={
                disableClicks
                  ? { r: 5 }
                  : {
                      r: 7,
                      onClick: (event, payload) =>
                        payload?.payload && onPointClick(payload.payload),
                    }
              }
              name={set.userId ? `User ${set.userId}` : set.ticker?.toUpperCase()}
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default ChartView;
