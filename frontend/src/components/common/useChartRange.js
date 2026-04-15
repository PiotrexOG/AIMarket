import { useState, useEffect } from "react";
import { getRangeDates, getIntervalForRange } from "../PortfolioChart/utils/intervalUtils";

/**
 * Hook do zarządzania zakresem wykresu (1D, 1W, 1M, Custom)
 * Używany zarówno w PortfolioChart, jak i StockChart.
 */
export function useChartRange(totalStart, totalEnd, onRangeChange) {
  const [range, setRange] = useState("All");
  const [customRange, setCustomRange] = useState("1w");

  // 🔄 Ustawienie nowego zakresu (np. "1W", "6M")
  const handleRangeChange = (newRange) => {
    setRange(newRange);
  };

  // 📅 Obsługa Customgo zakresu (z kalendarza)
  const handleCustomRangeChange = (customValues) => {
    setCustomRange(customValues);
    setRange("Custom");
  };

  // 📦 Zwraca faktyczny zakres (start, end, interval)
  const getEffectiveRange = () => {
    if (range === "Custom" && customRange) {
      return {
        start: customRange.start,
        end: customRange.end,
        interval: customRange.interval,
      };
    } else {
      const { start, end } = getRangeDates(range, totalStart, totalEnd);
      const interval = getIntervalForRange(range);
      return { start, end, interval };
    }
  };

  // 🔔 Jeśli ktoś chce reagować globalnie na zmianę zakresu
  useEffect(() => {
    if (onRangeChange) {
      onRangeChange(range, customRange);
    }
  }, [range, customRange]);

  return {
    range,
    customRange,
    handleRangeChange,
    handleCustomRangeChange,
    getEffectiveRange,
  };
}
