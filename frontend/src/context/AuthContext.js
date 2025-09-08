// context/AuthContext.js
import React, { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../utils/api";
import { tokenStorage } from "../utils/tokenStorage";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = tokenStorage.getAccessToken();
      if (accessToken) {
        try {
          const profile = await authApi.getProfile(accessToken);
          if (profile.error) {
            await handleTokenRefresh();
          } else {
            setUser(profile);
          }
        } catch (error) {
          console.log("Auth check failed:", error);
          tokenStorage.clearTokens();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleTokenRefresh = async () => {
    const refreshTokenValue = tokenStorage.getRefreshToken();
    if (refreshTokenValue) {
      try {
        const result = await authApi.refreshToken(refreshTokenValue);
        // Handle your backend's response format
        const newAccessToken = result.access_token;
        const newRefreshToken = result.refresh_token || refreshTokenValue;

        if (newAccessToken) {
          tokenStorage.setTokens(newAccessToken, newRefreshToken);
          const profile = await authApi.getProfile(newAccessToken);
          setUser(profile);
          return { success: true, message: "Token refreshed successfully" };
        } else {
          throw new Error("Refresh failed");
        }
      } catch (error) {
        tokenStorage.clearTokens();
        setUser(null);
        return {
          success: false,
          message: "Session expired, please login again",
        };
      }
    }
    return { success: false, message: "No refresh token available" };
  };

  const login = async (email, password) => {
    try {
      const result = await authApi.login(email, password);
      if (result.error) {
        return { success: false, message: `Login failed: ${result.error}` };
      } else {
        tokenStorage.setTokens(result.accessToken, result.refreshToken);
        const profile = await authApi.getProfile(result.accessToken);
        setUser(profile);
        return { success: true, message: "Login successful!" };
      }
    } catch (error) {
      return { success: false, message: `Error: ${error.message}` };
    }
  };

  const logout = () => {
    tokenStorage.clearTokens();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    refreshToken: handleTokenRefresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
