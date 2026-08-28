import { createContext, useContext, useEffect, useState } from "react";
import {
  seedUsers, getUsers, saveUsers, getCurrentUser,
  saveCurrentUser, clearCurrentUser,
} from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    seedUsers();
    setUser(getCurrentUser());
  }, []);

  const login = (email, pw, role) => {
    const match = getUsers().find(
      (u) => u.email.toLowerCase() === email.trim().toLowerCase() && u.password === pw && u.role === role
    );
    if (!match) return { error: "Invalid login details." };
    saveCurrentUser(match);
    setUser(match);
    return { user: match };
  };

  const signup = ({ name, email, company, password, role }) => {
    const users = getUsers();
    if (users.find((u) => u.email.toLowerCase() === email.toLowerCase() && u.role === role)) {
      return { error: "Account already exists for that role." };
    }
    const code = role === "Buyer" ? "BUY" : "SEL";
    const nu = {
      role, name, email, password, company,
      customerId: `CUST-${code}-${Date.now().toString().slice(-4)}`,
    };
    users.push(nu);
    saveUsers(users);
    saveCurrentUser(nu);
    setUser(nu);
    return { user: nu };
  };

  const logout = () => { clearCurrentUser(); setUser(null); };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
