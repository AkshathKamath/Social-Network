// components/MessageAlert.js
import React from "react";

const MessageAlert = ({ message, onClose }) => {
  if (!message) return null;

  const isError = message.includes("failed") || message.includes("Error");

  return (
    <div
      className={`p-3 rounded mb-4 ${
        isError
          ? "bg-red-100 text-red-700 border border-red-300"
          : "bg-green-100 text-green-700 border border-green-300"
      }`}
    >
      <div className="flex justify-between items-center">
        <span>{message}</span>
        {onClose && (
          <button onClick={onClose} className="ml-2 text-sm font-bold">
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default MessageAlert;
