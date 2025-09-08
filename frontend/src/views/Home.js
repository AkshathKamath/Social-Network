// views/Home.js
import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { API_BASE } from "../utils/api";

const Home = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 text-center">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Auth Test Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Simple testing interface for JWT authentication backend services
          </p>
        </div>

        {user ? (
          /* Logged In State */
          <div className="bg-white rounded-lg shadow-md p-8 mb-8">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <span className="text-white text-2xl font-bold">
                  {(user.username || user.email).charAt(0).toUpperCase()}
                </span>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Welcome back!
              </h2>
              <p className="text-gray-600">
                Logged in as{" "}
                <span className="font-medium text-blue-600">{user.email}</span>
              </p>
            </div>

            <Link
              to="/dashboard"
              className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-8 rounded-lg transition duration-200"
            >
              Go to Dashboard
            </Link>
          </div>
        ) : (
          /* Not Logged In State */
          <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto mb-12">
            {/* Login Card */}
            <div className="bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition duration-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <span className="text-blue-600 text-xl font-bold">→</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Sign In
              </h3>
              <p className="text-gray-600 mb-4 text-sm">
                Access your existing account and test protected endpoints
              </p>
              <Link
                to="/login"
                className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-6 rounded-lg transition duration-200"
              >
                Login
              </Link>
            </div>

            {/* Register Card */}
            <div className="bg-white rounded-lg shadow-md p-8 hover:shadow-lg transition duration-200">
              <div className="w-12 h-12 bg-green-100 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <span className="text-green-600 text-xl font-bold">+</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Create Account
              </h3>
              <p className="text-gray-600 mb-4 text-sm">
                Register a new account to get started with testing
              </p>
              <Link
                to="/register"
                className="inline-block bg-green-500 hover:bg-green-600 text-white font-medium py-2 px-6 rounded-lg transition duration-200"
              >
                Register
              </Link>
            </div>
          </div>
        )}

        {/* API Info */}
        <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
          <h4 className="font-semibold text-gray-900 mb-3">
            Backend Configuration
          </h4>
          <div className="bg-gray-100 rounded px-4 py-2 mb-3">
            <code className="text-sm text-gray-800">{API_BASE}</code>
          </div>
          <p className="text-sm text-gray-600">
            Update API_BASE in{" "}
            <code className="bg-gray-100 px-2 py-1 rounded">utils/api.js</code>{" "}
            to match your backend URL
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
