// src/components/PortfolioChart/utils/dateUtils.js
export const clampDate = (date, min, max) =>
  new Date(Math.min(Math.max(date.getTime(), min.getTime()), max.getTime()));
