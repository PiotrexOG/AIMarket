export const fetchPerformanceSummary = async (start, end) => {
    const url = `http://localhost:8000/portfolios/performance-summary?start=${encodeURIComponent(
      start
    )}&end=${encodeURIComponent(end)}`;
  
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch performance summary");
    return response.json();
  };

  export const fetchArchetypes = async () => {
    const response = await fetch("http://localhost:8000/archetypes/");
    if (!response.ok) throw new Error("Failed to fetch archetypes");
    return response.json();
  };