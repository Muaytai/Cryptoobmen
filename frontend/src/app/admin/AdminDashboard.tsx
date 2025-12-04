"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

interface DashboardStats {
  users: {
    total: number;
    active: number;
    verified: number;
    kyc_verified: number;
    new_today: number;
  };
  transactions: {
    total: number;
    pending: number;
    completed: number;
    failed: number;
    volume_24h: number;
    volume_7d: number;
  };
  wallets: {
    total: number;
    total_balance_usd: number;
    active_currencies: number;
  };
  system: {
    active_cryptocurrencies: number;
    total_exchange_pairs: number;
    system_health: 'good' | 'warning' | 'critical';
  };
}

interface RecentActivity {
  id: number;
  type: 'user_registration' | 'transaction' | 'verification' | 'withdrawal';
  description: string;
  timestamp: string;
  user?: {
    username: string;
    email: string;
  };
  amount?: string;
  currency?: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  date_joined: string;
}

interface Transaction {
  id: number;
  type_display: string;
  amount: string;
  crypto_info?: {
    symbol: string;
  };
  timestamp: string;
  user_info?: {
    username: string;
    email: string;
  };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      
      const statsRes = await api.get<DashboardStats>("/accounts/users/dashboard_stats/", { headers });
      const dashboardStats = statsRes.data;
      
      setStats(dashboardStats);

      const usersRes = await api.get<{ results: User[] }>("/accounts/users/admin_list/", { headers });
      const users = usersRes.data.results ?? [];
      
      const transactionsRes = await api.get<{ results: Transaction[] }>("/transactions/transactions/admin_list/?page_size=50", { headers });
      const transactions = transactionsRes?.data?.results ?? [];

      const activity: RecentActivity[] = [];
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      
      users
        .filter((u: User) => new Date(u.date_joined) >= yesterday)
        .slice(0, 5)
        .forEach((u: User) => {
          activity.push({
            id: u.id,
            type: 'user_registration',
            description: 'Новый пользователь зарегистрировался',
            timestamp: u.date_joined,
            user: { username: u.username, email: u.email },
          });
        });

      transactions
        .filter((t: Transaction) => new Date(t.timestamp) >= yesterday)
        .slice(0, 10)
        .forEach((t: Transaction) => {
          activity.push({
            id: t.id,
            type: 'transaction',
            description: `Транзакция ${t.type_display} ${t.amount} ${t.crypto_info?.symbol}`,
            timestamp: t.timestamp,
            user: t.user_info ? { username: t.user_info.username, email: t.user_info.email } : undefined,
            amount: t.amount,
            currency: t.crypto_info?.symbol,
          });
        });

