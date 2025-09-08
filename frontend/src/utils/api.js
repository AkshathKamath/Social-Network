// utils/api.js

// API base URL - change this to match your backend
const API_BASE = "http://localhost:4000/api/v1"; // Adjust port as needed

export const authApi = {
  register: async (email, password, username, fullName, dateOfBirth) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        user_name: username, // Match backend field name
        full_name: fullName, // Match backend field name
        date_of_birth: dateOfBirth, // Match backend field name
      }),
    });
    return res.json();
  },

  login: async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return res.json();
  },

  getProfile: async (token) => {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.json();
  },

  refreshToken: async (refreshToken) => {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });
    return res.json();
  },
};

export { API_BASE };
