'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';

interface Transaction {
  id: string;
  type: 'deposit' | 'withdrawal' | 'exchange';
  amount: number;
  currency: string;
  status: 'completed' | 'pending' | 'failed';
  date: string;
}

interface Balance {
  currency: string;
  amount: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // Имитация загрузки данных
    const fetchDashboardData = async () => {
      try {
        // В реальном приложении здесь будет API запрос
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setBalances([
          { currency: 'BTC', amount: 0.5 },
          { currency: 'ETH', amount: 2.3 },
          { currency: 'USDT', amount: 1000 }
        ]);
        
        setTransactions([
          {
            id: '1',
            type: 'deposit',
            amount: 0.1,
            currency: 'BTC',
            status: 'completed',
            date: '2024-01-15'
          },
          {
            id: '2',
            type: 'withdrawal',
            amount: 0.5,
            currency: 'ETH',
            status: 'pending',
            date: '2024-01-14'
          },
          {
            id: '3',
            type: 'exchange',
            amount: 100,
            currency: 'USDT',
            status: 'failed',
            date: '2024-01-13'
          }
        ]);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [isAuthenticated, router]);

  const getTotalBalance = () => {
    // В реальном приложении здесь будет конвертация в одну валюту
    return balances.reduce((total, balance) => total + balance.amount, 0);
  };

  const getStatusColor = (status: Transaction['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'pending':
        return 'text-yellow-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTransactionIcon = (type: Transaction['type']) => {
    switch (type) {
      case 'deposit':
        return '↓';
      case 'withdrawal':
        return '↑';
      case 'exchange':
        return '↔';
      default:
        return '•';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-4">
            Добро пожаловать, {user?.username}!
          </h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h2 className="text-lg font-medium text-blue-900">Общий баланс</h2>
              <p className="text-2xl font-bold text-blue-600">${getTotalBalance().toFixed(2)}</p>
            </div>
            
            {balances.map((balance) => (
              <div key={balance.currency} className="bg-gray-50 p-4 rounded-lg">
                <h2 className="text-lg font-medium text-gray-900">{balance.currency}</h2>
                <p className="text-2xl font-bold text-gray-900">{balance.amount}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Последние транзакции</h2>
            <div className="space-y-4">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getTransactionIcon(transaction.type)}</span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {transaction.amount} {transaction.currency}
                      </p>
                      <p className="text-sm text-gray-500">{transaction.date}</p>
                    </div>
                  </div>
                  <span className={`font-medium ${getStatusColor(transaction.status)}`}>
                    {transaction.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-4">
            <button
              onClick={() => router.push('/exchange')}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Обмен валют
            </button>
            <button
              onClick={() => router.push('/transactions')}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors"
            >
              Все транзакции
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 