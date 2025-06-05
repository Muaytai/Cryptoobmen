'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { api } from '@/lib/api/fetch';
import Image from 'next/image';
import Link from 'next/link';

// Типы данных
interface Cryptocurrency {
  id: number;
  name: string;
  symbol: string;
  icon: string;
  min_amount: string;
  max_amount: string;
  fee_percentage: string;
}

interface ExchangePair {
  id: number;
  from_crypto: Cryptocurrency;
  to_crypto: Cryptocurrency;
  is_active: boolean;
  custom_fee_percentage: string | null;
  min_from_amount: string | null;
  max_from_amount: string | null;
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

interface Wallet {
  id: number;
  currency: Cryptocurrency;
  balance: string;
  available_balance: string;
  locked_balance: string;
}

interface ExchangeCalculation {
  from_amount: string;
  from_crypto: Cryptocurrency;
  to_amount: string;
  to_crypto: Cryptocurrency;
  rate: string;
  fee_percentage: string;
  fee_amount: string;
  fee_usd: string;
}

export default function ExchangePageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();

  // Состояния для данных
  const [cryptocurrencies, setCryptocurrencies] = useState<Cryptocurrency[]>([]);
  const [exchangePairs, setExchangePairs] = useState<ExchangePair[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  
  // Состояния для формы обмена
  const [fromCryptoId, setFromCryptoId] = useState<number | null>(null);
  const [toCryptoId, setToCryptoId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [calculation, setCalculation] = useState<ExchangeCalculation | null>(null);
  const [selectedPair, setSelectedPair] = useState<ExchangePair | null>(null);
  
  // Состояния для UI
  const [loading, setLoading] = useState<boolean>(true);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [exchangeId, setExchangeId] = useState<string | null>(null);

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    if (authLoading) {
      console.log('ExchangePage: authLoading is true, ожидаем завершения проверки сессии...');
      setLoading(true);
      return;
    }

    console.log(`ExchangePage: authLoading is false. isAuthenticated: ${isAuthenticated}, user: ${!!user}`);

    if (!isAuthenticated || !user) {
      console.log('ExchangePage: Пользователь НЕ аутентифицирован (после authLoading: false). Перенаправление на /login.');
      const redirectPath = `/exchange${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
      router.push(`/login?redirect=${encodeURIComponent(redirectPath)}`);
      return;
    }
    
    // Если пользователь аутентифицирован, загружаем данные страницы
    const fetchData = async () => {
      console.log('ExchangePage: Пользователь аутентифицирован. Загрузка данных страницы...');
      setLoading(true);
      try {
        const cryptoResponse = await api.get('/crypto/cryptocurrencies/');
        const pairsResponse = await api.get('/crypto/pairs/');
        const pricesResponse = await api.get('/crypto/prices/');
        const walletsResponse = await api.get('/crypto/wallets/');
        
        setCryptocurrencies(cryptoResponse.data);
        setExchangePairs(pairsResponse.data);
        setPrices(pricesResponse.data);
        setWallets(walletsResponse.data);
        
        // Если в URL есть параметр from_crypto, выбираем эту криптовалюту
        const fromCryptoParam = searchParams.get('from_crypto');
        if (fromCryptoParam && cryptoResponse.data.some((c: Cryptocurrency) => c.id === parseInt(fromCryptoParam))) {
          setFromCryptoId(parseInt(fromCryptoParam));
          
          // Находим подходящую пару для обмена
          const suitablePairs = pairsResponse.data.filter(
            (p: ExchangePair) => p.from_crypto.id === parseInt(fromCryptoParam)
          );
          
          if (suitablePairs.length > 0) {
            // Предпочитаем USDT или стейблкоины для обмена
            const usdtPair = suitablePairs.find(
              (p: ExchangePair) => p.to_crypto.symbol === 'USDT' || 
                                  p.to_crypto.symbol === 'USDC' || 
                                  p.to_crypto.symbol === 'DAI'
            );
            
            if (usdtPair) {
              setToCryptoId(usdtPair.to_crypto.id);
              setSelectedPair(usdtPair);
            } else {
              setToCryptoId(suitablePairs[0].to_crypto.id);
              setSelectedPair(suitablePairs[0]);
            }
          }
        } else if (cryptoResponse.data.length > 0) {
          // По умолчанию выбираем первую криптовалюту с наибольшим балансом
          const userWallets = walletsResponse.data;
          if (userWallets.length > 0) {
            // Сортируем кошельки по балансу (от большего к меньшему)
            const sortedWallets = [...userWallets].sort(
              (a, b) => parseFloat(b.available_balance) - parseFloat(a.available_balance)
            );
            
            // Выбираем криптовалюту из кошелька с наибольшим балансом
            const walletWithBalance = sortedWallets.find(w => parseFloat(w.available_balance) > 0);
            if (walletWithBalance) {
              setFromCryptoId(walletWithBalance.currency.id);
              
              // Находим подходящую пару для обмена
              const suitablePairs = pairsResponse.data.filter(
                (p: ExchangePair) => p.from_crypto.id === walletWithBalance.currency.id
              );
              
              if (suitablePairs.length > 0) {
                setToCryptoId(suitablePairs[0].to_crypto.id);
                setSelectedPair(suitablePairs[0]);
              }
            } else {
              // Если нет кошельков с балансом, выбираем первую криптовалюту
              setFromCryptoId(cryptoResponse.data[0].id);
              
              // И первую доступную пару обмена
              const firstPair = pairsResponse.data.find(
                (p: ExchangePair) => p.from_crypto.id === cryptoResponse.data[0].id
              );
              
              if (firstPair) {
                setToCryptoId(firstPair.to_crypto.id);
                setSelectedPair(firstPair);
              }
            }
          }
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении данных:', err);
        setError('Не удалось загрузить данные. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    fetchData();
  }, [authLoading, isAuthenticated, user, router, searchParams]);

  // Обновление выбранной пары при изменении криптовалют
  useEffect(() => {
    if (fromCryptoId && toCryptoId) {
      const pair = exchangePairs.find(
        p => p.from_crypto.id === fromCryptoId && p.to_crypto.id === toCryptoId
      );
      
      setSelectedPair(pair || null);
      
      // Если пара не найдена, сбрасываем расчет
      if (!pair) {
        setCalculation(null);
      }
    } else {
      setSelectedPair(null);
      setCalculation(null);
    }
  }, [fromCryptoId, toCryptoId, exchangePairs]);

  // Расчет обмена при изменении суммы или пары
  useEffect(() => {
    const calculateExchange = async () => {
      if (selectedPair && amount && !isNaN(parseFloat(amount)) && parseFloat(amount) > 0) {
        try {
          setCalculating(true);
          
          const calculationData = {
            from_crypto: selectedPair.from_crypto.id,
            to_crypto: selectedPair.to_crypto.id,
            amount: parseFloat(amount)
          };
          
          const response = await api.post('/crypto/calculator/', calculationData);
          
          setCalculation(response.data);
          setCalculating(false);
        } catch (err) {
          console.error('Ошибка при расчете обмена:', err);
          setCalculation(null);
          setCalculating(false);
        }
      } else {
        setCalculation(null);
      }
    };
    
    // Используем debounce для предотвращения слишком частых запросов
    const debounceTimeout = setTimeout(calculateExchange, 500);
    
    return () => clearTimeout(debounceTimeout);
  }, [selectedPair, amount]);

  // Обработчики изменения полей формы
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Разрешаем только числа и одну точку
    if (/^\d*\.?\d*$/.test(value) || value === '') {
      setAmount(value);
    }
  };

  const handleFromCryptoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cryptoId = parseInt(e.target.value);
    setFromCryptoId(cryptoId);
    
    // Сбрасываем выбранную криптовалюту для получения, если она совпадает с выбранной для отправки
    if (toCryptoId === cryptoId) {
      setToCryptoId(null);
    }
    
    // Находим подходящие пары для обмена
    const suitablePairs = exchangePairs.filter(
      p => p.from_crypto.id === cryptoId
    );
    
    // Если есть подходящие пары и не выбрана криптовалюта для получения, выбираем первую доступную
    if (suitablePairs.length > 0 && (!toCryptoId || toCryptoId === cryptoId)) {
      setToCryptoId(suitablePairs[0].to_crypto.id);
    }
  };

  const handleToCryptoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setToCryptoId(parseInt(e.target.value));
  };

  // Получение максимально доступной суммы для обмена
  const getMaxAvailableAmount = (): string => {
    if (!fromCryptoId) return '0';
    
    const wallet = wallets.find(w => w.currency.id === fromCryptoId);
    if (!wallet) return '0';
    
    return wallet.available_balance;
  };

  // Установка максимальной доступной суммы
  const setMaxAmount = () => {
    const maxAmount = getMaxAvailableAmount();
    setAmount(maxAmount);
  };

  // Обмен местами криптовалют
  const swapCryptos = () => {
    if (fromCryptoId && toCryptoId) {
      const tempCryptoId = fromCryptoId;
      setFromCryptoId(toCryptoId);
      setToCryptoId(tempCryptoId);
      setAmount(''); // Сбрасываем сумму при обмене местами
    }
  };

  // Отправка формы обмена
  const handleExchange = async () => {
    // Проверка аутентификации (если еще не сделана глобально для страницы или компонента)
    // В нашем случае, useAuthStore и проверка в fetchData уже должны были отработать.
    // Если selectedPair или amount не установлены, или нет данных для calculation (если они нужны для валидации)
    if (!selectedPair || !amount || parseFloat(amount) <= 0) {
      setError('Пожалуйста, выберите криптовалюты, введите корректную сумму и дождитесь расчета.');
      return;
    }
    
    // Дополнительная проверка баланса перед отправкой
    const fromWallet = wallets.find(w => w.currency.id === selectedPair.from_crypto.id);
    if (!fromWallet || parseFloat(fromWallet.available_balance) < parseFloat(amount)) {
      setError('Недостаточно средств на выбранном кошельке для совершения обмена.');
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      // Формируем данные для запроса в соответствии с ожиданиями бэкенда
      const exchangePayload = {
        from_symbol: selectedPair.from_crypto.symbol, // Используем символ валюты
        to_symbol: selectedPair.to_crypto.symbol,     // Используем символ валюты
        amount_from: parseFloat(amount).toString()      // Сумма как строка
      };
      
      // Используем правильный эндпоинт и обновленные данные
      const response = await api.post('/crypto/exchange-currency/', exchangePayload);
      
      setSuccess(true);
      // Убедимся, что получаем ID транзакции или обмена из ответа бэкенда
      // Это может быть response.data.transaction_id, response.data.exchange_id, или просто response.data.id
      // В ExchangeCurrencyView мы возвращали {'message': 'Exchange successful', 'exchange_id': new_exchange.id, 'transaction_from_id': trans_from.id, 'transaction_to_id': trans_to.id}
      setExchangeId(response.data.exchange_id || response.data.transaction_from_id || 'N/A');
      
      // Очищаем форму
      setAmount('');
      setCalculation(null); // Также сбрасываем расчет
      
      // Опционально: обновить балансы пользователя после успешного обмена
      // const updatedWalletsResponse = await api.get('/crypto/wallets/');
      // setWallets(updatedWalletsResponse.data);
      
      setSubmitting(false);
    } catch (err: any) {
      console.error('Ошибка при отправке запроса:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.');
      setSubmitting(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка данных...</p>
      </div>
    );
  }

  if (success) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="bg-green-500 bg-opacity-20 p-8 rounded-xl max-w-md w-full text-center">
          <svg className="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <h2 className="text-2xl font-bold mb-4">Обмен успешно выполнен!</h2>
          <p className="mb-6">Идентификатор операции: {exchangeId}</p>
          <p className="mb-6 text-sm text-gray-400">
            Обмен выполнен успешно. Вы можете проверить статус операции в разделе "История транзакций".
          </p>
          <div className="flex flex-col space-y-3">
            <Link href="/wallet" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
              Перейти к кошельку
            </Link>
            <button 
              onClick={() => setSuccess(false)} 
              className="text-purple-400 hover:text-purple-300 transition"
            >
              Новый обмен
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Обмен криптовалют</h1>
        
        {error && (
          <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
            <p className="text-red-500">{error}</p>
          </div>
        )}
        
        <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
          {/* Форма обмена */}
          <div className="space-y-6">
            {/* Отдаю */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-gray-300">Отдаю</label>
                <button 
                  type="button"
                  onClick={setMaxAmount}
                  className="text-sm text-purple-400 hover:text-purple-300"
                >
                  Максимум: {parseFloat(getMaxAvailableAmount()).toFixed(8)}
                </button>
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={amount}
                  onChange={handleAmountChange}
                  placeholder="0.00000000"
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <select
                  value={fromCryptoId || ''}
                  onChange={handleFromCryptoChange}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="" disabled>Выберите</option>
                  {cryptocurrencies.map(crypto => (
                    <option key={crypto.id} value={crypto.id}>
                      {crypto.symbol}
                    </option>
                  ))}
                </select>
              </div>
              {fromCryptoId && (
                <div className="mt-2 flex items-center">
                  {cryptocurrencies.find(c => c.id === fromCryptoId)?.icon ? (
                    <Image 
                      src={
                        (cryptocurrencies.find(c => c.id === fromCryptoId)?.icon || '').startsWith('http')
                          ? (cryptocurrencies.find(c => c.id === fromCryptoId)?.icon || '')
                          : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${(cryptocurrencies.find(c => c.id === fromCryptoId)?.icon || '')}`
                      } 
                      alt={cryptocurrencies.find(c => c.id === fromCryptoId)?.symbol || ''} 
                      width={24} 
                      height={24} 
                      className="rounded-full mr-2"
                    />
                  ) : (
                    <div className="w-6 h-6 bg-gray-700 rounded-full mr-2 flex items-center justify-center text-xs">
                      {cryptocurrencies.find(c => c.id === fromCryptoId)?.symbol.slice(0, 2)}
                    </div>
                  )}
                  <span className="text-sm text-gray-400">
                    {cryptocurrencies.find(c => c.id === fromCryptoId)?.name}
                  </span>
                </div>
              )}
            </div>
            
            {/* Кнопка обмена местами */}
            <div className="flex justify-center">
              <button
                onClick={swapCryptos}
                className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 transition"
              >
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
            </div>
            
            {/* Получаю */}
            <div>
              <label className="block text-gray-300 mb-2">Получаю</label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={calculation ? calculation.to_amount : '0'}
                  disabled
                  className="flex-1 bg-gray-600 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none"
                />
                <select
                  value={toCryptoId || ''}
                  onChange={handleToCryptoChange}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="" disabled>Выберите</option>
                  {fromCryptoId && exchangePairs
                    .filter(pair => pair.from_crypto.id === fromCryptoId)
                    .map(pair => (
                      <option key={pair.to_crypto.id} value={pair.to_crypto.id}>
                        {pair.to_crypto.symbol}
                      </option>
                    ))}
                </select>
              </div>
              {toCryptoId && (
                <div className="mt-2 flex items-center">
                  {cryptocurrencies.find(c => c.id === toCryptoId)?.icon ? (
                    <Image 
                      src={
                        (cryptocurrencies.find(c => c.id === toCryptoId)?.icon || '').startsWith('http')
                          ? (cryptocurrencies.find(c => c.id === toCryptoId)?.icon || '')
                          : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${(cryptocurrencies.find(c => c.id === toCryptoId)?.icon || '')}`
                      }
                      alt={cryptocurrencies.find(c => c.id === toCryptoId)?.symbol || ''} 
                      width={24} 
                      height={24} 
                      className="rounded-full mr-2"
                    />
                  ) : (
                    <div className="w-6 h-6 bg-gray-700 rounded-full mr-2 flex items-center justify-center text-xs">
                      {cryptocurrencies.find(c => c.id === toCryptoId)?.symbol.slice(0, 2)}
                    </div>
                  )}
                  <span className="text-sm text-gray-400">
                    {cryptocurrencies.find(c => c.id === toCryptoId)?.name}
                  </span>
                </div>
              )}
            </div>
            
            {/* Информация об обмене */}
            {calculation && (
              <div className="bg-gray-700 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Детали обмена</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Курс обмена:</span>
                    <span>1 {calculation.from_crypto.symbol} = {parseFloat(calculation.rate).toFixed(8)} {calculation.to_crypto.symbol}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Комиссия:</span>
                    <span className="text-yellow-400">
                      {calculation.fee_amount} {calculation.from_crypto.symbol} ({calculation.fee_percentage}%)
                    </span>
                  </div>
                  <div className="border-t border-gray-600 my-2 pt-2 flex justify-between font-semibold">
                    <span>Вы получите:</span>
                    <span className="text-green-400">
                      {calculation.to_amount} {calculation.to_crypto.symbol}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Кнопка обмена */}
            <button
              onClick={handleExchange}
              disabled={submitting || !selectedPair || !amount || parseFloat(amount) <= 0 || !calculation}
              className={`
                w-full py-3 px-6 rounded-lg text-white font-medium transition
                ${submitting || !selectedPair || !amount || parseFloat(amount) <= 0 || !calculation
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-purple-600 hover:bg-purple-700'}
              `}
            >
              {submitting ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Обработка...
                </span>
              ) : calculating ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Расчет...
                </span>
              ) : (
                'Обменять'
              )}
            </button>
            
            <p className="text-xs text-gray-400 mt-2 text-center">
              Обмен происходит по текущему рыночному курсу. Курс может измениться в момент выполнения операции.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}