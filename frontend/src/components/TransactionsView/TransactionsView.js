import React, { useEffect, useState } from "react";
import "./TransactionsView.css";

function TransactionsView({ selectedUsers, colorPalette }) {
  const [transactions, setTransactions] = useState([]);
  const [groupedData, setGroupedData] = useState({});

  // 🔹 Pobierz transakcje
  useEffect(() => {
    const selectedUserIds = Object.keys(selectedUsers);
    
    if (selectedUserIds.length === 0) {
      setTransactions([]);
      return;
    }

    const fetchAll = async () => {
      const all = [];

      for (const userId of selectedUserIds) {
        try {
          // 1️⃣ Transakcje
          const txRes = await fetch(`http://localhost:8000/portfolios/${userId}/transactions`);
          const txData = await txRes.json();
          all.push({ 
            userId: parseInt(userId), 
            userName: selectedUsers[userId],
            transactions: txData 
          });
        } catch (err) {
          console.error("Fetch error:", err);
        }
      }

      setTransactions(all);
    };

    fetchAll();
  }, [selectedUsers]);

  // 🔹 Grupowanie po miesiącu → dniu → użytkowniku
  useEffect(() => {
    const grouped = {};

    transactions.forEach(({ userId, transactions: userTxs }) => {
      userTxs.forEach((tx) => {
        const dt = new Date(tx.datetime);
        const monthKey = dt.toLocaleString("en-US", { month: "long", year: "numeric" });
        const dateKey = dt.toISOString().split("T")[0];
        const timeKey = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        if (!grouped[monthKey]) grouped[monthKey] = {};
        if (!grouped[monthKey][dateKey]) grouped[monthKey][dateKey] = {};
        if (!grouped[monthKey][dateKey][userId]) grouped[monthKey][dateKey][userId] = [];

        grouped[monthKey][dateKey][userId].push({
          ...tx,
          time: timeKey,
        });
      });
    });

    setGroupedData(grouped);
  }, [transactions]);

  // 🔹 Posortowane ID użytkowników (numerycznie)
  const sortedUserIds = Object.keys(selectedUsers)
    .map(id => parseInt(id))
    .sort((a, b) => a - b);

  return (
    <div className="transactions-view">
      <h2>💹 Transactions History</h2>

      {Object.keys(groupedData).length === 0 ? (
        <p className="empty-info">Select at least one user to view transactions.</p>
      ) : (
        Object.entries(groupedData).map(([month, days]) => (
          <div key={month} className="month-group">
            <h3 className="month-header">{month}</h3>

            {Object.entries(days).map(([date, users]) => (
              <div key={date} className="date-group">
                <h4 className="date-header">{date}</h4>

                <div className="user-columns">
                  {sortedUserIds.map((userId, idx) => {
                    const color = colorPalette[idx % colorPalette.length];
                    const userTxs = users[userId] || [];
                    const userName = selectedUsers[userId] || `User ${userId}`;

                    return (
                      <div
                        key={userId}
                        className="user-column"
                        style={{ borderColor: color }}
                      >
                        <div className="user-name" style={{ backgroundColor: color, color: "#fff" }}>
                          {userName}
                        </div>

                        {/* 🔹 Nowy: nagłówki tak jak w StockTransactionPanel */}
                        <div className="header-row">
                          <div className="col-time">Time</div>
                          <div className="col-ticker">Ticker</div>
                          <div className="col-qty">Quantity</div>
                          <div className="col-type">Type</div>
                        </div>

                        <div className="user-column-content">
                          {userTxs.length === 0 ? (
                            <div className="no-tx">—</div>
                          ) : (
                            userTxs
                              .sort((a, b) => new Date(a.datetime) - new Date(b.datetime))
                              .map((tx, i) => (
                                <div key={i} className="txn-row">
                                  <div className="col-time">{tx.time}</div>
                                  <div className="col-ticker">{tx.ticker}</div>
                                  <div className="col-qty">{tx.quantity}</div>
                                  <div className={`col-type ${tx.type === "BUY" ? "buy" : "sell"}`}>
                                    {tx.type === "BUY" ? "➕" : "➖"}
                                  </div>
                                </div>
                              ))
                          )}

                        </div>

                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}

export default TransactionsView;