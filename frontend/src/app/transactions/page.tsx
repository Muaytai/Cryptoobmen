'use client';

import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter } from 'next/navigation';
import Image from "next/image";

// Типы данных
interface CryptoCurrency {
    id: number;
    name: string;
    symbol: string;
    icon: string;
}

interface TransactionDetails {
    // Обмен
    from_currency?: CryptoCurrency;
    to_currency?: CryptoCurrency;
    from_amount?: string;
    to_amount?: string;
    rate?: string;
    // Депозит
    address?: string;
    // Вывод
    destination_address?: string;
}

interface Transaction {
    transaction_id: string;
    type: 'deposit' | 'withdrawal' | 'exchange';
    status: string;
    amount: string;
    crypto: CryptoCurrency;
    timestamp: string;
    tx_hash: string | null;
    details: TransactionDetails | null;
}

const TransactionHistoryPage = () => {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { isAuthenticated, isLoading: authLoading } = useAuthStore();
    const router = useRouter();

    useEffect(() => {
        if (authLoading) return;
        if (!isAuthenticated) {
            router.push('/login?redirect=transactions');
            return;
        }

        const fetchTransactions = async () => {
            try {
                setLoading(true);
                const response = await api.get('/transactions/history/');
                setTransactions(response.data);
                setError(null);
            } catch (err) {
                console.error("Failed to fetch transaction history", err);
                setError("Не удалось загрузить историю транзакций.");
            } finally {
                setLoading(false);
            }
        };

        fetchTransactions();
    }, [isAuthenticated, authLoading, router]);

    const renderTransactionDetails = (tx: Transaction) => {
        switch (tx.type) {
            case 'deposit':
                return (
                    <span>
                        Пополнение {parseFloat(tx.amount).toFixed(6)} {tx.crypto.symbol}
                    </span>
                );
            case 'withdrawal':
                return (
                    <span>
                        Вывод {parseFloat(tx.amount).toFixed(6)} {tx.crypto.symbol}
                    </span>
                );
            case 'exchange':
                if (tx.details && tx.details.from_currency && tx.details.to_currency) {
                    return (
                        <span>
                            Обмен {parseFloat(tx.details.from_amount!).toFixed(6)} {tx.details.from_currency.symbol} на {parseFloat(tx.details.to_amount!).toFixed(6)} {tx.details.to_currency.symbol}
                        </span>
                    );
                }
                return <span>Обмен</span>;
            default:
                return <span>Неизвестная операция</span>;
        }
    };
    
    const getStatusClass = (status: string) => {
        switch (status.toLowerCase()) {
            case 'completed': return 'text-green-400';
            case 'pending': return 'text-yellow-400';
            case 'failed':
            case 'cancelled':
                return 'text-red-400';
            default: return 'text-gray-400';
        }
    }

    if (loading || authLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (error) {
        return <div className="min-h-screen flex items-center justify-center text-red-500">{error}</div>;
    }

    return (
        <div className="container mx-auto p-4 md:p-8 text-white">
            <h1 className="text-3xl font-bold mb-6 text-center">История транзакций</h1>
            <div className="bg-gray-800 rounded-xl shadow-lg p-4">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-400 uppercase bg-gray-700">
                            <tr>
                                <th scope="col" className="px-6 py-3">Тип</th>
                                <th scope="col" className="px-6 py-3">Описание</th>
                                <th scope="col" className="px-6 py-3">Статус</th>
                                <th scope="col" className="px-6 py-3">Дата</th>
                            </tr>
                        </thead>
                        <tbody>
                        {transactions.map((tx) => (
                            <tr key={tx.transaction_id} className="border-b border-gray-700 hover:bg-gray-700/50">
                                <td className="px-6 py-4 capitalize font-medium flex items-center">
                                    {tx.type === 'exchange' ? (
                                        <div className="flex items-center">
                                            <Image src={tx.details?.from_currency?.icon!} alt="" width={24} height={24} className="rounded-full z-10" unoptimized/>
                                            <Image src={tx.details?.to_currency?.icon!} alt="" width={24} height={24} className="rounded-full -ml-2" unoptimized/>
                                        </div>
                                    ) : (
                                        <Image src={tx.crypto.icon} alt="" width={24} height={24} className="rounded-full" unoptimized/>
                                    )}
                                    <span className="ml-2">{tx.type}</span>
                                </td>
                                <td className="px-6 py-4">
                                    {renderTransactionDetails(tx)}
                                </td>
                                <td className={`px-6 py-4 font-semibold ${getStatusClass(tx.status)}`}>
                                    {tx.status}
                                </td>
                                <td className="px-6 py-4 text-gray-400">
                                    {new Date(tx.timestamp).toLocaleString('ru-RU')}
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                    {transactions.length === 0 && !loading && (
                        <div className="text-center py-8 text-gray-500">
                            История транзакций пуста.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TransactionHistoryPage;
