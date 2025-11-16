import React from "react";
import StockTransactionList from "./StockTransactionList";
import "./StockTransactionPanel.css";

function StockTransactionPanel({ transactions, onClose, selectedUsers = {}, colorPalette = [] }) {
  if (!transactions || transactions.length === 0) return null;

  const grouped = transactions.reduce((acc, tx) => {
    if (!acc[tx.userId]) acc[tx.userId] = [];
    acc[tx.userId].push(tx);
    return acc;
  }, {});

  // 🔹 Posortowane ID użytkowników (numerycznie)
  const sortedUserIds = Object.keys(grouped)
    .map(id => parseInt(id))
    .sort((a, b) => a - b);

  return (
    <div className="stock-panel-wrapper">
      <div className="stock-panel">
        <div className="panel-header">
          <h3>📋 Selected Transactions</h3>
          <button className="close-btn" onClick={onClose}>✖</button>
        </div>

        <div className="users-columns">
          {sortedUserIds.map((userId, idx) => {
            const userTx = grouped[userId];
            const color = colorPalette[idx % colorPalette.length] || "#888888ff";
            const userName = selectedUsers[userId] || `User ${userId}`;

            return (
              <div key={userId} className="user-column" style={{ borderColor: color }}>
                {/* user name header */}
                <div className="user-label" style={{ backgroundColor: color }}>
                  {userName}
                </div>

                {/* header directly under user name */}
                <div className="header-row">
                  <div className="col-date">Date</div>
                  <div className="col-time">Time</div>
                  <div className="col-quantity">Quantity</div>
                  <div className="col-price">Price</div>
                  <div className="col-total">Total Value</div>
                  <div className="col-ratio">Ratio</div>
                </div>

                {/* transactions */}
                <StockTransactionList transactions={userTx} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default StockTransactionPanel;