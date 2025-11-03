// src/components/PortfolioChart/ChartView.js
import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import CustomTooltip from "./CustomTooltip";
import { handleChartClick } from "./utils/chartClickUtils";
import { formatXAxisTick, getXAxisInterval } from "./utils/intervalUtils";

function ChartView({ data, range, onPointClick }) {
  return (
    <ResponsiveContainer width="100%" aspect={2.6}>
      <LineChart
        data={data.history}
        margin={{ top: 20, right: 10, left: 20, bottom: 5 }}
        onClick={(e) => handleChartClick(e, data, onPointClick)}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(tick) => formatXAxisTick(tick, range)}
          interval={getXAxisInterval(range)}
        />
        <YAxis domain={["auto", "auto"]} />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="portfolio_value"
          stroke="#4a90e2"
          strokeWidth={3}
          dot={{ r: 1.2, cursor: "pointer" }}
          activeDot={{
            r: 7,
            onClick: (event, payload) =>
              payload?.payload && onPointClick(payload.payload),
          }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default ChartView;
