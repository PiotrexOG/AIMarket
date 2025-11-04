import React, { useState, useEffect } from "react";
import { fetchUsers } from "../PortfolioChart/utils/fetchUtils";
import "./UserSelector.css";

function UserSelector({ onSelectionChange }) {
  const [users, setUsers] = useState([]);
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  // 🔹 Pobierz listę użytkowników
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const data = await fetchUsers();
        setUsers(data);
      } catch (err) {
        console.error("Fetch users error:", err);
      }
    };
    loadUsers();
  }, []);

  // 🔹 Obsługa kliknięcia checkboxa
  const handleCheckboxChange = (userId) => {
    setSelectedUserIds((prev) => {
      const updated = prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId];

      onSelectionChange(updated); // informujemy rodzica (App.js)
      return updated;
    });
  };

  if (users.length === 0) {
    return <p>Loading users...</p>;
  }

  return (
    <div className="user-selector">
      <h3>Select Users:</h3>
      <div className="user-list">
        {users.map((user) => (
          <label key={user.id} className="user-item">
            <input
              type="checkbox"
              checked={selectedUserIds.includes(user.id)}
              onChange={() => handleCheckboxChange(user.id)}
            />
            {user.name}
          </label>
        ))}
      </div>
    </div>
  );
}

export default UserSelector;
