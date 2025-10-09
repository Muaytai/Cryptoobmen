"use client";

import React from "react";
import WalletsTable from "../WalletsTable";

export default function WalletsPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Управление кошельками</h1>
      <WalletsTable />
    </div>
  );
}
