"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

type WalletRow = {
  id: number | string;
  user: {
    id: number | string;
    email: string;
    username: string;
  };
  currency: {
    id: number | string;
    name: string;
    symbol: string;
  };
  balance: string;
  available_balance: string;
  locked_balance: string;
  deposit_address?: string;
  is_system_wallet: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export default function WalletsTable() {
  const [wallets, setWallets] = useState<WalletRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCrypto, setFilterCrypto] = useState("all");
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchWallets = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/crypto/wallets/", { headers });
      const data = res?.data ?? res;
      setWallets(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить кошельки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWallets();
  }, [getAuthHeaders]);

  const filteredWallets = wallets.filter((wallet) => {
    const matchesSearch = 
      wallet.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wallet.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (wallet.deposit_address && wallet.deposit_address.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = 
      filterType === "all" ||
      (filterType === "user" && !wallet.is_system_wallet) ||
      (filterType === "system" && wallet.is_system_wallet);

    const matchesStatus = 
      filterStatus === "all" ||
      (filterStatus === "active" && wallet.is_active) ||
      (filterStatus === "inactive" && !wallet.is_active);

    const matchesCrypto = 
      filterCrypto === "all" ||
      wallet.currency.symbol.toLowerCase() === filterCrypto.toLowerCase();

    return matchesSearch && matchesType && matchesStatus && matchesCrypto;
  });

  const toggleActive = async (walletId: string | number, currentStatus: boolean) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/crypto/wallets/${walletId}/`, 
        { is_active: !currentStatus }, 
        { headers }
      );
      await fetchWallets();
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить статус кошелька");
    }
  };

  const formatBalance = (balance: string) => {
    const num = parseFloat(balance);
    if (num === 0) return "0";
    if (num < 0.000001) return "< 0.000001";
    return num.toFixed(8).replace(/\.?0+$/, '');
  };

  if (loading) return <div className="py-4">Загрузка кошельков…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      {/* Фильтры и поиск */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/20 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Поиск по email, username, адресу..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все типы</option>
          <option value="user">Пользовательские</option>
          <option value="system">Системные</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все статусы</option>
          <option value="active">Активные</option>
          <option value="inactive">Неактивные</option>
        </select>
        <select
          value={filterCrypto}
          onChange={(e) => setFilterCrypto(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все валюты</option>
          {Array.from(new Set(wallets.map(w => w.currency.symbol))).map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
        <button
          onClick={fetchWallets}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90"
        >
          Обновить
        </button>
      </div>

      {/* Таблица */}
      <div className="w-full overflow-x-auto border rounded-md">
        <table className="min-w-[1200px] w-full text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="text-left p-3">Пользователь</th>
              <th className="text-left p-3">Валюта</th>
              <th className="text-left p-3">Тип</th>
              <th className="text-left p-3">Общий баланс</th>
              <th className="text-left p-3">Доступно</th>
              <th className="text-left p-3">Заблокировано</th>
              <th className="text-left p-3">Адрес депозита</th>
              <th className="text-left p-3">Статус</th>
              <th className="text-left p-3">Обновлено</th>
              <th className="text-left p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredWallets.map((wallet) => (
              <tr key={wallet.id} className="border-t hover:bg-muted/40">
                <td className="p-3">
                  {wallet.is_system_wallet ? (
                    <div className="text-muted-foreground">Системный</div>
                  ) : (
                    <div>
                      <div className="font-medium">{wallet.user.email}</div>
                      <div className="text-xs text-muted-foreground">{wallet.user.username}</div>
                    </div>
                  )}
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-1">
                    <span className="font-mono font-medium">{wallet.currency.symbol}</span>
                    <span className="text-xs text-muted-foreground">({wallet.currency.name})</span>
                  </div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    wallet.is_system_wallet 
                      ? "bg-red-100 text-red-800" 
                      : "bg-blue-100 text-blue-800"
                  }`}>
                    {wallet.is_system_wallet ? "Системный" : "Пользовательский"}
                  </span>
                </td>
                <td className="p-3">
                  <div className="font-mono font-medium">
                    {formatBalance(wallet.balance)}
                  </div>
                </td>
                <td className="p-3">
                  <div className="font-mono text-green-600">
                    {formatBalance(wallet.available_balance)}
                  </div>
                </td>
                <td className="p-3">
                  <div className="font-mono text-orange-600">
                    {formatBalance(wallet.locked_balance)}
                  </div>
                </td>
                <td className="p-3">
                  {wallet.deposit_address ? (
                    <div className="font-mono text-xs max-w-[120px] truncate">
                      {wallet.deposit_address}
                    </div>
                  ) : "—"}
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    wallet.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  }`}>
                    {wallet.is_active ? "Активен" : "Неактивен"}
                  </span>
                </td>
                <td className="p-3">
                  <div className="text-xs">
                    <div>{wallet.updated_at.slice(0, 10)}</div>
                    <div className="text-muted-foreground">{wallet.updated_at.slice(11, 19)}</div>
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => window.location.href = `/admin/users/${wallet.user.id}`}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                    >
                      Пользователь
                    </button>
                    <button
                      onClick={() => toggleActive(wallet.id, wallet.is_active)}
                      className={`px-2 py-1 rounded text-xs ${
                        wallet.is_active 
                          ? "bg-red-100 text-red-800 hover:bg-red-200" 
                          : "bg-green-100 text-green-800 hover:bg-green-200"
                      }`}
                    >
                      {wallet.is_active ? "Деактивировать" : "Активировать"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredWallets.length === 0 && (
              <tr>
                <td className="p-4 text-center text-muted-foreground" colSpan={10}>
                  Кошельки не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        Показано {filteredWallets.length} из {wallets.length} кошельков
      </div>
    </div>
  );
}
