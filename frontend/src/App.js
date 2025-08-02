import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Uwaga: Używamy nazwy usługi z docker-compose ("backend") zamiast "localhost"
        const response = await fetch('http://localhost:8000/users/user2');
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setUserData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Errfghor: {error}</div>;

  return (
    <div className="App">
      <h1>Investment Portfolio</h1>
      {userData && (
        <div>
          <h2>User: {userData.user_id}</h2>
          <p>Cash: ${userData.cash.toFixed(2)}</p>
          <p>Portfolio Value: ${userData.portfolio_value.toFixed(2)}</p>
          
          <h3>Positions:</h3>
          <ul>
            {userData.positions.map((position, index) => (
              <li key={index}>
                {position.ticker}: {position.shares} shares (${position.price.toFixed(2)} each) - ${position.value.toFixed(2)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;