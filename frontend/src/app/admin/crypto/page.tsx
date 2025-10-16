"use client";

import React from "react";
import CryptoTable from "../CryptoTable";

export default function CryptoPage() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">💰 Управление криптовалютами</h1>
      </div>
      
      <CryptoTable />
    </div>
  );
}
