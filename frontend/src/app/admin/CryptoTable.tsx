"use client";

import React, { useCallback, useEffect, useState } from "react";
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
  const [setShowForm] = useState(false);
  const [setEditingCrypto] = useState<CryptoRow | null>(null);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchCryptos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res = await api.get<{ results: CryptoRow[] }>("/crypto/cryptocurrencies/", { headers });
      const data = res.data.results ?? [];
      setCryptos(Array.isArray(data) ? data : []);
    } catch (e: unknown) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Не удалось загрузить криптовалюты");
      }
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchCryptos();
  }, [fetchCryptos]);

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
    } catch (e: unknown) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Не удалось обновить статус криптовалюты");
      }
    }
  };

  const deleteCrypto = async (cryptoId: string | number) => {
    if (!confirm("Вы уверены, что хотите удалить эту криптовалюту?")) return;
    
    try {
      const headers = getAuthHeaders();
      await api.delete(`/crypto/cryptocurrencies/${cryptoId}/`, { headers });
      await fetchCryptos();
    } catch (e: unknown) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError("Не удалось удалить криптовалюту");
      }
    }
  };

  if (loading) return <div className="py-4">Загрузка криптовалют…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      {/* Фильтры и поиск */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-100">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[250px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🔍 Поиск криптовалют
            </label>
            <input
              type="text"
              placeholder="Введите название, символ или сеть..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              💰 Тип
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все типы</option>
              <option value="crypto">Криптовалюты</option>
              <option value="fiat">Фиатные валюты</option>
            </select>
          </div>
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ✅ Статус
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все статусы</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg text-sm font-medium hover:from-green-700 hover:to-emerald-700 transition-all transform hover:scale-105 shadow-lg"
            >
              ➕ Добавить
            </button>
            <button
              onClick={fetchCryptos}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
            >
              🔄 Обновить
            </button>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего криптовалют</p>
              <p className="text-2xl font-bold text-gray-900">{cryptos.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">💰</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Активные</p>
              <p className="text-2xl font-bold text-green-600">{cryptos.filter(c => c.is_active).length}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Криптовалюты</p>
              <p className="text-2xl font-bold text-purple-600">{cryptos.filter(c => c.currency_type === 'crypto').length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">🪙</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Фиатные</p>
              <p className="text-2xl font-bold text-orange-600">{cryptos.filter(c => c.currency_type === 'fiat').length}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">💵</span>
            </div>
          </div>
        </div>
      </div>

      {/* Таблица */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Криптовалюта</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Тип</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Сеть</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Статус</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Комиссия</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Лимиты</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Обновлено</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredCryptos.map((crypto) => (
                <tr key={crypto.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-medium text-sm">
                        {crypto.symbol}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{crypto.name}</div>
                        <div className="text-xs text-gray-500 font-mono">{crypto.symbol}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      crypto.currency_type === 'crypto' 
                        ? "bg-blue-100 text-blue-800" 
                        : "bg-green-100 text-green-800"
                    }`}>
                      {crypto.currency_type === 'crypto' ? 'Crypto' : 'Fiat'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-900">{crypto.network || "—"}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      crypto.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    }`}>
                      {crypto.is_active ? "Активна" : "Неактивна"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{crypto.fee_percentage}%</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs text-gray-600">
                      <div>Min: {crypto.min_exchange_amount}</div>
                      <div>Max: {crypto.max_exchange_amount}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {crypto.updated_at ? new Date(crypto.updated_at).toLocaleDateString('ru-RU') : "—"}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => setEditingCrypto(crypto)}
                        className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                      >
                        Редактировать
                      </button>
                      <button
                        onClick={() => toggleActive(crypto.id, crypto.is_active)}
                        className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                          crypto.is_active 
                            ? "bg-red-100 text-red-700 hover:bg-red-200" 
                            : "bg-green-100 text-green-700 hover:bg-green-200"
                        }`}>
                        {crypto.is_active ? "Деактивировать" : "Активировать"}
                      </button>
                      <button
                        onClick={() => deleteCrypto(crypto.id)}
                        className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                      >
                        Удалить
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredCryptos.length === 0 && (
                <tr>
                  <td className="px-4 py-8 text-center text-gray-500" colSpan={8}>
                    <p className="text-sm">Криптовалюты не найдены</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Информация о результатах */}
      <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-4 py-3 rounded-lg">
        <span>Показано {filteredCryptos.length} из {cryptos.length} криптовалют</span>
        {filteredCryptos.length > 0 && (
          <span className="text-blue-600">Последнее обновление: {new Date().toLocaleTimeString('ru-RU')}</span>
        )}
      </div>
    </div>
  );
}
