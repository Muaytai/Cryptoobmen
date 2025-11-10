'use client';

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import Link from 'next/link';

interface Transaction {
  id: number;
  transaction_id: string;
  amount: string;
  crypto: {
    symbol: string;
  };
  type: string;
  status: string;
  status_display: string;
  timestamp: string;
  updated_at: string;
}

const TransactionsPage = () => {
  const { tokens, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const fetchTransactions = async () => {
        try {
          const response = await api.get('/transactions/history/');
          const transactionsData = Array.isArray(response) ? response : response.results || [];
          setTransactions(transactionsData);
        } catch (err: any) {
          setError(err.message || 'Не удалось загрузить историю транзакций.');
        } finally {
          setLoading(false);
        }
      };
      fetchTransactions();
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
    }
  }, [authLoading, isAuthenticated, tokens]);

  if (authLoading || loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка истории транзакций...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-xl text-white">Пожалуйста, <Link href="/login" className="text-purple-400 hover:underline">войдите</Link>, чтобы просмотреть историю транзакций.</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-xl text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-white">История транзакций</h1>
      {transactions.length === 0 ? (
        <p className="text-gray-400">У вас пока нет транзакций.</p>
      ) : (
        <div className="bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <table className="min-w-full text-white">
            <thead className="bg-gray-700">
              <tr>
                <th className="py-3 px-4 text-left">ID</th>
                <th className="py-3 px-4 text-left">Тип</th>
                <th className="py-3 px-4 text-left">Сумма</th>
                <th className="py-3 px-4 text-left">Статус</th>
                <th className="py-3 px-4 text-left">Дата</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {transactions.map((tx) => (
                <tr key={tx.transaction_id} className="hover:bg-gray-750">
                  <td className="py-3 px-4 font-mono text-sm">{tx.transaction_id.slice(0, 12)}...</td>
                  <td className="py-3 px-4">{tx.type}</td>
                  <td className="py-3 px-4">{parseFloat(tx.amount).toFixed(8)} {tx.crypto.symbol}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      tx.status === 'completed' ? 'bg-green-900 text-green-300' :
                      tx.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                      tx.status === 'processing' ? 'bg-blue-900 text-blue-300' :
                      tx.status === 'cancelled' ? 'bg-gray-900 text-gray-300' :
                      tx.status === 'failed' ? 'bg-red-900 text-red-300' :
                      'bg-gray-900 text-gray-300'
                    }`}>
                      {tx.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">{new Date(tx.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TransactionsPage;
