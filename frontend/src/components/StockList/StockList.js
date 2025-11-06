// src/components/StockList/StockList.js
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchTickers } from "../StockChart/utils/fetchUtils";
import "./StockList.css";

function StockList() {
  const [tickers, setTickers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTickers = async () => {
      try {
        const data = await fetchTickers();
        setTickers(data.tickers || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadTickers();
  }, []);

  if (loading) return <p className="loading-text">Loading tickers...</p>;
  if (error) return <p className="error-text">Error: {error}</p>;

  return (
    <div className="stock-list-container">
      <h2 className="stock-list-title">📊 Available Stocks</h2>
      <div className="stock-grid">
        {tickers.map((ticker) => (
          <Link
            key={ticker}
            to={`/stocks/${ticker}`}
            className="stock-card"
          >
            {ticker}
          </Link>
        ))}
      </div>
    </div>
  );
}

export default StockList;
