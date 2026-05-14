const BASE_URL = "http://localhost:8000";

export const fetchSimulationConfig = async () => {
  const url = "http://localhost:8000/simulation/config";

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch simulation config");
  }

  return response.json();
};

export const startSimulation = async (startDate, endDate, usersPerArchetype, deltaDays, archetypes_config, isBatch) => {
  // Ponieważ datetime-local nie ma sekund ani strefy, dodajemy je tutaj:
  const payload = {
    start_time: startDate, 
    end_time: endDate,
    users_per_archetype: usersPerArchetype,
    delta_days: deltaDays,
    archetypes_config: archetypes_config,
    is_batch: isBatch
  };

  const response = await fetch(`${BASE_URL}/simulation/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to start simulation");
  }

  return response.json();
};

// Reset symulacji (POST)
export const resetSimulation = async () => {
  const response = await fetch(`${BASE_URL}/simulation/reset`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to reset simulation");
  }

  return response.json();
};