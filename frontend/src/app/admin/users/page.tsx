"use client";

import React from "react";
import UsersTable from "../UsersTable";

export default function UsersPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Управление пользователями</h1>
      <UsersTable />
    </div>
  );
}
