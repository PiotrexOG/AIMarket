// src/components/PortfolioChart/utils/fetchUtils.js
export const fetchValuation = async (userId, start, end, interval) => {
  const url = `http://localhost:8000/portfolios/${userId}/valuation?start=${encodeURIComponent(
    start
  )}&end=${encodeURIComponent(end)}&interval=${interval}&detailed=false`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch valuation");
  return response.json();
};
