import React, { useState, useEffect, useRef } from "react";
import { fetchUsers } from "../PortfolioChart/utils/fetchUtils";
import "./UserSelector.css";

function UserSelector({ onSelectionChange }) {
  const [users, setUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState({}); // {id: name, id: name, ...}
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

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

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCheckboxChange = (user) => {
    setSelectedUsers((prev) => {
      const updated = { ...prev };
      
      if (updated[user.id]) {
        // Usuń użytkownika
        delete updated[user.id];
      } else {
        // Dodaj użytkownika
        updated[user.id] = user.name;
      }
      
      // Przekaż posortowany słownik do komponentu nadrzędnego
      onSelectionChange(updated);
      
      return updated;
    });
  };

  // Tekst przycisku
  const selectedCount = Object.keys(selectedUsers).length;
  const buttonLabel =
    selectedCount === 0
      ? "Select users"
      : selectedCount === 1
      ? Object.values(selectedUsers)[0]
      : `${selectedCount} users selected`;

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
                checked={!!selectedUsers[user.id]}
                onChange={() => handleCheckboxChange(user)}
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
