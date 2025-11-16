import React from "react";

function StockTransactionList({ transactions }) {
  return (
    <div className="txn-list">
      {transactions
        .sort((a, b) => new Date(a.datetime) - new Date(b.datetime))
        .map((t, i) => (
          <div className="txn-row" key={i}>
            <div className="col-date">{new Date(t.datetime).toLocaleDateString()}</div>
            <div className="col-time">
              {new Date(t.datetime).toLocaleTimeString([], { 
                hour: "2-digit", 
                minute: "2-digit" 
              })}
            </div>
            <div className="col-quantity">{t.quantity}</div>
            <div className="col-price">{t.price}</div>
            <div className="col-total">{t.total_value}</div>
            <div className="col-ratio">{(t.ratio * 100).toFixed(2)}%</div>
          </div>
        ))}
    </div>
  );
}

export default StockTransactionList;