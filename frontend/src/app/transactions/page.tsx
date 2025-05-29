'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import axios from 'axios';
import Link from 'next/link';

// Типы данных
interface Transaction {
  id: number;
  transaction_id: string;
  type: string;
  amount: string;
  status: string;
  timestamp: string;
  crypto: {
    id: number;
    name: string;
    symbol: string;
  };
  details: any;
}

export default function TransactionsPage() {
  const router = useRouter();
  const { tokens } = useAuthStore();
  const token = tokens?.access;

  // Состояния
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  // Загрузка данных
  useEffect(() => {
    const fetchTransactions = async () => {
      if (!token) {
        router.push('/login?redirect=transactions');
        return;
      }

      try {
        setLoading(true);
        
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/transactions/?page=${currentPage}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setTransactions(response.data.results);
        setTotalPages(Math.ceil(response.data.count / 10)); // Предполагаем, что на странице 10 транзакций
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении транзакций:', err);
        setError('Не удалось загрузить историю транзакций. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [token, router, currentPage]);

  // Получение типа транзакции на русском
  const getTransactionType = (type: string): string => {
    switch (type) {
      case 'deposit':
        return 'Пополнение';
      case 'withdrawal':
        return 'Вывод';
      case 'exchange':
        return 'Обмен';
      case 'transfer':
        return 'Перевод';
      case 'fee':
        return 'Комиссия';
      default:
        return 'Транзакция';
    }
  };

  // Получение статуса транзакции на русском
  const getTransactionStatus = (status: string): string => {
    switch (status) {
      case 'pending':
        return 'В обработке';
      case 'completed':
        return 'Завершена';
      case 'failed':
        return 'Ошибка';
      case 'cancelled':
        return 'Отменена';
      default:
        return 'Неизвестно';
    }
  };

  // Получение цвета статуса
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending':
        return 'text-yellow-400';
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'cancelled':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  };

  // Форматирование даты
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка истории транзакций...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">История транзакций</h1>
        
        {error && (
          <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
            <p className="text-red-500">{error}</p>
          </div>
        )}
        
        {transactions.length === 0 ? (
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg text-center">
            <p className="text-gray-400 mb-4">У вас пока нет транзакций</p>
            <div className="flex flex-col space-y-3 sm:flex-row sm:space-y-0 sm:space-x-3 justify-center">
              <Link href="/funds/deposit" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
                Пополнить
              </Link>
              <Link href="/exchange" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
                Обменять
              </Link>
            </div>
          </div>
        ) : (
          <>
            <div className="bg-gray-800 rounded-xl overflow-hidden shadow-lg">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-700">
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Дата</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Тип</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Сумма</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Статус</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {transactions.map((transaction) => (
                      <tr 
                        key={transaction.id} 
                        className="hover:bg-gray-700 cursor-pointer" 
                        onClick={() => router.push(`/transactions/${transaction.id}`)}
                      >
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {formatDate(transaction.timestamp)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">
                          {getTransactionType(transaction.type)}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">
                          {transaction.amount} {transaction.crypto.symbol}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`${getStatusColor(transaction.status)}`}>
                            {getTransactionStatus(transaction.status)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            {/* Пагинация */}
            {totalPages > 1 && (
              <div className="flex justify-center mt-6">
                <div className="flex space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className={`px-3 py-1 rounded ${
                      currentPage === 1
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                  >
                    &laquo;
                  </button>
                  
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-1 rounded ${
                        currentPage === page
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-700 text-white hover:bg-gray-600'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className={`px-3 py-1 rounded ${
                      currentPage === totalPages
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                  >
                    &raquo;
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
