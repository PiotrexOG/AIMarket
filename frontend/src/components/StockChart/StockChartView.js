import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
} from "recharts";
import { formatXAxisTick, getXAxisInterval } from "../PortfolioChart/utils/intervalUtils";
import { groupTransactionsByNearestPoint } from "./utils/markerUtils";
import CustomTooltip from "../PortfolioChart/CustomTooltip";


export const handleChartClick = (e, chartData, transactionMarkers, onPointClick) => {
  if (!e) return;

  if (e.activeLabel && chartData) {
    const foundPoint = chartData.find((d) => d.date === e.activeLabel);
    if (!foundPoint) return;

    // 🟣 Pobierz wszystkie markery z tego dnia
    const markersOfDay = transactionMarkers.filter(
      (m) => m.x === foundPoint.date
    );

    if (markersOfDay.length > 0) {
      // 🟢 Zbierz wszystkie transakcje ze wszystkich userów
      const mergedTransactions = markersOfDay.flatMap(
        (marker) =>
          marker.originalTransactions.map((t) => ({
            ...t,
            userId: marker.userId,
            color: marker.color,
          }))
      );

      onPointClick?.(mergedTransactions);
    } else {
      onPointClick?.([]);
    }
  }
};

// 🔺🔻 komponent SVG trójkąta
const TriangleMarker = ({ cx, cy, color, isUp, size }) => {
  if (cx == null || cy == null) return null;
  
  const points = isUp
    ? `${cx - size / 2},${cy + size / 2} ${cx + size / 2},${cy + size / 2} ${cx},${cy - size / 2}`
    : `${cx - size / 2},${cy - size / 2} ${cx + size / 2},${cy - size / 2} ${cx},${cy + size / 2}`;
  
  const strokeColor = isUp ? "#00FF00" : "#FF0000"; // zielony dla góry, czerwony dla dołu
  
  return (
    <polygon points={points} fill={color} stroke={strokeColor} strokeWidth="0.5" />
  );
};

function StockChartView({ dataSets = [], range, transactionsByUser = [], onMarkerClick }) {
  const dataSet = Array.isArray(dataSets) ? dataSets[0] : dataSets;
  const history = dataSet?.data?.history;
  
  const chartData = useMemo(() => {
    if (!Array.isArray(history)) return [];
    return history.map((point) => ({
      date: point.date || point.datetime,
      value: point.value,
    }));
  }, [history]);

  // 🔹 Grupowanie transakcji wszystkich userów
  const transactionMarkers = useMemo(() => {
    if (!transactionsByUser?.length || !chartData.length) return [];

          console.log(transactionsByUser)
    
    return transactionsByUser.flatMap((userData) => {
      const grouped = groupTransactionsByNearestPoint(userData.transactions, chartData);
      return grouped.map((m) => ({
        ...m,
        color: userData.color,
        userId: userData.userId,
      }));
    });
  }, [transactionsByUser, chartData]);

  if (!chartData.length) {
    return <p style={{ textAlign: "center" }}>No data available</p>;
  }

  return (
    <ResponsiveContainer width="100%" aspect={2.6}>
      <LineChart
        data={chartData}
        margin={{ top: 20, right: 20, left: 20, bottom: 5 }}
        onClick={(e) => handleChartClick(e, chartData, transactionMarkers, onMarkerClick)}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(tick) => formatXAxisTick(tick, range)}
          interval={getXAxisInterval(range)}
        />
        <YAxis
          domain={["auto", "auto"]}
          padding={{ top: 30, bottom: 30 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          stroke={dataSet.color || "#4a90e2"}
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 7 }}
          name={dataSet.ticker?.toUpperCase() || "Stock"}
        />
        {/* 🔺🔻 Markery transakcji */}
        {transactionMarkers.map((t, i) => (
          <ReferenceDot
            key={i}
            x={t.x}
            y={t.y}
            ifOverflow="visible"
            isFront
            shape={<TriangleMarker color={t.color} isUp={t.isUp} size={t.size} />}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default StockChartView;