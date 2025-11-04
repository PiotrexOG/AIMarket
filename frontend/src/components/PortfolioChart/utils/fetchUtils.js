// src/components/PortfolioChart/utils/fetchUtils.js
export const fetchValuation = async (userId, start, end, interval) => {
  const url = `http://localhost:8000/portfolios/${userId}/valuation?start=${encodeURIComponent(
    start
  )}&end=${encodeURIComponent(end)}&interval=${interval}&detailed=false`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch valuation");
  return response.json();
};

// --- 🔹 nowa funkcja do pobierania listy użytkowników ---
export const fetchUsers = async () => {
  const url = "http://localhost:8000/users/";

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch users");
  return response.json();
};
