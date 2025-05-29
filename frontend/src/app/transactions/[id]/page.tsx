'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import axios from 'axios';
import Link from 'next/link';

// Типы данных
interface TransactionDetails {
  id: number;
  transaction_id: string;
  type: string;
  status: string;
  amount: string;
  fee: string;
  timestamp: string;
  updated_at: string;
  crypto: {
    id: number;
    name: string;
    symbol: string;
  };
  tx_hash: string | null;
  notes: string | null;
  details: any;
}

export default function TransactionDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const { tokens } = useAuthStore();
  const token = tokens?.access;
  const transactionId = params.id;

  // Состояния
  const [transaction, setTransaction] = useState<TransactionDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Загрузка данных
  useEffect(() => {
    const fetchTransactionDetails = async () => {
      if (!token) {
        router.push('/login?redirect=transactions');
        return;
      }

      try {
        setLoading(true);
        
        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/api/transactions/${transactionId}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setTransaction(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении деталей транзакции:', err);
        setError('Не удалось загрузить детали транзакции. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    if (transactionId) {
      fetchTransactionDetails();
    }
  }, [token, router, transactionId]);

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
        return 'bg-yellow-400 bg-opacity-20 text-yellow-400';
      case 'completed':
        return 'bg-green-400 bg-opacity-20 text-green-400';
      case 'failed':
        return 'bg-red-400 bg-opacity-20 text-red-400';
      case 'cancelled':
        return 'bg-gray-400 bg-opacity-20 text-gray-400';
      default:
        return 'bg-gray-400 bg-opacity-20 text-gray-400';
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
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Отображение дополнительных деталей в зависимости от типа транзакции
  const renderTransactionDetails = () => {
    if (!transaction) return null;

    switch (transaction.type) {
      case 'deposit':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Детали пополнения</h3>
            {transaction.details?.payment_method && (
              <div className="flex justify-between">
                <span className="text-gray-400">Способ оплаты:</span>
                <span>{transaction.details.payment_method}</span>
              </div>
            )}
            {transaction.details?.card_last4 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Карта:</span>
                <span>**** **** **** {transaction.details.card_last4}</span>
              </div>
            )}
          </div>
        );
      
      case 'withdrawal':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Детали вывода</h3>
            {transaction.details?.address && (
              <div className="flex justify-between">
                <span className="text-gray-400">Адрес:</span>
                <span className="break-all">{transaction.details.address}</span>
              </div>
            )}
            {transaction.details?.network && (
              <div className="flex justify-between">
                <span className="text-gray-400">Сеть:</span>
                <span>{transaction.details.network}</span>
              </div>
            )}
            {transaction.details?.txid && (
              <div className="flex justify-between">
                <span className="text-gray-400">ID транзакции:</span>
                <span className="break-all">{transaction.details.txid}</span>
              </div>
            )}
          </div>
        );
      
      case 'exchange':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Детали обмена</h3>
            {transaction.details?.from_amount && transaction.details?.from_crypto && (
              <div className="flex justify-between">
                <span className="text-gray-400">Отдано:</span>
                <span>{transaction.details.from_amount} {transaction.details.from_crypto}</span>
              </div>
            )}
            {transaction.details?.to_amount && transaction.details?.to_crypto && (
              <div className="flex justify-between">
                <span className="text-gray-400">Получено:</span>
                <span>{transaction.details.to_amount} {transaction.details.to_crypto}</span>
              </div>
            )}
            {transaction.details?.rate && (
              <div className="flex justify-between">
                <span className="text-gray-400">Курс обмена:</span>
                <span>1 {transaction.details.from_crypto} = {transaction.details.rate} {transaction.details.to_crypto}</span>
              </div>
            )}
          </div>
        );
      
      case 'investment':
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Детали инвестиции</h3>
            {transaction.details?.plan_name && (
              <div className="flex justify-between">
                <span className="text-gray-400">План:</span>
                <span>{transaction.details.plan_name}</span>
              </div>
            )}
            {transaction.details?.term_days && (
              <div className="flex justify-between">
                <span className="text-gray-400">Срок:</span>
                <span>{transaction.details.term_days} дней</span>
              </div>
            )}
            {transaction.details?.interest_rate && (
              <div className="flex justify-between">
                <span className="text-gray-400">Процентная ставка:</span>
                <span>{transaction.details.interest_rate}%</span>
              </div>
            )}
            {transaction.details?.end_date && (
              <div className="flex justify-between">
                <span className="text-gray-400">Дата окончания:</span>
                <span>{formatDate(transaction.details.end_date)}</span>
              </div>
            )}
          </div>
        );
      
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка деталей транзакции...</p>
      </div>
    );
  }

  if (error || !transaction) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-500 bg-opacity-20 p-6 rounded-xl text-center">
            <h1 className="text-2xl font-bold mb-4 text-red-400">Ошибка</h1>
            <p className="mb-6 text-gray-300">{error || 'Транзакция не найдена'}</p>
            <Link href="/transactions" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
              Вернуться к списку транзакций
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6 flex items-center">
          <Link href="/transactions" className="text-purple-400 hover:text-purple-300 flex items-center">
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Назад к списку
          </Link>
        </div>
        
        <h1 className="text-2xl font-bold mb-6">
          {getTransactionType(transaction.type)} #{transaction.id}
        </h1>
        
        <div className="bg-gray-800 rounded-xl p-6 shadow-lg mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <span className="text-gray-400 text-sm">Статус</span>
              <div className={`mt-1 px-3 py-1 rounded-full inline-block ${getStatusColor(transaction.status)}`}>
                {getTransactionStatus(transaction.status)}
              </div>
            </div>
            <div className="text-right">
              <span className="text-gray-400 text-sm">Сумма</span>
              <div className="mt-1 text-xl font-bold">
                {transaction.amount} {transaction.crypto.symbol}
              </div>
            </div>
          </div>
          
          <div className="space-y-4 border-t border-gray-700 pt-4">
            <div className="flex justify-between">
              <span className="text-gray-400">ID транзакции:</span>
              <span>{transaction.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Дата создания:</span>
              <span>{formatDate(transaction.timestamp)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Дата обновления:</span>
              <span>{formatDate(transaction.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Криптовалюта:</span>
              <span>{transaction.crypto.name} ({transaction.crypto.symbol})</span>
            </div>
            {transaction.fee && parseFloat(transaction.fee) > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Комиссия:</span>
                <span>{transaction.fee} {transaction.crypto.symbol}</span>
              </div>
            )}
          </div>
          
          {transaction.details && (
            <div className="mt-6 border-t border-gray-700 pt-4">
              {renderTransactionDetails()}
            </div>
          )}
        </div>
        
        <div className="flex justify-center">
          <Link href="/transactions" className="bg-gray-700 text-white py-2 px-6 rounded-lg hover:bg-gray-600 transition">
            Вернуться к списку транзакций
          </Link>
        </div>
      </div>
    </div>
  );
}
