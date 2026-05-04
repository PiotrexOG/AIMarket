import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { startSimulation, resetSimulation } from "../../api/fetchSimulationConfig";
import "./LandingPage.css";

const LandingPage = ({ totalStart, totalEnd }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Formatuje datę do formatu: YYYY-MM-DDTHH:mm (wymagane przez datetime-local)
  const formatForDateTimeLocal = (dateValue) => {
    if (!dateValue) return "";
    const d = new Date(dateValue);
    if (isNaN(d.getTime())) return "";

    // Korekta o strefę czasową, aby ISO zwróciło lokalny czas
    const tzOffset = d.getTimezoneOffset() * 60000;
    const localISOTime = new Date(d.getTime() - tzOffset).toISOString().slice(0, 16);
    return localISOTime;
  };

  const [startDate, setStartDate] = useState(formatForDateTimeLocal(totalStart));
  const [endDate, setEndDate] = useState(formatForDateTimeLocal(totalEnd));
  const [usersPerArchetype, setUsersPerArchetype] = useState(1);
  const [deltaDays, setDeltaDays] = useState(7);

  // Aktualizacja, jeśli propsy przyjdą później (np. z API w App.js)
  useEffect(() => {
    if (totalStart) setStartDate(formatForDateTimeLocal(totalStart));
    if (totalEnd) setEndDate(formatForDateTimeLocal(totalEnd));
  }, [totalStart, totalEnd]);

  const handleStartSimulation = async () => {
    setLoading(true);
    try {
      // Wysyłamy daty bezpośrednio (startSimulation doda Z lub inne formatowanie)
      await startSimulation(startDate, endDate, usersPerArchetype, deltaDays);
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

  return (
    <div className="landing-container">
      <h1>Stock Simulator</h1>
      
      <div className="config-panel">
        <div className="input-group">
          <label>Simulation Start (Date & Time):</label>
          <input 
            type="datetime-local" 
            value={startDate} 
            onChange={(e) => setStartDate(e.target.value)} 
          />
        </div>
        
        <div className="input-group">
          <label>Simulation End (Date & Time):</label>
          <input 
            type="datetime-local" 
            value={endDate} 
            onChange={(e) => setEndDate(e.target.value)} 
          />
        </div>

        <div className="input-group">
          <label>Users per Archetype:</label>
          <input 
            type="number" 
            value={usersPerArchetype} 
            onChange={(e) => setUsersPerArchetype(parseInt(e.target.value) || 1)} 
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
        <button className="btn btn-start" onClick={handleStartSimulation} disabled={loading}>
          {loading ? "Processing..." : "▶ Start Simulation"}
        </button>
        <button className="btn btn-reset" onClick={handleReset} disabled={loading}>
          🔄 Reset
        </button>
      </div>
    </div>
  );
};

export default LandingPage;