"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import Link from "next/link";

const adminNavItems = [
  { href: "/admin", label: "Главная", icon: "🏠" },
  { href: "/admin/users", label: "Пользователи", icon: "👥" },
  { href: "/admin/crypto", label: "Криптовалюты", icon: "💰" },
  { href: "/admin/transactions", label: "Транзакции", icon: "💳" },
  { href: "/admin/wallets", label: "Кошельки", icon: "👛" },
  { href: "/admin/documents", label: "KYC Документы", icon: "📄" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const checkAuthStatus = useAuthStore((s) => s.checkAuthStatus);

  useEffect(() => {
    if (!user && !isLoading) {
      checkAuthStatus().catch(() => {});
    }
  }, [user, isLoading, checkAuthStatus]);

  useEffect(() => {
    if (!isLoading && user && !user.is_site_admin) {
      router.replace("/me");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return <div className="p-6">Загрузка…</div>;
  }

  if (!user.is_site_admin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold">Админ-панель</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {user.email}
              </span>
              <Link
                href="/me"
                className="text-sm text-primary hover:underline"
              >
                ← Назад в профиль
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-card min-h-screen">
          <nav className="p-4">
            <ul className="space-y-2">
              {adminNavItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                      pathname === item.href || pathname.startsWith(item.href + "/")
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    }`}
                  >
                    <span>{item.icon}</span>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
