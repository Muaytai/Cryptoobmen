"use client";

import React from "react";
import CryptoTable from "../CryptoTable";

export default function CryptoPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Управление криптовалютами</h1>
      <CryptoTable />
    </div>
  );
}
