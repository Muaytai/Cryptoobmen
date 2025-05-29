'use client';

import React, { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import axios from 'axios';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

// Типы данных
interface Wallet {
  id: number;
  crypto: {
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
  id: number;
  crypto: {
    id: number;
    name: string;
    symbol: string;
  };
  price_usd: string;
}

export const WalletPage: React.FC = () => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalUsdBalance, setTotalUsdBalance] = useState<number>(0);
  const [selectedAction, setSelectedAction] = useState<'deposit' | 'withdraw' | 'exchange' | 'invest' | null>(null);
  const [selectedWallet, setSelectedWallet] = useState<Wallet | null>(null);
  
  const router = useRouter();
  const { tokens, isAuthenticated } = useAuthStore();
  const token = tokens?.access;

  // Получение данных кошельков пользователя
  useEffect(() => {
    const fetchWallets = async () => {
      // Проверяем наличие токена и авторизации
      if (!token || !isAuthenticated) {
        console.log('Нет токена или не авторизован, перенаправляем на страницу входа');
        router.push('/login?redirect=wallet');
        return;
      }
      
      // Дополнительная проверка на наличие токена в заголовках
      if (!token) {
        console.log('Токен отсутствует в заголовках');
        router.push('/login?redirect=wallet');
        return;
      }

      console.log('Начинаем загрузку данных кошелька');
      try {
        setLoading(true);
        
        // Получаем кошельки пользователя
        console.log('Запрашиваем кошельки по URL:', `${process.env.NEXT_PUBLIC_API_URL}/wallets/`);
        const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/wallets/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Получен ответ по кошелькам:', walletsResponse.data);
        
        // Получаем последние цены криптовалют
        console.log('Запрашиваем цены криптовалют по URL:', `${process.env.NEXT_PUBLIC_API_URL}/crypto-prices/latest/`);
        const pricesResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto-prices/latest/`);
        console.log('Получен ответ по ценам:', pricesResponse.data);
        
        // Получаем общий баланс в USD
        console.log('Запрашиваем баланс по URL:', `${process.env.NEXT_PUBLIC_API_URL}/wallets/balance/`);
        const balanceResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/wallets/balance/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Получен ответ по балансу:', balanceResponse.data);
        
        setWallets(walletsResponse.data);
        setPrices(pricesResponse.data);
        setTotalUsdBalance(balanceResponse.data.total_usd_balance);
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении данных кошелька:', err);
        setError('Не удалось загрузить данные кошелька. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    fetchWallets();
  }, [token, router]);

  // Получение цены криптовалюты по ID
  const getCryptoPrice = (cryptoId: number): string => {
    const price = prices.find(p => p.crypto.id === cryptoId);
    return price ? price.price_usd : '0';
  };

  // Расчет USD-эквивалента для кошелька
  const getWalletUsdValue = (wallet: Wallet): number => {
    const price = parseFloat(getCryptoPrice(wallet.crypto.id));
    const balance = parseFloat(wallet.balance);
    return price * balance;
  };

  // Обработчик выбора действия
  const handleActionSelect = (action: 'deposit' | 'withdraw' | 'exchange' | 'invest', wallet: Wallet) => {
    setSelectedAction(action);
    setSelectedWallet(wallet);
    
    // Перенаправление на соответствующую страницу
    if (action === 'deposit') {
      router.push(`/funds/deposit?wallet_id=${wallet.id}&crypto=${wallet.crypto.symbol}`);
    } else if (action === 'withdraw') {
      router.push(`/funds/withdraw?wallet_id=${wallet.id}&crypto=${wallet.crypto.symbol}`);
    } else if (action === 'exchange') {
      router.push(`/exchange?from_crypto=${wallet.crypto.id}`);
    } else if (action === 'invest') {
      router.push(`/profile/investments/new?wallet_id=${wallet.id}&crypto=${wallet.crypto.symbol}`);
    }
  };

  if (loading) {
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
          onClick={() => window.location.reload()} 
          className="mt-4 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  // Добавляем логи для отладки рендеринга
  console.log('Состояние перед рендерингом:', { loading, error, wallets, prices, totalUsdBalance });
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center text-purple-500">Мои кошельки</h1>
      {/* Добавляем отладочную информацию */}
      <div className="bg-gray-800 p-4 mb-4 rounded">
        <p className="text-green-400">Debug Info:</p>
        <p>Loading: {loading ? 'true' : 'false'}</p>
        <p>Error: {error || 'none'}</p>
        <p>Wallets Count: {wallets.length}</p>
        <p>Prices Count: {prices.length}</p>
        <p>Total USD Balance: ${totalUsdBalance}</p>
        <p>Token: {token ? 'Есть токен' : 'Нет токена'}</p>
        <p>Authenticated: {isAuthenticated ? 'true' : 'false'}</p>
      </div>
      
      {/* Общий баланс */}
      <div className="bg-gray-800 rounded-xl p-6 mb-8 shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Общий баланс</h2>
        <div className="text-4xl font-bold text-green-500">${typeof totalUsdBalance === 'number' ? totalUsdBalance.toFixed(2) : '0.00'}</div>
      </div>
      <p className="text-sm text-gray-400 mt-1">Эквивалент в USD</p>
      
      {/* Список кошельков */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {wallets && wallets.length > 0 ? wallets.map(wallet => {
          // Находим текущую цену криптовалюты
          const price = prices && prices.length > 0 ? prices.find(p => p.crypto && p.crypto.id === wallet.crypto.id) : null;
          const usdValue = price && wallet.balance ? parseFloat(wallet.balance) * parseFloat(price.price_usd) : 0;
          
          return (
            <div key={wallet.id} className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex items-center mb-4">
                {wallet.crypto.icon ? (
                  <Image 
                    src={`${process.env.NEXT_PUBLIC_API_URL}${wallet.crypto.icon}`} 
                    alt={wallet.crypto.symbol} 
                    width={40} 
                    height={40} 
                    className="rounded-full mr-3"
                  />
                ) : (
                  <div className="w-10 h-10 bg-gray-700 rounded-full mr-3 flex items-center justify-center">
                    {wallet.crypto.symbol.slice(0, 2)}
                  </div>
                )}
                <div>
                  <h3 className="text-lg font-semibold">{wallet.crypto.name}</h3>
                  <p className="text-sm text-gray-400">{wallet.crypto.symbol}</p>
                </div>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-400">Баланс</p>
                <p className="text-xl font-bold">{parseFloat(wallet.balance).toFixed(8)} {wallet.crypto.symbol}</p>
                <p className="text-sm text-gray-400">
                  ≈ ${getWalletUsdValue(wallet).toFixed(2)}
                </p>
              </div>
              
              {parseFloat(wallet.locked_balance) > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-gray-400">Заблокировано в инвестициях</p>
                  <p className="text-md font-medium text-yellow-500">
                    {parseFloat(wallet.locked_balance).toFixed(8)} {wallet.crypto.symbol}
                  </p>
                </div>
              )}
              
              {wallet.address && (
                <div className="mb-4">
                  <p className="text-sm text-gray-400">Адрес кошелька</p>
                  <p className="text-xs bg-gray-700 p-2 rounded overflow-x-auto whitespace-nowrap">
                    {wallet.address}
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-2 mt-4">
                <button 
                  onClick={() => handleActionSelect('deposit', wallet)}
                  className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition"
                >
                  Пополнить
                </button>
                <button 
                  onClick={() => handleActionSelect('withdraw', wallet)}
                  className="bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition"
                >
                  Вывести
                </button>
                <button 
                  onClick={() => handleActionSelect('exchange', wallet)}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition"
                >
                  Обменять
                </button>
                <button 
                  onClick={() => handleActionSelect('invest', wallet)}
                  className="bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition"
                >
                  Инвестировать
                </button>
              </div>
            </div>
          );
        }) : (
          <div className="col-span-full bg-gray-800 rounded-xl p-6 text-center">
            <p className="text-lg mb-4">У вас пока нет кошельков</p>
            <p className="text-sm text-gray-400 mb-6">
              Кошельки создаются автоматически при первом пополнении или получении криптовалюты
            </p>
            <Link href="/exchange" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
              Перейти к обмену
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
