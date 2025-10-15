"use client";

import React from "react";
import TransactionsTable from "../TransactionsTable";

export default function TransactionsPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Управление транзакциями</h1>
      <TransactionsTable />
    </div>
  );
}