      activity.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setRecentActivity(activity.slice(0, 15));

    } catch (e: unknown) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Не удалось загрузить данные дашборда");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getActivityIcon = (type: string) => {
    const icons: Record<string, string> = {
      'user_registration': '👤',
      'transaction': '💳',
      'verification': '✅',
      'withdrawal': '⬆️',
    };
    return icons[type] || '📝';
  };

  const getHealthColor = (health: string) => {
    const colors: Record<string, string> = {
      'good': 'text-green-600 bg-green-100',
      'warning': 'text-yellow-600 bg-yellow-100',
      'critical': 'text-red-600 bg-red-100',
    };
    return colors[health] || 'text-gray-600 bg-gray-100';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка дашборда...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📊</span>
            <h1 className="text-2xl font-semibold text-gray-900">Дашборд администратора</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthColor(stats.system.system_health)}`}>
              {stats.system.system_health === 'good' && '✅ Система работает нормально'}
              {stats.system.system_health === 'warning' && '⚠️ Требует внимания'}
              {stats.system.system_health === 'critical' && '🚨 Критические проблемы'}
            </span>
            <button
              onClick={fetchDashboardData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              🔄 Обновить
            </button>
          </div>
        </div>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Пользователи */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">👥</span>
            </div>
            <span className="text-2xl font-bold text-blue-600">{formatNumber(stats.users.total)}</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Пользователи</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Активных:</span>
              <span className="font-medium">{formatNumber(stats.users.active)}</span>
            </div>
            <div className="flex justify-between">
              <span>Верифицированных:</span>
              <span className="font-medium">{formatNumber(stats.users.verified)}</span>
            </div>
            <div className="flex justify-between">
              <span>KYC пройден:</span>
              <span className="font-medium">{formatNumber(stats.users.kyc_verified)}</span>
            </div>
            <div className="flex justify-between">
              <span>Новых сегодня:</span>
              <span className="font-medium text-green-600">{formatNumber(stats.users.new_today)}</span>
            </div>
          </div>
        </div>

        {/* Транзакции */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">💳</span>
            </div>
            <span className="text-2xl font-bold text-green-600">{formatNumber(stats.transactions.total)}</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Транзакции</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Завершено:</span>
              <span className="font-medium text-green-600">{formatNumber(stats.transactions.completed)}</span>
            </div>
            <div className="flex justify-between">
              <span>В обработке:</span>
              <span className="font-medium text-yellow-600">{formatNumber(stats.transactions.pending)}</span>
            </div>
            <div className="flex justify-between">
              <span>Ошибок:</span>
              <span className="font-medium text-red-600">{formatNumber(stats.transactions.failed)}</span>
            </div>
            <div className="flex justify-between">
              <span>Объем за 24ч:</span>
              <span className="font-medium">{formatCurrency(stats.transactions.volume_24h)}</span>
            </div>
          </div>
        </div>

        {/* Кошельки */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
            <span className="text-2xl font-bold text-purple-600">{formatNumber(stats.wallets.total)}</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Кошельки</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Общий баланс:</span>
              <span className="font-medium">{formatCurrency(stats.wallets.total_balance_usd)}</span>
            </div>
            <div className="flex justify-between">
              <span>Активных валют:</span>
              <span className="font-medium">{formatNumber(stats.wallets.active_currencies)}</span>
            </div>
          </div>
        </div>

        {/* Система */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">⚙️</span>
            </div>
            <span className="text-2xl font-bold text-orange-600">{formatNumber(stats.system.active_cryptocurrencies)}</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Система</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Криптовалют:</span>
              <span className="font-medium">{formatNumber(stats.system.active_cryptocurrencies)}</span>
            </div>
            <div className="flex justify-between">
              <span>Пар обмена:</span>
              <span className="font-medium">{formatNumber(stats.system.total_exchange_pairs)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Недавняя активность */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">📈 Недавняя активность</h2>
        <div className="space-y-3">
          {recentActivity.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Нет недавней активности</p>
          ) : (
            recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-xl">{getActivityIcon(activity.type)}</span>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  {activity.user && (
                    <p className="text-xs text-gray-500">
                      {activity.user.username} ({activity.user.email})
                    </p>
                  )}
                  {activity.amount && activity.currency && (
                    <p className="text-xs text-gray-500">
                      {activity.amount} {activity.currency}
                    </p>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(activity.timestamp).toLocaleString('ru-RU')}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Быстрые действия */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">🚀 Быстрые действия</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/admin/users"
            className="flex items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <span className="text-2xl">👥</span>
            <div>
              <h3 className="font-medium text-gray-900">Пользователи</h3>
              <p className="text-sm text-gray-500">Управление пользователями</p>
            </div>
          </Link>
          <Link
            href="/admin/transactions"
            className="flex items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <span className="text-2xl">💳</span>
            <div>
              <h3 className="font-medium text-gray-900">Транзакции</h3>
              <p className="text-sm text-gray-500">Просмотр транзакций</p>
            </div>
          </Link>
          <Link
            href="/admin/crypto"
            className="flex items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <span className="text-2xl">💰</span>
            <div>
              <h3 className="font-medium text-gray-900">Криптовалюты</h3>
              <p className="text-sm text-gray-500">Управление валютами</p>
            </div>
          </Link>
          <Link
            href="/admin/wallets"
            className="flex items-center gap-3 p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <span className="text-2xl">👛</span>
            <div>
              <h3 className="font-medium text-gray-900">Кошельки</h3>
              <p className="text-sm text-gray-500">Управление кошельками</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
