"use client";

import React, { useEffect, useState, useCallback } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";
import TransactionDetailsModal from "@/components/TransactionDetailsModal";

type TransactionRow = {
  id: number;
  transaction_id: string;
  type: string;
  status: string;
  amount: string;
  fee: string;
  timestamp: string;
  updated_at: string;
  tx_hash?: string;
  block_number?: number;
  notes?: string;
  ip_address?: string;
  type_display: string;
  status_display: string;
  user_info: {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
    is_verified: boolean;
    kyc_verified: boolean;
  };
  crypto_info: {
    id: number;
    name: string;
    symbol: string;
    network?: string;
    icon?: string;
  };
  exchange_info?: Record<string, unknown>;
  deposit_info?: Record<string, unknown>;
  withdrawal_info?: Record<string, unknown>;
};

type TransactionsResponse = {
  results: TransactionRow[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export default function TransactionsTable() {
  const [transactions, setTransactions] = useState<TransactionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCrypto, setFilterCrypto] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selectedTransactionId, setSelectedTransactionId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 50,
    total_pages: 1,
    count: 0
  });
  
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);
  const user = useAuthStore((s) => s.user);
  const checkAuthStatus = useAuthStore((s) => s.checkAuthStatus);

  // Обернули в useCallback и добавили все зависимости
  const fetchTransactions = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pagination.page_size.toString(),
      });

      if (searchTerm) params.append('search', searchTerm);
      if (filterType !== 'all') params.append('type', filterType);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      if (filterCrypto !== 'all') params.append('crypto_id', filterCrypto);
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const res = await api.get<TransactionsResponse>(`/transactions/transactions/admin_list/?${params}`, { headers });
      const data: TransactionsResponse =
        (res as { data?: TransactionsResponse }).data ?? (res as TransactionsResponse);
      
      setTransactions(data.results || []);
      setPagination((prev) => ({
        ...prev,
        page: data.page,
        page_size: data.page_size,
        total_pages: data.total_pages,
        count: data.count
      }));
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : null;
      setError(message || "Не удалось загрузить транзакции");
    } finally {
      setLoading(false);
    }
  }, [
    getAuthHeaders,
    pagination.page_size,
    searchTerm,
    filterType,
    filterStatus,
    filterCrypto,
    dateFrom,
    dateTo
  ]);

  useEffect(() => {
    const initData = async () => {
      setAuthLoading(true);
      try {
        if (!user) {
          await checkAuthStatus();
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setError('Ошибка аутентификации');
      } finally {
        setAuthLoading(false);
      }
    };
    
    initData();
  }, [user, checkAuthStatus]);

  useEffect(() => {
    if (user && !authLoading) {
      fetchTransactions(1);
    }
  }, [user, authLoading, fetchTransactions]);

  const openTransactionDetails = (transactionId: number) => {
    setSelectedTransactionId(transactionId);
    setIsModalOpen(true);
  };

  const closeTransactionDetails = () => {
    setSelectedTransactionId(null);
    setIsModalOpen(false);
  };

  const handleSearch = () => {
    fetchTransactions(1);
  };

  const handlePageChange = (newPage: number) => {
    fetchTransactions(newPage);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount: string) => {
    return parseFloat(amount).toFixed(8);
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'awaiting_confirmation': 'bg-orange-100 text-orange-800',
      'processing': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800',
      'refunded': 'bg-purple-100 text-purple-800',
    };
    
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: string) => {
    const typeIcons: Record<string, string> = {
      'deposit': '⬇️',
      'withdrawal': '⬆️',
      'exchange': '🔄',
      'transfer': '↔️',
      'fee': '💰',
      'consolidation': '📦',
    };
    
    return typeIcons[type] || '📝';
  };

  if (authLoading) return <div className="py-4">Проверка аутентификации…</div>;
  if (loading && transactions.length === 0) return <div className="py-4">Загрузка транзакций…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;
  if (!user) return <div className="py-4 text-red-500">Необходима аутентификация</div>;

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📊</span>
          <h1 className="text-2xl font-semibold text-gray-900">Управление транзакциями</h1>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-100">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🔍 Поиск
            </label>
            <input
              type="text"
              placeholder="ID, email, username, hash..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📝 Тип
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все типы</option>
              <option value="deposit">Депозит</option>
              <option value="withdrawal">Вывод</option>
              <option value="exchange">Обмен</option>
              <option value="transfer">Перевод</option>
              <option value="fee">Комиссия</option>
              <option value="consolidation">Консолидация</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ✅ Статус
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все статусы</option>
              <option value="pending">В ожидании</option>
              <option value="awaiting_confirmation">Ожидает подтверждения</option>
              <option value="processing">В обработке</option>
              <option value="completed">Завершено</option>
              <option value="failed">Ошибка</option>
              <option value="cancelled">Отменено</option>
              <option value="refunded">Возвращено</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              💰 Криптовалюта
            </label>
            <select
              value={filterCrypto}
              onChange={(e) => setFilterCrypto(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все валюты</option>
              <option value="1">Bitcoin</option>
              <option value="2">Ethereum</option>
              <option value="3">USDT</option>
              {/* Добавьте другие валюты по необходимости */}
            </select>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📅 Дата от
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📅 Дата до
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSearch}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
          >
            🔍 Поиск
          </button>
          <button
            onClick={() => {
              setSearchTerm("");
              setFilterType("all");
              setFilterStatus("all");
              setFilterCrypto("all");
              setDateFrom("");
              setDateTo("");
              // Сброс инициирует обновление через useEffect, так как зависимости fetchTransactions изменятся
            }}
            className="px-6 py-3 bg-gray-500 text-white rounded-lg text-sm font-medium hover:bg-gray-600 transition-all"
          >
            🗑️ Сбросить
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего транзакций</p>
              <p className="text-2xl font-bold text-gray-900">{pagination.count}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Завершено</p>
              <p className="text-2xl font-bold text-green-600">
                {transactions.filter(t => t.status === 'completed').length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">В обработке</p>
              <p className="text-2xl font-bold text-blue-600">
                {transactions.filter(t => t.status === 'processing').length}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">⏳</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Ошибки</p>
              <p className="text-2xl font-bold text-red-600">
                {transactions.filter(t => t.status === 'failed').length}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">❌</span>
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
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Транзакция</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Пользователь</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Тип</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Статус</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Сумма</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Дата</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {transactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getTypeIcon(transaction.type)}</span>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {transaction.transaction_id.substring(0, 8)}...
                        </div>
                        <div className="text-xs text-gray-500">
                          ID: {transaction.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {transaction.user_info.username}
                      </div>
                      <div className="text-xs text-gray-500">
                        {transaction.user_info.email}
                      </div>
                      <div className="flex items-center space-x-1 mt-1">
                        {transaction.user_info.is_verified && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            ✓
                          </span>
                        )}
                        {transaction.user_info.kyc_verified && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            KYC
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{transaction.type_display}</div>
                    <div className="text-xs text-gray-500">{transaction.crypto_info.symbol}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusBadge(transaction.status)}`}>
                      {transaction.status_display}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-gray-900">
                      {formatAmount(transaction.amount)} {transaction.crypto_info.symbol}
                    </div>
                    {parseFloat(transaction.fee) > 0 && (
                      <div className="text-xs text-gray-500">
                        Комиссия: {formatAmount(transaction.fee)}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {formatDate(transaction.timestamp)}
                    </div>
                    {transaction.tx_hash && (
                      <div className="text-xs text-blue-600 font-mono">
                        {transaction.tx_hash.substring(0, 8)}...
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => openTransactionDetails(transaction.id)}
                      className="px-3 py-1 rounded text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                      title="Просмотреть детали транзакции"
                    >
                      👁️ Детали
                    </button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td className="px-4 py-8 text-center text-gray-500" colSpan={7}>
                    <p className="text-sm">Транзакции не найдены</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Пагинация */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between bg-white px-4 py-3 border border-gray-200 rounded-lg">
          <div className="flex items-center">
            <p className="text-sm text-gray-700">
              Показано <span className="font-medium">{transactions.length}</span> из{' '}
              <span className="font-medium">{pagination.count}</span> транзакций
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Назад
            </button>
            <span className="px-3 py-1 text-sm text-gray-700">
              Страница {pagination.page} из {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Вперед
            </button>
          </div>
        </div>
      )}

      {/* Transaction Details Modal */}
      {selectedTransactionId && (
        <TransactionDetailsModal
          transactionId={selectedTransactionId}
          isOpen={isModalOpen}
          onClose={closeTransactionDetails}
        />
      )}
    </div>
  );
}