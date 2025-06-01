'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import axios from 'axios';
import Image from 'next/image';
import Link from 'next/link';

// Типы данных
interface Investment {
  id: number;
  investment_id: string;
  user: number;
  wallet: {
    id: number;
    crypto: {
      id: number;
      name: string;
      symbol: string;
      icon: string;
    };
  };
  plan: {
    id: number;
    name: string;
    interest_rate: string;
    duration_value: number;
    duration_unit: string;
    early_withdrawal_allowed: boolean;
    early_withdrawal_fee: string;
  };
  amount: string;
  expected_return: string;
  actual_return: string | null;
  start_date: string;
  end_date: string;
  status: string;
  completed_date: string | null;
}

interface InvestmentStats {
  total_investments: number;
  active_investments: number;
  completed_investments: number;
  total_invested: {
    [key: string]: string;
  };
  total_expected_return: {
    [key: string]: string;
  };
  total_actual_return: {
    [key: string]: string;
  };
}

export const InvestmentsPage: React.FC = () => {
  const router = useRouter();
  const { tokens, user, isAuthenticated } = useAuthStore();
  const token = tokens?.access;

  const [investments, setInvestments] = useState<Investment[]>([]);
  const [stats, setStats] = useState<InvestmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [withdrawingId, setWithdrawingId] = useState<number | null>(null);
  const [withdrawSuccess, setWithdrawSuccess] = useState<boolean>(false);
  const [withdrawError, setWithdrawError] = useState<string | null>(null);

  // Получение инвестиций пользователя
  useEffect(() => {
    const fetchInvestments = async () => {
      // Проверяем наличие токена и авторизации
      if (!token || !isAuthenticated) {
        console.log('Нет токена или не авторизован, перенаправляем на страницу входа');
        router.push('/login?redirect=profile/investments');
        return;
      }
      
      // Дополнительная проверка на наличие токена в заголовках
      if (!token) {
        console.log('Токен отсутствует в заголовках');
        router.push('/login?redirect=profile/investments');
        return;
      }

      console.log('Начинаем загрузку данных инвестиций');
      try {
        setLoading(true);
        
        // Получаем инвестиции пользователя
        console.log('Запрашиваем инвестиции по URL:', `${process.env.NEXT_PUBLIC_API_URL}/crypto/investments/`);
        const investmentsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/investments/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Получен ответ по инвестициям:', investmentsResponse.data);
        
        // Получаем статистику по инвестициям
        console.log('Запрашиваем статистику по URL:', `${process.env.NEXT_PUBLIC_API_URL}/crypto/investments/stats/`);
        const statsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/investments/stats/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Получен ответ по статистике:', statsResponse.data);
        
        setInvestments(investmentsResponse.data);
        setStats(statsResponse.data);
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении данных инвестиций:', err);
        setError('Не удалось загрузить данные инвестиций. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    fetchInvestments();
  }, [token, router, withdrawSuccess]);

  // Форматирование даты
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Расчет оставшегося времени инвестиции
  const getRemainingTime = (investment: Investment): string => {
    if (investment.status !== 'active') {
      return '-';
    }
    
    const now = new Date();
    const endDate = new Date(investment.end_date);
    const diffTime = endDate.getTime() - now.getTime();
    
    if (diffTime <= 0) {
      return 'Завершается';
    }
    
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 30) {
      const diffMonths = Math.floor(diffDays / 30);
      return `${diffMonths} мес.`;
    }
    
    return `${diffDays} дн.`;
  };

  // Получение статуса инвестиции на русском
  const getStatusText = (status: string): string => {
    switch (status) {
      case 'active':
        return 'Активна';
      case 'completed':
        return 'Завершена';
      case 'cancelled':
        return 'Отменена';
      case 'withdrawn':
        return 'Досрочно выведена';
      default:
        return status;
    }
  };

  // Получение класса для статуса
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'active':
        return 'bg-green-500 bg-opacity-20 text-green-500';
      case 'completed':
        return 'bg-blue-500 bg-opacity-20 text-blue-500';
      case 'cancelled':
        return 'bg-red-500 bg-opacity-20 text-red-500';
      case 'withdrawn':
        return 'bg-yellow-500 bg-opacity-20 text-yellow-500';
      default:
        return 'bg-gray-500 bg-opacity-20 text-gray-500';
    }
  };

  // Досрочный вывод инвестиции
  const handleWithdrawEarly = async (investmentId: number) => {
    if (!token) {
      router.push('/login?redirect=profile/investments');
      return;
    }

    try {
      setWithdrawingId(investmentId);
      setWithdrawError(null);
      
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/investments/${investmentId}/withdraw_early/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setWithdrawSuccess(true);
      setWithdrawingId(null);
      
      // Сбрасываем флаг успеха через 3 секунды
      setTimeout(() => {
        setWithdrawSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error('Ошибка при досрочном выводе инвестиции:', err);
      setWithdrawError(err.response?.data?.error || 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.');
      setWithdrawingId(null);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка данных инвестиций...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg">
          <p className="text-red-500">{error}</p>
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-4 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (!loading && investments.length === 0) {
    return <div className="text-center text-gray-400 mt-8">У вас нет инвестиций</div>;
  }

  // Добавляем логи для отладки рендеринга
  console.log('Состояние перед рендерингом инвестиций:', { loading, error, investments, stats });

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Добавляем отладочную информацию */}
      <div className="bg-gray-800 p-4 mb-4 rounded">
        <p className="text-green-400">Debug Info:</p>
        <p>Loading: {loading ? 'true' : 'false'}</p>
        <p>Error: {error || 'none'}</p>
        <p>Investments Count: {investments.length}</p>
        <p>Stats: {stats ? 'Есть данные' : 'Нет данных'}</p>
        <p>Token: {token ? 'Есть токен' : 'Нет токена'}</p>
        <p>Authenticated: {isAuthenticated ? 'true' : 'false'}</p>
      </div>
      
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-purple-500">Мои инвестиции</h1>
        <Link 
          href="/profile/investments/new" 
          className="bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition"
        >
          Новая инвестиция
        </Link>
      </div>
      
      {withdrawSuccess && (
        <div className="bg-green-500 bg-opacity-20 p-4 rounded-lg mb-6 animate-pulse">
          <p className="text-green-500">Инвестиция успешно выведена! Средства зачислены на ваш кошелек.</p>
        </div>
      )}
      
      {withdrawError && (
        <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
          <p className="text-red-500">{withdrawError}</p>
        </div>
      )}
      
      {/* Статистика инвестиций */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h2 className="text-lg font-semibold mb-2">Всего инвестиций</h2>
            <p className="text-3xl font-bold text-purple-500">{stats.total_investments}</p>
            <div className="flex justify-between text-sm text-gray-400 mt-2">
              <span>Активных: {stats.active_investments}</span>
              <span>Завершенных: {stats.completed_investments}</span>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h2 className="text-lg font-semibold mb-2">Инвестировано</h2>
            <div className="space-y-2">
              {stats.total_invested && typeof stats.total_invested === 'object' ? (
                Object.entries(stats.total_invested).map(([symbol, amount]) => (
                  <p key={symbol} className="text-xl font-bold">
                    {typeof amount === 'object' && amount !== null
                      ? `${(amount as any).total_amount} (${(amount as any).count})`
                      : parseFloat(amount as any).toFixed(8)} <span className="text-gray-400">{symbol}</span>
                  </p>
                ))
              ) : (
                <p className="text-gray-400">Нет данных</p>
              )}
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h2 className="text-lg font-semibold mb-2">Ожидаемая прибыль</h2>
            <div className="space-y-2">
              {stats.total_expected_return && typeof stats.total_expected_return === 'object' ? (
                Object.entries(stats.total_expected_return).map(([symbol, amount]) => (
                  <p key={symbol} className="text-xl font-bold text-green-500">
                    {typeof amount === 'object' && amount !== null
                      ? `${(amount as any).total_amount} (${(amount as any).count})`
                      : parseFloat(amount as any).toFixed(8)} <span className="text-gray-400">{symbol}</span>
                  </p>
                ))
              ) : (
                <p className="text-gray-400">Нет данных</p>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Список инвестиций */}
      {investments.length > 0 ? (
        <div className="bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left">Инвестиция</th>
                  <th className="px-4 py-3 text-left">План</th>
                  <th className="px-4 py-3 text-right">Сумма</th>
                  <th className="px-4 py-3 text-right">Ожидаемый возврат</th>
                  <th className="px-4 py-3 text-center">Дата начала</th>
                  <th className="px-4 py-3 text-center">Осталось</th>
                  <th className="px-4 py-3 text-center">Статус</th>
                  <th className="px-4 py-3 text-center">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {investments.map((investment) => (
                  <tr key={investment.id} className="hover:bg-gray-750">
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        {investment.wallet.crypto.icon ? (
                          <Image 
                            src={`${process.env.NEXT_PUBLIC_API_URL}${investment.wallet.crypto.icon}`} 
                            alt={investment.wallet.crypto.symbol} 
                            width={24} 
                            height={24} 
                            className="rounded-full mr-2"
                          />
                        ) : (
                          <div className="w-6 h-6 bg-gray-700 rounded-full mr-2 flex items-center justify-center text-xs">
                            {investment.wallet.crypto.symbol.slice(0, 2)}
                          </div>
                        )}
                        <span className="text-sm">{investment.wallet.crypto.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium">{investment.plan.name}</p>
                        <p className="text-xs text-gray-400">{investment.plan.interest_rate}%</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-medium">
                        {parseFloat(investment.amount).toFixed(8)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {investment.wallet.crypto.symbol}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-medium text-green-400">
                        {parseFloat(investment.expected_return).toFixed(8)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {investment.wallet.crypto.symbol}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <p className="text-sm">{formatDate(investment.start_date)}</p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <p className="text-sm">{getRemainingTime(investment)}</p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusClass(investment.status)}`}>
                        {getStatusText(investment.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {investment.status === 'active' && investment.plan.early_withdrawal_allowed && (
                        <button
                          onClick={() => handleWithdrawEarly(investment.id)}
                          disabled={withdrawingId === investment.id}
                          className={`
                            text-xs px-3 py-1 rounded-lg transition
                            ${withdrawingId === investment.id
                              ? 'bg-gray-600 cursor-not-allowed'
                              : 'bg-yellow-600 hover:bg-yellow-700'}
                          `}
                        >
                          {withdrawingId === investment.id ? (
                            <span className="flex items-center">
                              <span className="animate-spin h-3 w-3 border-b-2 border-white mr-1"></span>
                              Вывод...
                            </span>
                          ) : (
                            'Вывести досрочно'
                          )}
                        </button>
                      )}
                      
                      {investment.status === 'completed' && (
                        <span className="text-xs text-gray-400">
                          Завершена {investment.completed_date ? formatDate(investment.completed_date) : ''}
                        </span>
                      )}
                      
                      {investment.status === 'withdrawn' && (
                        <span className="text-xs text-gray-400">
                          Выведена {investment.completed_date ? formatDate(investment.completed_date) : ''}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl p-8 text-center">
          <p className="text-lg mb-4">У вас пока нет инвестиций</p>
          <p className="text-sm text-gray-400 mb-6">
            Создайте свою первую инвестицию и начните получать пассивный доход
          </p>
          <Link href="/profile/investments/new" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
            Создать инвестицию
          </Link>
        </div>
      )}
    </div>
  );
};
