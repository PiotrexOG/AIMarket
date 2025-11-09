import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceDot,
} from "recharts";
import { formatXAxisTick, getXAxisInterval } from "../PortfolioChart/utils/intervalUtils";
import CustomTooltip from "../PortfolioChart/CustomTooltip";

// 🔺🔻 komponent SVG trójkąta
const TriangleMarker = ({ cx, cy, color, isUp, size }) => {
  console.log("🔼 Rendering TriangleMarker at:", cx, cy);
  
  // Jeśli brak pozycji, nie renderuj
  if (cx == null || cy == null) return null;
  
  const points = isUp
    ? `${cx - size / 2},${cy + size / 2} ${cx + size / 2},${cy + size / 2} ${cx},${cy - size / 2}`
    : `${cx - size / 2},${cy - size / 2} ${cx + size / 2},${cy - size / 2} ${cx},${cy + size / 2}`;
  
  return <polygon points={points} fill={color} opacity={0.8} />;
};

function StockChartView({ dataSets = [], range, disableClicks = false, transactions = [] }) {
  const dataSet = Array.isArray(dataSets) ? dataSets[0] : dataSets;
  const history = dataSet?.data?.history;

  console.log("📊 StockChartView props:", {
    transactions: transactions,
    transactionsCount: transactions?.length,
    history: history,
    historyCount: history?.length,
    dataSet: dataSet
  });

  // Przygotuj dane wykresu
  const chartData = useMemo(() => {
    if (!Array.isArray(history)) return [];
    return history.map((point) => ({
      date: point.date || point.datetime,
      value: point.value,
    }));
  }, [history]);

  // 🔺🔻 Memoizowane punkty transakcji
  const transactionMarkers = useMemo(() => {
    console.log("🔄 Calculating transaction markers...");
    
    if (!transactions?.length || !chartData.length) {
      console.log("❌ No transactions or chart data");
      return [];
    }

    console.log("✅ Processing transactions:", transactions);
    console.log("📈 Chart data for matching:", chartData);
    
    const markers = transactions.map((t, index) => {
      console.log(`📈 Processing transaction ${index}:`, t);

      // Znajdź dokładny punkt w chartData który pasuje do daty transakcji
      const exactMatch = chartData.find(point => 
        point.date === t.datetime || 
        new Date(point.date).getTime() === new Date(t.datetime).getTime()
      );

      // Jeśli nie ma dokładnego dopasowania, znajdź najbliższy
      const matchingPoint = exactMatch || chartData.reduce((prev, curr) => {
        const prevDate = new Date(prev.date);
        const currDate = new Date(curr.date);
        const transactionDate = new Date(t.datetime);
        
        return Math.abs(currDate - transactionDate) < Math.abs(prevDate - transactionDate)
          ? curr
          : prev;
      });

      console.log(`📍 Matching point for transaction ${index}:`, matchingPoint);

      const isPositive = t.ratio > 0;
      const scale = Math.min(Math.abs(t.ratio), 1);
      const size = 8 + scale * 10;
      const color = isPositive ? "green" : "red";

      const marker = {
        x: matchingPoint.date, // UŻYJ TEGO SAMEGO FORMATU CO W chartData!
        y: matchingPoint.value,
        isUp: isPositive,
        color,
        size,
        originalTransaction: t
      };

      console.log(`🎯 Created marker ${index}:`, marker);
      return marker;
    });

    console.log("🎯 Final markers:", markers);
    return markers;
  }, [transactions, chartData]);

  if (!Array.isArray(history) || !chartData.length) {
    console.log("❌ No history data available");
    return <p style={{ textAlign: "center" }}>No data available</p>;
  }

  console.log("📈 Chart data:", chartData);
  console.log("🎯 Transaction markers to render:", transactionMarkers);

  return (
    <ResponsiveContainer width="100%" aspect={2.6}>
      <LineChart
        data={chartData}
        margin={{ top: 20, right: 20, left: 20, bottom: 5 }}
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

        <Line
          type="monotone"
          dataKey="value"
          stroke={dataSet.color || "#4a90e2"}
          strokeWidth={2.5}
          dot={disableClicks ? false : { r: 1.2 }}
          activeDot={disableClicks ? { r: 5 } : { r: 7 }}
          name={dataSet.ticker?.toUpperCase() || "Stock"}
        />

        {/* 🔺🔻 Trójkąty transakcji */}
        {transactionMarkers.map((t, i) => (
          <ReferenceDot
            key={i}
            x={t.x}  // UŻYJ x zamiast date
            y={t.y}  // UŻYJ y zamiast value
            ifOverflow="visible" // ZMIEŃ NA visible ŻEBY ZOBACZYĆ CZY SĄ POZA ZAKRESEM
            isFront
            shape={<TriangleMarker color={t.color} isUp={t.isUp} size={t.size} />}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default StockChartView;