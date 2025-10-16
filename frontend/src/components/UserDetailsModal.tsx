"use client";

import React, { useState, useEffect } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

interface UserWallet {
  id: number;
  currency: {
    id: number;
    name: string;
    symbol: string;
    icon?: string;
  };
  balance: string;
  available_balance: string;
  locked_balance: string;
  is_active: boolean;
}

interface UserTransaction {
  id: number;
  transaction_id: string;
  type: string;
  status: string;
  amount: string;
  fee: string;
  crypto: {
    name: string;
    symbol: string;
  };
  timestamp: string;
  tx_hash?: string;
}

interface UserDetails {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  phone_number?: string;
  is_verified: boolean;
  kyc_verified: boolean;
  telegram_id?: string;
  date_joined: string;
  last_login?: string;
  is_site_admin: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_active: boolean;
  wallets: UserWallet[];
  transactions: UserTransaction[];
  total_balance_usd: number;
}

interface UserDetailsModalProps {
  userId: number | string;
  isOpen: boolean;
  onClose: () => void;
}

export default function UserDetailsModal({ userId, isOpen, onClose }: UserDetailsModalProps) {
  const [userDetails, setUserDetails] = useState<UserDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'wallets' | 'transactions'>('info');
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchUserDetails = async () => {
    if (!userId) return;
    
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get(`/accounts/users/${userId}/detailed_info/`, { headers });
      const data = res?.data ?? res;
      setUserDetails(data);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить данные пользователя");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && userId) {
      fetchUserDetails();
    }
  }, [isOpen, userId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatBalance = (balance: string) => {
    return parseFloat(balance).toFixed(8);
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'processing': 'bg-blue-100 text-blue-800',
      'cancelled': 'bg-gray-100 text-gray-800',
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
    };
    
    return typeIcons[type] || '📝';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👤</span>
            <h2 className="text-xl font-semibold">
              {userDetails ? `Детали пользователя: ${userDetails.username}` : 'Загрузка...'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-200 text-2xl font-bold transition-colors"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-col h-full max-h-[calc(90vh-80px)]">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Загрузка данных пользователя...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={fetchUserDetails}
                  className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Попробовать снова
                </button>
              </div>
            </div>
          )}

          {userDetails && (
            <>
              {/* Tabs */}
              <div className="border-b border-gray-200 px-6">
                <nav className="flex space-x-8">
                  {[
                    { key: 'info', label: 'Информация', icon: '📋' },
                    { key: 'wallets', label: 'Кошельки', icon: '💰' },
                    { key: 'transactions', label: 'Транзакции', icon: '📊' },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as any)}
                      className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.key
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <span className="mr-2">{tab.icon}</span>
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeTab === 'info' && (
                  <div className="space-y-6">
                    {/* Basic Info */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold mb-4 text-gray-900">Основная информация</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-600">ID пользователя</label>
                          <p className="text-gray-900">{userDetails.id}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Email</label>
                          <p className="text-gray-900">{userDetails.email}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Username</label>
                          <p className="text-gray-900">{userDetails.username}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Полное имя</label>
                          <p className="text-gray-900">
                            {userDetails.first_name && userDetails.last_name 
                              ? `${userDetails.first_name} ${userDetails.last_name}`
                              : userDetails.first_name || userDetails.last_name || "Не указано"
                            }
                          </p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Телефон</label>
                          <p className="text-gray-900">{userDetails.phone_number || "Не указан"}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Telegram ID</label>
                          <p className="text-gray-900">{userDetails.telegram_id || "Не указан"}</p>
                        </div>
                      </div>
                    </div>

                    {/* Status Info */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold mb-4 text-gray-900">Статус и права</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Статус аккаунта</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            userDetails.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {userDetails.is_active ? 'Активен' : 'Заблокирован'}
                          </span>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Верификация email</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            userDetails.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {userDetails.is_verified ? 'Подтвержден' : 'Не подтвержден'}
                          </span>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">KYC верификация</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            userDetails.kyc_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {userDetails.kyc_verified ? 'Пройдена' : 'Не пройдена'}
                          </span>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Роли</label>
                          <div className="flex flex-wrap gap-1">
                            {userDetails.is_superuser && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                                Суперпользователь
                              </span>
                            )}
                            {userDetails.is_staff && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                Персонал
                              </span>
                            )}
                            {userDetails.is_site_admin && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                Администратор сайта
                              </span>
                            )}
                            {!userDetails.is_superuser && !userDetails.is_staff && !userDetails.is_site_admin && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                Пользователь
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Dates */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold mb-4 text-gray-900">Даты</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Дата регистрации</label>
                          <p className="text-gray-900">{formatDate(userDetails.date_joined)}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Последний вход</label>
                          <p className="text-gray-900">
                            {userDetails.last_login ? formatDate(userDetails.last_login) : "Никогда"}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Balance Summary */}
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
                      <h3 className="text-lg font-semibold mb-2 text-gray-900">Общий баланс</h3>
                      <p className="text-2xl font-bold text-green-600">
                        ${userDetails.total_balance_usd.toFixed(2)} USD
                      </p>
                      <p className="text-sm text-gray-600">Общая стоимость всех активов</p>
                    </div>
                  </div>
                )}

                {activeTab === 'wallets' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Кошельки пользователя</h3>
                      <span className="text-sm text-gray-600">
                        Всего кошельков: {userDetails.wallets.length}
                      </span>
                    </div>
                    
                    {userDetails.wallets.length === 0 ? (
                      <div className="text-center py-8">
                        <p className="text-gray-500">У пользователя нет кошельков</p>
                      </div>
                    ) : (
                      <div className="grid gap-4">
                        {userDetails.wallets.map((wallet) => (
                          <div key={wallet.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                {wallet.currency.icon && (
                                  <img 
                                    src={wallet.currency.icon} 
                                    alt={wallet.currency.symbol}
                                    className="w-8 h-8 rounded-full"
                                  />
                                )}
                                <div>
                                  <h4 className="font-medium text-gray-900">{wallet.currency.name}</h4>
                                  <p className="text-sm text-gray-500">{wallet.currency.symbol}</p>
                                </div>
                              </div>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                wallet.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {wallet.is_active ? 'Активен' : 'Неактивен'}
                              </span>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-4 text-sm">
                              <div>
                                <label className="block text-gray-600">Общий баланс</label>
                                <p className="font-medium text-gray-900">{formatBalance(wallet.balance)}</p>
                              </div>
                              <div>
                                <label className="block text-gray-600">Доступно</label>
                                <p className="font-medium text-green-600">{formatBalance(wallet.available_balance)}</p>
                              </div>
                              <div>
                                <label className="block text-gray-600">Заблокировано</label>
                                <p className="font-medium text-orange-600">{formatBalance(wallet.locked_balance)}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'transactions' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Последние транзакции</h3>
                      <span className="text-sm text-gray-600">
                        Показано: {userDetails.transactions.length} транзакций
                      </span>
                    </div>
                    
                    {userDetails.transactions.length === 0 ? (
                      <div className="text-center py-8">
                        <p className="text-gray-500">У пользователя нет транзакций</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {userDetails.transactions.map((transaction) => (
                          <div key={transaction.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-3">
                                <span className="text-2xl">{getTypeIcon(transaction.type)}</span>
                                <div>
                                  <h4 className="font-medium text-gray-900">
                                    {transaction.type === 'deposit' && 'Пополнение'}
                                    {transaction.type === 'withdrawal' && 'Вывод'}
                                    {transaction.type === 'exchange' && 'Обмен'}
                                    {transaction.type === 'transfer' && 'Перевод'}
                                    {transaction.type === 'fee' && 'Комиссия'}
                                  </h4>
                                  <p className="text-sm text-gray-500">{transaction.crypto.name}</p>
                                </div>
                              </div>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(transaction.status)}`}>
                                {transaction.status === 'pending' && 'В ожидании'}
                                {transaction.status === 'completed' && 'Завершено'}
                                {transaction.status === 'failed' && 'Ошибка'}
                                {transaction.status === 'processing' && 'В обработке'}
                                {transaction.status === 'cancelled' && 'Отменено'}
                              </span>
                            </div>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <label className="block text-gray-600">Сумма</label>
                                <p className="font-medium text-gray-900">
                                  {formatBalance(transaction.amount)} {transaction.crypto.symbol}
                                </p>
                              </div>
                              <div>
                                <label className="block text-gray-600">Комиссия</label>
                                <p className="font-medium text-gray-900">
                                  {formatBalance(transaction.fee)} {transaction.crypto.symbol}
                                </p>
                              </div>
                              <div>
                                <label className="block text-gray-600">Дата</label>
                                <p className="font-medium text-gray-900">{formatDate(transaction.timestamp)}</p>
                              </div>
                              <div>
                                <label className="block text-gray-600">ID транзакции</label>
                                <p className="font-mono text-xs text-gray-600 break-all">
                                  {transaction.transaction_id.substring(0, 8)}...
                                </p>
                              </div>
                            </div>
                            
                            {transaction.tx_hash && (
                              <div className="mt-2 pt-2 border-t border-gray-100">
                                <label className="block text-xs text-gray-600">Hash транзакции</label>
                                <p className="font-mono text-xs text-blue-600 break-all">{transaction.tx_hash}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
