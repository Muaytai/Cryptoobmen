"use client";

import React from "react";
import UsersTable from "./UsersTable";

export default function AdminPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Главная панель</h1>
      <div className="space-y-6">
        <section>
          <h2 className="text-lg font-medium mb-3">Пользователи</h2>
          <UsersTable />
        </section>
      </div>
    </div>
  );
}


