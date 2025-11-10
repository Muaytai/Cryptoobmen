"use client";

import React from "react";
import DocumentsTable from "../DocumentsTable";

export default function DocumentsPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Управление KYC документами</h1>
      <DocumentsTable />
    </div>
  );
}
