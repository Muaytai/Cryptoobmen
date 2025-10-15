"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

type CryptoRow = {
  id: number | string;
  name: string;
  symbol: string;
  currency_type: string;
  network?: string;
  is_active: boolean;
  coingecko_id?: string;
  contract_address?: string;
  decimals?: number;
  requires_memo: boolean;
  min_exchange_amount: string;
  max_exchange_amount: string;
  fee_percentage: string;
  created_at?: string;
  updated_at?: string;
};

export default function CryptoTable() {
  const [cryptos, setCryptos] = useState<CryptoRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [showForm, setShowForm] = useState(false);
  const [editingCrypto, setEditingCrypto] = useState<CryptoRow | null>(null);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchCryptos = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/crypto/cryptocurrencies/", { headers });
      const data = res?.data ?? res;
      setCryptos(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить криптовалюты");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCryptos();
  }, [getAuthHeaders]);

  const filteredCryptos = cryptos.filter((crypto) => {
    const matchesSearch = 
      crypto.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      crypto.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (crypto.network && crypto.network.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = 
      filterType === "all" ||
      crypto.currency_type === filterType;

    const matchesStatus = 
      filterStatus === "all" ||
      (filterStatus === "active" && crypto.is_active) ||
      (filterStatus === "inactive" && !crypto.is_active);

    return matchesSearch && matchesType && matchesStatus;
  });

  const toggleActive = async (cryptoId: string | number, currentStatus: boolean) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/crypto/cryptocurrencies/${cryptoId}/`, 
        { is_active: !currentStatus }, 
        { headers }
      );
      await fetchCryptos();
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить статус криптовалюты");
    }
  };

  const deleteCrypto = async (cryptoId: string | number) => {
    if (!confirm("Вы уверены, что хотите удалить эту криптовалюту?")) return;
    
    try {
      const headers = getAuthHeaders();
      await api.delete(`/crypto/cryptocurrencies/${cryptoId}/`, { headers });
      await fetchCryptos();
    } catch (e: any) {
      setError(e?.message || "Не удалось удалить криптовалюту");
    }
  };

  if (loading) return <div className="py-4">Загрузка криптовалют…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      {/* Фильтры и поиск */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/20 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Поиск по названию, символу, сети..."
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
          <option value="crypto">Криптовалюты</option>
          <option value="fiat">Фиатные валюты</option>
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
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
        >
          Добавить
        </button>
        <button
          onClick={fetchCryptos}
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
              <th className="text-left p-3">Название</th>
              <th className="text-left p-3">Символ</th>
              <th className="text-left p-3">Тип</th>
              <th className="text-left p-3">Сеть</th>
              <th className="text-left p-3">Статус</th>
              <th className="text-left p-3">CoinGecko ID</th>
              <th className="text-left p-3">Комиссия %</th>
              <th className="text-left p-3">Min/Max</th>
              <th className="text-left p-3">Обновлено</th>
              <th className="text-left p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredCryptos.map((crypto) => (
              <tr key={crypto.id} className="border-t hover:bg-muted/40">
                <td className="p-3">
                  <div className="font-medium">{crypto.name}</div>
                  {crypto.contract_address && (
                    <div className="text-xs text-muted-foreground">
                      {crypto.contract_address.slice(0, 10)}...
                    </div>
                  )}
                </td>
                <td className="p-3">
                  <span className="font-mono">{crypto.symbol}</span>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    crypto.currency_type === 'crypto' 
                      ? "bg-blue-100 text-blue-800" 
                      : "bg-green-100 text-green-800"
                  }`}>
                    {crypto.currency_type === 'crypto' ? 'Crypto' : 'Fiat'}
                  </span>
                </td>
                <td className="p-3">{crypto.network || "—"}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    crypto.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  }`}>
                    {crypto.is_active ? "Активна" : "Неактивна"}
                  </span>
                </td>
                <td className="p-3">
                  {crypto.coingecko_id ? (
                    <span className="text-xs font-mono">{crypto.coingecko_id}</span>
                  ) : "—"}
                </td>
                <td className="p-3">
                  <span className="font-mono">{crypto.fee_percentage}%</span>
                </td>
                <td className="p-3">
                  <div className="text-xs">
                    <div>Min: {crypto.min_exchange_amount}</div>
                    <div>Max: {crypto.max_exchange_amount}</div>
                  </div>
                </td>
                <td className="p-3">
                  {crypto.updated_at?.slice(0, 10) || "—"}
                </td>
                <td className="p-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingCrypto(crypto)}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                    >
                      Редактировать
                    </button>
                    <button
                      onClick={() => toggleActive(crypto.id, crypto.is_active)}
                      className={`px-2 py-1 rounded text-xs ${
                        crypto.is_active 
                          ? "bg-red-100 text-red-800 hover:bg-red-200" 
                          : "bg-green-100 text-green-800 hover:bg-green-200"
                      }`}
                    >
                      {crypto.is_active ? "Деактивировать" : "Активировать"}
                    </button>
                    <button
                      onClick={() => deleteCrypto(crypto.id)}
                      className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                    >
                      Удалить
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredCryptos.length === 0 && (
              <tr>
                <td className="p-4 text-center text-muted-foreground" colSpan={10}>
                  Криптовалюты не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        Показано {filteredCryptos.length} из {cryptos.length} криптовалют
      </div>
    </div>
  );
}
