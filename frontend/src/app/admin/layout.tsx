"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import Link from "next/link";
import { useTheme } from "next-themes";

const adminNavItems = [
  { href: "/admin/", label: "Главная", icon: "🏠" },
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
  const { theme } = useTheme();

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
    <div className={`min-h-screen transition-colors duration-300 ${
      theme === 'dark' 
        ? 'bg-gray-900' 
        : 'bg-gray-50'
    }`}>
      {/* Header */}
      <header className={`border-b transition-colors duration-300 ${
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700'
          : 'bg-white border-gray-200'
      }`}>
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className={`text-xl font-semibold transition-colors duration-300 ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>Админ-панель</h1>
            <div className="flex items-center gap-4">
              <span className={`text-sm transition-colors duration-300 ${
                theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                {user.email}
              </span>
              <Link
                href="/me"
                className={`text-sm hover:underline transition-colors duration-300 ${
                  theme === 'dark' 
                    ? 'text-blue-400 hover:text-blue-300' 
                    : 'text-blue-600 hover:text-blue-700'
                }`}
              >
                ← Назад в профиль
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`w-64 border-r min-h-screen relative transition-colors duration-300 ${
          theme === 'dark'
            ? 'bg-gray-800 border-gray-700'
            : 'bg-white border-gray-200'
        }`}>
          <nav className="p-4">
            <ul className="space-y-2">
              {adminNavItems.map((item) => {
                // Логика подсветки с учетом слэшей
                const isActive = pathname === item.href || 
                  (item.href !== "/admin/" && pathname.startsWith(item.href + "/"));
                
                return (
                  <li key={item.href} className="relative">
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all duration-200 ${
                        isActive
                          ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                          : theme === 'dark'
                            ? "text-gray-300 hover:text-white hover:bg-gray-700"
                            : "text-gray-700 hover:text-gray-900 hover:bg-gray-100"
                      }`}
                    >
                      <span className="text-lg">{item.icon}</span>
                      <span className="font-medium">{item.label}</span>
                      
                      {/* Индикатор активной страницы */}
                      {isActive && (
                        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-white rounded-r-full shadow-sm"></div>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
          
          {/* Дополнительная информация в сайдбаре */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className={`rounded-lg p-3 border transition-colors duration-300 ${
              theme === 'dark'
                ? 'bg-gray-700 border-gray-600'
                : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-sm font-medium transition-colors duration-300 ${
                  theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>👤 {user.username}</span>
              </div>
              <div className={`text-xs transition-colors duration-300 ${
                theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>
                Администратор сайта
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className={`flex-1 p-6 transition-colors duration-300 ${
          theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
        }`}>
          {children}
        </main>
      </div>
    </div>
  );
}
