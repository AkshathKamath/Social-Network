// views/Dashboard.js
import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { authApi } from "../utils/api";
import { tokenStorage } from "../utils/tokenStorage";
import MessageAlert from "../components/MessageAlert";

const Dashboard = () => {
  const { user, refreshToken } = useAuth();
  const [message, setMessage] = useState("");

  const testProtectedEndpoint = async () => {
    const accessToken = tokenStorage.getAccessToken();
    try {
      const profile = await authApi.getProfile(accessToken);
      if (profile.error) {
        setMessage("Token expired, trying refresh...");
        const refreshResult = await refreshToken();
        if (refreshResult.success) {
          setMessage("Token refreshed and endpoint working!");
        } else {
          setMessage("Token refresh failed");
        }
      } else {
        setMessage("Protected endpoint working! User data refreshed.");
      }
    } catch (error) {
      setMessage(`Protected endpoint failed: ${error.message}`);
    }
  };

  const testTokenRefresh = async () => {
    const result = await refreshToken();
    setMessage(result.message);
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-center mb-6">Dashboard</h2>

      <MessageAlert message={message} onClose={() => setMessage("")} />

      <div className="bg-blue-50 p-4 rounded mb-6">
        <h3 className="font-semibold text-lg">User Information</h3>
        <p className="text-sm text-gray-600">User ID: {user?.id}</p>
        <p className="text-sm text-gray-600">Email: {user?.email}</p>
        <p className="text-sm text-gray-600">Username: {user?.username}</p>
      </div>

      <div className="space-y-3">
        <button
          onClick={testProtectedEndpoint}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
        >
          Test Protected Endpoint
        </button>

        <button
          onClick={testTokenRefresh}
          className="w-full bg-yellow-500 text-white py-2 px-4 rounded hover:bg-yellow-600"
        >
          Test Token Refresh
        </button>
      </div>

      {/* Token Info */}
      <div className="mt-6 p-3 bg-gray-100 rounded text-xs">
        <p className="mb-1">
          <strong>Access Token:</strong>
        </p>
        <p className="break-all">
          {tokenStorage.getAccessToken()?.substring(0, 100)}...
        </p>
        <p className="mb-1 mt-2">
          <strong>Refresh Token:</strong>
        </p>
        <p className="break-all">
          {tokenStorage.getRefreshToken()?.substring(0, 100)}...
        </p>
      </div>
    </div>
  );
};

export default Dashboard;
