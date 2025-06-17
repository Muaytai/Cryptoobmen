'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useIsomorphicLayoutEffect } from 'usehooks-ts'
import { useSWRConfig } from 'swr'


// ---- CONFIG ----
const REFETCH_INTERVAL = 30000; // 30 секунд

// Типы данных
interface Wallet {
  id: number;
  currency: {
    id: number;
    name: string;
    symbol: string;
    icon: string;
  };
  balance: string;
  available_balance: string;
  locked_balance: string;
  address: string;
}

interface CryptoPrice {
  crypto_id: number;
  name: string;
  symbol: string;
  prices: { [key: string]: number }; // e.g. { usd: 60000, eur: 55000 }
}

export const WalletPage: React.FC = () => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [componentLoading, setComponentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalUsdBalance, setTotalUsdBalance] = useState<number>(0);
  const [selectedAction, setSelectedAction] = useState<'deposit' | 'withdraw' | 'exchange' | 'invest' | null>(null);
  const [selectedWallet, setSelectedWallet] = useState<Wallet | null>(null);
  
  const router = useRouter();
  const { isAuthenticated, user, isLoading: authLoading } = useAuthStore();
  const { mutate } = useSWRConfig()

  const refetchData = async (isBackground = false) => {
    console.log(`[refetchData] Starting data refetch (background: ${isBackground})...`);
    if (!isBackground) setComponentLoading(true);

    try {
      const [walletsResponse, pricesResponse, balanceResponse] = await Promise.all([
        api.get('/crypto/wallets/'),
        api.get(`/crypto/prices/latest/?vs_currencies=usd`),
        api.get('/crypto/wallets/balance/')
      ]);

      setWallets(walletsResponse.data);
      console.log('[WalletPage Debug] walletsResponse.data:', walletsResponse.data);
      setPrices(pricesResponse.data);
      console.log('[WalletPage Debug] balanceResponse.data:', balanceResponse.data);
      setTotalUsdBalance(balanceResponse.data.total_usd_balance);
      setError(null);
    } catch (err) {
      console.error('Ошибка при получении данных кошелька:', err);
      if (!isBackground) setError('Не удалось обновить данные.');
    } finally {
      if (!isBackground) setComponentLoading(false);
    }
  };

  // Первоначальная загрузка и установка интервала
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated || !user) {
      router.push('/login?redirect=wallet');
      return;
    }
    
    refetchData(false);
    const intervalId = setInterval(() => refetchData(true), REFETCH_INTERVAL);
    return () => clearInterval(intervalId);
  }, [isAuthenticated, authLoading, user, router]);
  
  // Обновление при фокусе окна
  useIsomorphicLayoutEffect(() => {
    const handleFocus = () => refetchData(true);
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  // --- CALCULATIONS ---
  const getConvertedValue = (crypto_id: number, balance: string): number => {
    const priceInfo = prices.find(p => p.crypto_id === crypto_id);
    const rate = priceInfo?.prices?.['usd'];
    if (!rate) return 0;
    return parseFloat(balance) * rate;
  };

  // --- UI RENDERING ---
  if (authLoading || componentLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка данных кошелька...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg">
          <p className="text-red-500">{error}</p>
        </div>
        <button
          onClick={() => refetchData(false)}
          className="mt-4 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-900 text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-center text-gray-100">Мои кошельки</h1>

      {/* Общий баланс */}
      <div className="bg-gray-800 rounded-xl p-6 mb-8 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Общий баланс</h2>
        </div>
        <div className="text-4xl font-bold text-green-500">
          {totalUsdBalance.toLocaleString('ru-RU', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <p className="text-sm text-gray-400 mt-1">Примерный эквивалент в USD</p>
      </div>

      {/* Список кошельков */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {wallets.filter(wallet => wallet.currency.symbol !== 'USD' && wallet.currency.symbol !== 'RUB' && wallet.currency.symbol !== 'BYR').length > 0 ? wallets.filter(wallet => wallet.currency.symbol !== 'USD' && wallet.currency.symbol !== 'RUB' && wallet.currency.symbol !== 'BYR').map((wallet, index) => {
          const convertedValue = getConvertedValue(wallet.currency.id, wallet.balance);
          const itemClassName = index === 0 ? 'wallet-item-example' : '';
          return (
            <div key={wallet.id} className={`bg-gray-800 rounded-xl p-6 shadow-lg flex flex-col justify-between ${itemClassName}`}>
              <div>
                <div className="flex items-center mb-4">
                  {wallet.currency.icon ? (
                    <Image
                      src={wallet.currency.icon.startsWith('http') ? wallet.currency.icon : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${wallet.currency.icon}`}
                      alt={wallet.currency.symbol}
                      width={40}
                      height={40}
                      className="rounded-full mr-3"
                      unoptimized
                    />
                  ) : (
                    <div className="w-10 h-10 bg-gray-700 rounded-full mr-3 flex items-center justify-center font-bold text-gray-300">
                      {wallet.currency?.symbol?.slice(0, 2) || '??'}
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold">{wallet.currency.name}</h3>
                    <p className="text-sm text-gray-400">{wallet.currency.symbol}</p>
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-400">Баланс</p>
                  <p className="text-xl font-bold">{parseFloat(wallet.balance).toFixed(8)} {wallet.currency.symbol}</p>
                  <p className="text-sm text-gray-400">
                    ≈ {convertedValue.toLocaleString('ru-RU', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 mt-auto">
                {/* Кнопки действий */}
                <Link href={`/funds/deposit?wallet_id=${wallet.id}&crypto=${wallet.currency.symbol}`} className="bg-green-600 text-center text-white py-2 px-4 rounded-lg hover:bg-green-700 transition">Пополнить</Link>
                <Link href={`/funds/withdraw?wallet_id=${wallet.id}&crypto=${wallet.currency.symbol}`} className="bg-red-600 text-center text-white py-2 px-4 rounded-lg hover:bg-red-700 transition">Вывести</Link>
                <Link href={`/exchange?from_crypto=${wallet.currency.id}`} className="col-span-2 bg-blue-600 text-center text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition">Обменять</Link>
              </div>
            </div>
          );
        }) : (
          <div className="col-span-full bg-gray-800 rounded-xl p-6 text-center">
            <p className="text-lg">У вас пока нет кошельков.</p>
          </div>
        )}
      </div>
    </div>
  );
};
