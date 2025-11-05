import React, { useEffect, useState } from "react";
import "./TransactionsView.css";

function TransactionsView({ selectedUserIds, colorPalette }) {
  const [transactions, setTransactions] = useState([]);
  const [groupedData, setGroupedData] = useState({});
  const [userNames, setUserNames] = useState({});

  // 🔹 Pobierz transakcje + nazwy użytkowników
  useEffect(() => {
    if (selectedUserIds.length === 0) {
      setTransactions([]);
      setUserNames({});
      return;
    }

    const fetchAll = async () => {
      const all = [];
      const names = {};

      for (const userId of selectedUserIds) {
        try {
          // 1️⃣ Transakcje
          const txRes = await fetch(`http://localhost:8000/portfolios/${userId}/transactions`);
          const txData = await txRes.json();
          all.push({ userId, transactions: txData });

          // 2️⃣ Dane użytkownika (jeśli masz np. /users/:id)
          const userRes = await fetch(`http://localhost:8000/users/${userId}`);
          if (userRes.ok) {
            const user = await userRes.json();
            names[userId] = user.name || `User ${userId}`;
          } else {
            names[userId] = `User ${userId}`;
          }
        } catch (err) {
          console.error("Fetch error:", err);
          names[userId] = `User ${userId}`;
        }
      }

      setTransactions(all);
      setUserNames(names);
    };

    fetchAll();
  }, [selectedUserIds]);

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
                  {selectedUserIds.map((userId, idx) => {
                    const color = colorPalette[idx % colorPalette.length];
                    const userTxs = users[userId] || [];

                    return (
                      <div
                        key={userId}
                        className="user-column"
                        style={{ borderColor: color }}
                      >
                        <div
                          className="user-name"
                          style={{
                            backgroundColor: color,
                            color: "#fff",
                          }}
                        >
                          {userNames[userId] || `User ${userId}`}
                        </div>

                        {userTxs.length === 0 ? (
                          <div className="no-tx">—</div>
                        ) : (
                          userTxs
                            .sort((a, b) => new Date(a.datetime) - new Date(b.datetime))
                            .map((tx, i) => (
                              <div key={i} className="transaction-item">
                                <div className="tx-time">{tx.time}</div>
                                <div className="tx-ticker">{tx.ticker}</div>
                                <div className="tx-qty">{tx.quantity}</div>
                                <div
                                  className={`tx-type ${
                                    tx.type === "BUY" ? "buy" : "sell"
                                  }`}
                                >
                                  {tx.type === "BUY" ? "➕" : "➖"}
                                </div>
                              </div>
                            ))
                        )}
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
