import React, { useState, useEffect, useRef } from "react";
import { fetchUsers } from "../PortfolioChart/utils/fetchUtils";
import "./UserSelector.css";

function UserSelector({ onSelectionChange }) {
  const [users, setUsers] = useState([]);
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // 🔹 Pobranie użytkowników
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

  // 🔹 Klik poza dropdownem — zamknij
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 🔹 Zmiana wyboru użytkownika
  const handleCheckboxChange = (userId) => {
    setSelectedUserIds((prev) => {
      const updated = prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId];
      onSelectionChange(updated);
      return updated;
    });
  };

  // 🔹 Tekst przycisku
  const buttonLabel =
    selectedUserIds.length === 0
      ? "Select users"
      : selectedUserIds.length === 1
      ? users.find((u) => u.id === selectedUserIds[0])?.name
      : `${selectedUserIds.length} users selected`;

  return (
    <div className="user-selector-wrapper" ref={dropdownRef}>
      <button className="user-select" onClick={() => setOpen(!open)}>
        {buttonLabel} <span className="arrow">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="user-dropdown">
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
      )}
    </div>
  );
}

export default UserSelector;
