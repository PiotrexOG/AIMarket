import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { startSimulation, resetSimulation } from "../../api/fetchSimulationConfig";
import "./LandingPage.css";

const LandingPage = ({ totalStart, totalEnd }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // 🔹 Pomocnicza funkcja: formatuje obiekt Date do stringa "YYYY-MM-DDTHH:mm" (ucinając strefę)
  const formatAsUTCForInput = (dateValue) => {
    if (!dateValue) return "";
    const d = new Date(dateValue);
    if (isNaN(d.getTime())) return "";
    
    // ISO string to "YYYY-MM-DDTHH:mm:ss.sssZ" -> wycinamy do minut
    return d.toISOString().substring(0, 16);
  };

  // 🔹 Konwersja: traktujemy tekst z inputa jako UTC i wysyłamy do API
  const toUTCISOString = (localValue) => {
    if (!localValue) return null;
    // Doklejamy "Z", żeby JS wiedział, że to co wpisaliśmy to JUŻ jest UTC
    return new Date(`${localValue}:00Z`).toISOString();
  };

  const [startDate, setStartDate] = useState(formatAsUTCForInput(totalStart));
  const [endDate, setEndDate] = useState(formatAsUTCForInput(totalEnd));
  const [usersPerArchetype, setUsersPerArchetype] = useState(1);
  const [deltaDays, setDeltaDays] = useState(7);

  useEffect(() => {
    if (totalStart) setStartDate(formatAsUTCForInput(totalStart));
    if (totalEnd) setEndDate(formatAsUTCForInput(totalEnd));
  }, [totalStart, totalEnd]);

  const handleStartSimulation = async () => {
    setLoading(true);
    console.log(toUTCISOString(startDate))
    try {
      await startSimulation(
        toUTCISOString(startDate),
        toUTCISOString(endDate),
        usersPerArchetype,
        deltaDays
      );
      navigate("/dashboard");
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

    const handleReset = async () => {
    if (!window.confirm("Are you sure?")) return;
    setLoading(true);
    try {
      await resetSimulation();
      alert("Simulation reset successful");
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 🔥 UTC "Wczoraj" - teraz bez żadnych przesunięć lokalnych
  const setYesterdayStart = () => {
    const yesterday = new Date();
    yesterday.setUTCDate(yesterday.getUTCDate() - 1);

    const startStr = `${yesterday.toISOString().split('T')[0]}T13:30`;

    setStartDate(startStr);
  };

  const setYesterdayEnd = () => {
    const yesterday = new Date();
    yesterday.setUTCDate(yesterday.getUTCDate() - 1);

    const endStr = `${yesterday.toISOString().split('T')[0]}T20:30`;

    setEndDate(endStr);
  };

// Pomocnicza funkcja generująca string "wczoraj + godzina"
  const getYesterdayString = (timeStr) => {
    const yesterday = new Date();
    yesterday.setUTCDate(yesterday.getUTCDate() - 1);
    return `${yesterday.toISOString().split('T')[0]}T${timeStr}`;
  };

  const toggleStart = () => {
    const yesterdayStart = getYesterdayString("13:30");
    // Jeśli aktualnie jest "wczoraj", wróć do default, w przeciwnym razie ustaw "wczoraj"
    if (startDate === yesterdayStart) {
      setStartDate(formatAsUTCForInput(totalStart));
    } else {
      setStartDate(yesterdayStart);
    }
  };

  const toggleEnd = () => {
    const yesterdayEnd = getYesterdayString("20:30");
    if (endDate === yesterdayEnd) {
      setEndDate(formatAsUTCForInput(totalEnd));
    } else {
      setEndDate(yesterdayEnd);
    }
  };

  return (
    <div className="landing-container">
      <h1>Stock Simulator (Mode)</h1>

      <div className="config-panel">
        <div className="input-group">
        <label>Simulation Start:</label>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="datetime-local"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <button type="button" onClick={toggleStart} style={{ minWidth: '80px' }}>
            {startDate === getYesterdayString("13:30") ? "Default" : "Yesterday"}
          </button>
        </div>
      </div>

      <div className="input-group">
        <label>Simulation End:</label>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="datetime-local"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
          <button type="button" onClick={toggleEnd} style={{ minWidth: '80px' }}>
            {endDate === getYesterdayString("20:30") ? "Default" : "Yesterday"}
          </button>
        </div>
      </div>

        <div className="input-group">
          <label>Users per Archetype:</label>
          <input
            type="number"
            value={usersPerArchetype}
            onChange={(e) =>
              setUsersPerArchetype(parseInt(e.target.value) || 1)
            }
          />
        </div>

        <div className="input-group">
          <label>Delta Days:</label>
          <input
            type="number"
            value={deltaDays}
            onChange={(e) => setDeltaDays(parseInt(e.target.value) || 1)}
          />
        </div>
      </div>

      <div className="actions">
        <button
          className="btn btn-start"
          onClick={handleStartSimulation}
          disabled={loading}
        >
          {loading ? "Processing..." : "▶ Start Simulation"}
        </button>

        <button
          className="btn btn-reset"
          onClick={handleReset}
          disabled={loading}
        >
          🔄 Reset
        </button>
      </div>
    </div>
  );
};

export default LandingPage;