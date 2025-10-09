"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

type TransactionRow = {
  id: number | string;
  user: {
    id: number | string;
    email: string;
    username: string;
  };
  transaction_id: string;
  type: string;
  status: string;
  amount: string;
  fee: string;
  crypto: {
    id: number | string;
    name: string;
    symbol: string;
  };
  tx_hash?: string;
  block_number?: number;
  timestamp: string;
  updated_at: string;
};

export default function TransactionsTable() {
  const [transactions, setTransactions] = useState<TransactionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCrypto, setFilterCrypto] = useState("all");
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/transactions/transactions/", { headers });
      const data = res?.data ?? res;
      setTransactions(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить транзакции");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [getAuthHeaders]);

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch = 
      tx.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tx.tx_hash && tx.tx_hash.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesType = 
      filterType === "all" ||
      tx.type === filterType;

    const matchesStatus = 
      filterStatus === "all" ||
      tx.status === filterStatus;

    const matchesCrypto = 
      filterCrypto === "all" ||
      tx.crypto.symbol.toLowerCase() === filterCrypto.toLowerCase();

    return matchesSearch && matchesType && matchesStatus && matchesCrypto;
  });

  const updateStatus = async (txId: string | number, newStatus: string) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/transactions/transactions/${txId}/`, 
        { status: newStatus }, 
        { headers }
      );
      await fetchTransactions();
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить статус транзакции");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return "bg-green-100 text-green-800";
      case 'pending': return "bg-yellow-100 text-yellow-800";
      case 'processing': return "bg-blue-100 text-blue-800";
      case 'failed': return "bg-red-100 text-red-800";
      case 'cancelled': return "bg-gray-100 text-gray-800";
      case 'refunded': return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'deposit': return "bg-green-100 text-green-800";
      case 'withdrawal': return "bg-red-100 text-red-800";
      case 'exchange': return "bg-blue-100 text-blue-800";
      case 'transfer': return "bg-purple-100 text-purple-800";
      case 'fee': return "bg-orange-100 text-orange-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) return <div className="py-4">Загрузка транзакций…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      {/* Фильтры и поиск */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/20 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Поиск по ID, email, hash..."
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
          <option value="deposit">Депозит</option>
          <option value="withdrawal">Вывод</option>
          <option value="exchange">Обмен</option>
          <option value="transfer">Перевод</option>
          <option value="fee">Комиссия</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все статусы</option>
          <option value="pending">В ожидании</option>
          <option value="processing">В обработке</option>
          <option value="completed">Завершено</option>
          <option value="failed">Ошибка</option>
          <option value="cancelled">Отменено</option>
          <option value="refunded">Возвращено</option>
        </select>
        <select
          value={filterCrypto}
          onChange={(e) => setFilterCrypto(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все валюты</option>
          {Array.from(new Set(transactions.map(tx => tx.crypto.symbol))).map(symbol => (
            <option key={symbol} value={symbol}>{symbol}</option>
          ))}
        </select>
        <button
          onClick={fetchTransactions}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90"
        >
          Обновить
        </button>
      </div>

      {/* Таблица */}
      <div className="w-full overflow-x-auto border rounded-md">
        <table className="min-w-[1400px] w-full text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="text-left p-3">ID</th>
              <th className="text-left p-3">Пользователь</th>
              <th className="text-left p-3">Тип</th>
              <th className="text-left p-3">Статус</th>
              <th className="text-left p-3">Сумма</th>
              <th className="text-left p-3">Комиссия</th>
              <th className="text-left p-3">Валюта</th>
              <th className="text-left p-3">Hash</th>
              <th className="text-left p-3">Дата</th>
              <th className="text-left p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.map((tx) => (
              <tr key={tx.id} className="border-t hover:bg-muted/40">
                <td className="p-3">
                  <div className="font-mono text-xs">
                    {tx.transaction_id.slice(0, 8)}...
                  </div>
                </td>
                <td className="p-3">
                  <div>
                    <div className="font-medium">{tx.user.email}</div>
                    <div className="text-xs text-muted-foreground">{tx.user.username}</div>
                  </div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getTypeColor(tx.type)}`}>
                    {tx.type}
                  </span>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(tx.status)}`}>
                    {tx.status}
                  </span>
                </td>
                <td className="p-3">
                  <div className="font-mono">{tx.amount}</div>
                </td>
                <td className="p-3">
                  <div className="font-mono text-xs">{tx.fee}</div>
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-1">
                    <span className="font-mono">{tx.crypto.symbol}</span>
                    <span className="text-xs text-muted-foreground">({tx.crypto.name})</span>
                  </div>
                </td>
                <td className="p-3">
                  {tx.tx_hash ? (
                    <div className="font-mono text-xs">
                      {tx.tx_hash.slice(0, 10)}...
                    </div>
                  ) : "—"}
                </td>
                <td className="p-3">
                  <div className="text-xs">
                    <div>{tx.timestamp.slice(0, 10)}</div>
                    <div className="text-muted-foreground">{tx.timestamp.slice(11, 19)}</div>
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex gap-2">
                    {tx.status === 'pending' && (
                      <button
                        onClick={() => updateStatus(tx.id, 'processing')}
                        className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                      >
                        В обработку
                      </button>
                    )}
                    {tx.status === 'processing' && (
                      <>
                        <button
                          onClick={() => updateStatus(tx.id, 'completed')}
                          className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs hover:bg-green-200"
                        >
                          Завершить
                        </button>
                        <button
                          onClick={() => updateStatus(tx.id, 'failed')}
                          className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                        >
                          Отклонить
                        </button>
                      </>
                    )}
                    {(tx.status === 'pending' || tx.status === 'processing') && (
                      <button
                        onClick={() => updateStatus(tx.id, 'cancelled')}
                        className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs hover:bg-gray-200"
                      >
                        Отменить
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filteredTransactions.length === 0 && (
              <tr>
                <td className="p-4 text-center text-muted-foreground" colSpan={10}>
                  Транзакции не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        Показано {filteredTransactions.length} из {transactions.length} транзакций
      </div>
    </div>
  );
}
