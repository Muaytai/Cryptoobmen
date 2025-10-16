"use client";

import React, { useState, useEffect } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

interface TransactionDetails {
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
  exchange_info?: {
    from_crypto: { symbol: string; name: string };
    to_crypto: { symbol: string; name: string };
    from_amount: string;
    to_amount: string;
    rate: string;
    fee_percentage: string;
    fee_amount: string;
  };
  deposit_info?: {
    address: string;
    confirmed: boolean;
    confirmation_date?: string;
  };
  withdrawal_info?: {
    destination_address: string;
    memo?: string;
    is_email_confirmed: boolean;
    confirmed_by_admin: boolean;
    rejected_reason?: string;
    confirmation_date?: string;
    refunded: boolean;
  };
}

interface TransactionDetailsModalProps {
  transactionId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function TransactionDetailsModal({ transactionId, isOpen, onClose }: TransactionDetailsModalProps) {
  const [transactionDetails, setTransactionDetails] = useState<TransactionDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'details' | 'user'>('info');
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchTransactionDetails = async () => {
    if (!transactionId) return;
    
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get(`/transactions/transactions/${transactionId}/`, { headers });
      const data = res?.data ?? res;
      setTransactionDetails(data);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить данные транзакции");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && transactionId) {
      fetchTransactionDetails();
    }
  }, [isOpen, transactionId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getTypeIcon(transactionDetails?.type || '')}</span>
            <h2 className="text-xl font-semibold">
              {transactionDetails ? `Детали транзакции: ${transactionDetails.transaction_id.substring(0, 8)}...` : 'Загрузка...'}
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
                <p className="text-gray-600">Загрузка данных транзакции...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={fetchTransactionDetails}
                  className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Попробовать снова
                </button>
              </div>
            </div>
          )}

          {transactionDetails && (
            <>
              {/* Tabs */}
              <div className="border-b border-gray-200 px-6">
                <nav className="flex space-x-8">
                  {[
                    { key: 'info', label: 'Информация', icon: '📋' },
                    { key: 'details', label: 'Детали', icon: '🔍' },
                    { key: 'user', label: 'Пользователь', icon: '👤' },
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
                          <label className="block text-sm font-medium text-gray-600">ID транзакции</label>
                          <p className="text-gray-900 font-mono text-sm">{transactionDetails.transaction_id}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Тип</label>
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">{getTypeIcon(transactionDetails.type)}</span>
                            <span className="text-gray-900">{transactionDetails.type_display}</span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Статус</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusBadge(transactionDetails.status)}`}>
                            {transactionDetails.status_display}
                          </span>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Криптовалюта</label>
                          <div className="flex items-center gap-2">
                            {transactionDetails.crypto_info.icon && (
                              <img 
                                src={transactionDetails.crypto_info.icon} 
                                alt={transactionDetails.crypto_info.symbol}
                                className="w-6 h-6 rounded-full"
                              />
                            )}
                            <span className="text-gray-900">
                              {transactionDetails.crypto_info.name} ({transactionDetails.crypto_info.symbol})
                            </span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Сумма</label>
                          <p className="text-gray-900 font-medium">
                            {formatAmount(transactionDetails.amount)} {transactionDetails.crypto_info.symbol}
                          </p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Комиссия</label>
                          <p className="text-gray-900">
                            {formatAmount(transactionDetails.fee)} {transactionDetails.crypto_info.symbol}
                          </p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Дата создания</label>
                          <p className="text-gray-900">{formatDate(transactionDetails.timestamp)}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Последнее обновление</label>
                          <p className="text-gray-900">{formatDate(transactionDetails.updated_at)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Blockchain Info */}
                    {(transactionDetails.tx_hash || transactionDetails.block_number) && (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-lg font-semibold mb-4 text-gray-900">Blockchain информация</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {transactionDetails.tx_hash && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">Hash транзакции</label>
                              <p className="text-gray-900 font-mono text-sm break-all">{transactionDetails.tx_hash}</p>
                            </div>
                          )}
                          {transactionDetails.block_number && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">Номер блока</label>
                              <p className="text-gray-900 font-mono text-sm">{transactionDetails.block_number}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Additional Info */}
                    {(transactionDetails.notes || transactionDetails.ip_address) && (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h3 className="text-lg font-semibold mb-4 text-gray-900">Дополнительная информация</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {transactionDetails.notes && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">Заметки</label>
                              <p className="text-gray-900 text-sm">{transactionDetails.notes}</p>
                            </div>
                          )}
                          {transactionDetails.ip_address && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">IP адрес</label>
                              <p className="text-gray-900 font-mono text-sm">{transactionDetails.ip_address}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'details' && (
                  <div className="space-y-6">
                    {/* Exchange Details */}
                    {transactionDetails.exchange_info && (
                      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
                        <h3 className="text-lg font-semibold mb-4 text-gray-900">Детали обмена</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-600">От валюты</label>
                            <p className="text-gray-900">
                              {transactionDetails.exchange_info.from_crypto.name} ({transactionDetails.exchange_info.from_crypto.symbol})
                            </p>
                            <p className="text-sm text-gray-600">
                              Сумма: {formatAmount(transactionDetails.exchange_info.from_amount)}
                            </p>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-600">К валюте</label>
                            <p className="text-gray-900">
                              {transactionDetails.exchange_info.to_crypto.name} ({transactionDetails.exchange_info.to_crypto.symbol})
                            </p>
                            <p className="text-sm text-gray-600">
                              Сумма: {formatAmount(transactionDetails.exchange_info.to_amount)}
                            </p>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Курс обмена</label>
                            <p className="text-gray-900 font-mono">{formatAmount(transactionDetails.exchange_info.rate)}</p>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Комиссия</label>
                            <p className="text-gray-900">
                              {transactionDetails.exchange_info.fee_percentage}% ({formatAmount(transactionDetails.exchange_info.fee_amount)})
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Deposit Details */}
                    {transactionDetails.deposit_info && (
                      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-200">
                        <h3 className="text-lg font-semibold mb-4 text-gray-900">Детали депозита</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Адрес депозита</label>
                            <p className="text-gray-900 font-mono text-sm break-all">{transactionDetails.deposit_info.address}</p>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Статус подтверждения</label>
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              transactionDetails.deposit_info.confirmed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {transactionDetails.deposit_info.confirmed ? 'Подтвержден' : 'Ожидает подтверждения'}
                            </span>
                          </div>
                          {transactionDetails.deposit_info.confirmation_date && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">Дата подтверждения</label>
                              <p className="text-gray-900">{formatDate(transactionDetails.deposit_info.confirmation_date)}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Withdrawal Details */}
                    {transactionDetails.withdrawal_info && (
                      <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4 border border-orange-200">
                        <h3 className="text-lg font-semibold mb-4 text-gray-900">Детали вывода</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Адрес получателя</label>
                            <p className="text-gray-900 font-mono text-sm break-all">{transactionDetails.withdrawal_info.destination_address}</p>
                          </div>
                          {transactionDetails.withdrawal_info.memo && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">MEMO/Tag</label>
                              <p className="text-gray-900 font-mono text-sm">{transactionDetails.withdrawal_info.memo}</p>
                            </div>
                          )}
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Email подтверждение</label>
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              transactionDetails.withdrawal_info.is_email_confirmed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {transactionDetails.withdrawal_info.is_email_confirmed ? 'Подтвержден' : 'Ожидает подтверждения'}
                            </span>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Админ подтверждение</label>
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              transactionDetails.withdrawal_info.confirmed_by_admin ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {transactionDetails.withdrawal_info.confirmed_by_admin ? 'Подтвержден' : 'Ожидает подтверждения'}
                            </span>
                          </div>
                          {transactionDetails.withdrawal_info.rejected_reason && (
                            <div className="md:col-span-2">
                              <label className="block text-sm font-medium text-gray-600">Причина отклонения</label>
                              <p className="text-red-600 text-sm">{transactionDetails.withdrawal_info.rejected_reason}</p>
                            </div>
                          )}
                          {transactionDetails.withdrawal_info.confirmation_date && (
                            <div>
                              <label className="block text-sm font-medium text-gray-600">Дата подтверждения</label>
                              <p className="text-gray-900">{formatDate(transactionDetails.withdrawal_info.confirmation_date)}</p>
                            </div>
                          )}
                          <div>
                            <label className="block text-sm font-medium text-gray-600">Возврат</label>
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              transactionDetails.withdrawal_info.refunded ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {transactionDetails.withdrawal_info.refunded ? 'Возвращен' : 'Не возвращен'}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'user' && (
                  <div className="space-y-6">
                    {/* User Info */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold mb-4 text-gray-900">Информация о пользователе</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-600">ID пользователя</label>
                          <p className="text-gray-900">{transactionDetails.user_info.id}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Username</label>
                          <p className="text-gray-900">{transactionDetails.user_info.username}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Email</label>
                          <p className="text-gray-900">{transactionDetails.user_info.email}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Полное имя</label>
                          <p className="text-gray-900">
                            {transactionDetails.user_info.first_name && transactionDetails.user_info.last_name 
                              ? `${transactionDetails.user_info.first_name} ${transactionDetails.user_info.last_name}`
                              : transactionDetails.user_info.first_name || transactionDetails.user_info.last_name || "Не указано"
                            }
                          </p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">Email верификация</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            transactionDetails.user_info.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {transactionDetails.user_info.is_verified ? 'Подтвержден' : 'Не подтвержден'}
                          </span>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-600">KYC верификация</label>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            transactionDetails.user_info.kyc_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {transactionDetails.user_info.kyc_verified ? 'Пройдена' : 'Не пройдена'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h3 className="text-lg font-semibold mb-4 text-gray-900">Быстрые действия</h3>
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => window.open(`/admin/users/${transactionDetails.user_info.id}`, '_blank')}
                          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                        >
                          👤 Открыть профиль пользователя
                        </button>
                        <button
                          onClick={() => window.open(`/admin/transactions/transaction/${transactionDetails.id}/change/`, '_blank')}
                          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                        >
                          ✏️ Редактировать в админке
                        </button>
                      </div>
                    </div>
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
