export const fetchSimulationConfig = async () => {
  const url = "http://localhost:8000/simulation/config";

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch simulation config");
  }

  return response.json();
};