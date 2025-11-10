"use client";

import React from "react";
import AdminDashboard from "./AdminDashboard";
import AdminGuide from "./AdminGuide";

export default function AdminPage() {
  return (
    <div className="space-y-8">
      {/* Руководство администратора */}
      <AdminGuide />
      
      {/* Основной дашборд */}
      <AdminDashboard />
    </div>
  );
}



