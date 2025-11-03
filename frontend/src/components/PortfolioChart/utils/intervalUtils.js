// src/components/PortfolioChart/utils/intervalUtils.js
import { clampDate } from "./dateUtils";

export const getRangeDates = (range, totalStart, totalEnd) => {
  const end = totalEnd;
  let start = new Date(end);

  switch (range) {
    case "1D": start.setDate(end.getDate() - 1); break;
    case "1W": start.setDate(end.getDate() - 7); break;
    case "1M": start.setMonth(end.getMonth() - 1); break;
    case "3M": start.setMonth(end.getMonth() - 3); break;
    case "6M": start.setMonth(end.getMonth() - 6); break;
    case "YTD": start.setFullYear(end.getFullYear(), 0, 1); break;
    case "1Y": start.setFullYear(end.getFullYear() - 1); break;
  }

  start = clampDate(start, totalStart, totalEnd);
  return { start: start.toISOString(), end: end.toISOString() };
};

export const getIntervalForRange = (range) => {
  switch (range) {
    case "1D": return "30m";
    case "1W": return "1h";
    case "1M": return "4h";
    case "3M":
    case "6M": return "1d";
    case "YTD":
    case "1Y": return "1w";
    default: return "1h";
  }
};

export const formatXAxisTick = (tick, range) => {
  const date = new Date(tick);
  switch (range) {
    case "1D":
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    default:
      const month = (date.getMonth() + 1).toString().padStart(2, "0");
      const day = date.getDate().toString().padStart(2, "0");
      return `${month}.${day}`;
  }
};

export const getXAxisInterval = (range) => {
  switch (range) {
    case "1D": return "preserveStartEnd";
    case "1W": return 23;
    case "1M": return 11;
    case "3M": return 3;
    case "6M": return 6;
    case "YTD":
    case "1Y": return "preserveStartEnd";
    default: return "preserveStartEnd";
  }
};
