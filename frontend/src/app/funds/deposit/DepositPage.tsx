'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter } from 'next/navigation';

// --- Interfaces ---
interface DepositInfo {
  system_wallet_address: string;
  memo: string;
}

interface Currency {
    id: number;
    name: string;
    symbol: string;
    icon: string;
    networks: string[]; // e.g., ['TRC20', 'BEP20']
}

type DepositStatus = 'loading' | 'waiting' | 'completed' | 'error';

// --- Component ---
export const DepositPage: React.FC = () => {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  // --- State ---
  const [error, setError] = useState<string | null>(null);
  const [depositInfo, setDepositInfo] = useState<DepositInfo | null>(null);
  const [status, setStatus] = useState<DepositStatus>('loading');

  // Hardcoded for now, as we only support USDT on TRC20
  const selectedCurrency: Currency = {
      id: 1, // Assuming USDT has id 1, this should ideally be dynamic
      name: 'Tether',
      symbol: 'USDT',
      icon: '/path/to/usdt-icon.png', // Add a real path later
      networks: ['TRC20'],
  };
  const selectedNetwork = 'TRC20';

  const fetchDepositInfo = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const response = await api.post('/crypto/deposit/info/', {
        currency_symbol: selectedCurrency.symbol,
        network: selectedNetwork,
      });
      setDepositInfo({
          system_wallet_address: response.data.address,
          memo: response.data.memo,
      });
      setStatus('waiting');
    } catch (err: any) {
      console.error('Failed to fetch deposit info:', err);
      setError(err.message || 'Не удалось получить данные для пополнения.');
      setStatus('error');
    }
  }, [selectedCurrency.symbol, selectedNetwork]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchDepositInfo();
    }
  }, [isAuthenticated, fetchDepositInfo]);

  useEffect(() => {
    if (status !== 'waiting' || !depositInfo?.memo) {
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const response = await api.get(`/crypto/deposit/status/${depositInfo.memo}/`);
        if (response.data.status === 'used') {
          setStatus('completed');
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Failed to check deposit status:', err);
        // Optional: handle error, maybe stop polling
      }
    }, 7000); // Poll every 7 seconds

    return () => clearInterval(intervalId);
  }, [status, depositInfo]);

  if (authLoading) {
    return <div>Проверка авторизации...</div>;
  }

  if (!isAuthenticated) {
    router.push('/login');
    return null;
  }
  
  const renderContent = () => {
    switch (status) {
      case 'loading':
        return <div>Загрузка данных для пополнения...</div>;
      case 'error':
        return <div className="text-red-500">Ошибка: {error}</div>;
      case 'completed':
        return (
          <div className="text-center p-8 bg-green-900 rounded-lg">
            <h2 className="text-2xl font-bold text-green-300 mb-4">Пополнение успешно!</h2>
            <p className="text-green-400">Ваш баланс был успешно пополнен.</p>
            <p className="text-sm text-gray-400 mt-2">(Memo: {depositInfo?.memo})</p>
          </div>
        );
      case 'waiting':
        return (
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md">
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-400">Адрес кошелька для пополнения ({selectedNetwork}):</label>
                <input
                    type="text"
                    readOnly
                    value={depositInfo?.system_wallet_address || ''}
                    className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-2"
                />
            </div>
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-400">MEMO (обязательно для зачисления):</label>
                <input
                    type="text"
                    readOnly
                    value={depositInfo?.memo || ''}
                    className="mt-1 block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-2"
                />
            </div>
            <div className="bg-yellow-900 border-l-4 border-yellow-500 text-yellow-200 p-4 rounded-md">
                <h4 className="font-bold">ВАЖНО!</h4>
                <p>Отправляйте только USDT в сети TRC20. Обязательно укажите MEMO в комментарии к транзакции. Средства, отправленные без MEMO, могут быть утеряны.</p>
            </div>
            <div className="mt-4 text-center text-blue-400 animate-pulse">
                Ожидаем поступления средств...
            </div>
          </div>
        );
    }
  };

  return (
    <div className="container mx-auto p-4 flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-4">Пополнение USDT (TRC20)</h1>
      {renderContent()}
    </div>
  );
};

export default DepositPage;
