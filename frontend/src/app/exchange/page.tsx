'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
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
  from_crypto: number | Cryptocurrency;
  to_crypto: number | Cryptocurrency;
  is_active: boolean;
  custom_fee_percentage: string | null;
  min_from_amount: string | null;
  max_from_amount: string | null;
}

// Расширенный тип для поддержки обеих структур
interface CryptoPrice {
  id?: number;
  crypto?: {
    id: number;
    name: string;
    symbol: string;
  };
  price_usd?: string;
  crypto_id?: number;
  name?: string;
  symbol?: string;
  prices?: {
    usd: number;
  };
}

interface Wallet {
  id: number;
  currency: Cryptocurrency;
  balance: string;
  available_balance: string;
  locked_balance: string;
}

interface ExchangeCalculation {
  from_amount: number;
  from_crypto: Cryptocurrency;
  to_amount: number;
  to_crypto: Cryptocurrency;
  rate: number;
  fee_percentage: number;
  fee_amount: number;
  fee_usd?: number;
}

function ExchangePageClientInner() {
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
        const [cryptoResp, pairsResp, walletsResp] = await Promise.all([
            api.get('/crypto/cryptocurrencies/'),
            api.get('/crypto/exchange-pairs/'),
            api.get('/crypto/wallets/')
        ]);
        
        const cryptoData = Array.isArray(cryptoResp) ? cryptoResp : (cryptoResp as any).data;
        const pairsData = Array.isArray(pairsResp) ? pairsResp : (pairsResp as any).data;
        const walletsData = Array.isArray(walletsResp) ? walletsResp : (walletsResp as any).data;
        
        setCryptocurrencies(cryptoData);
        setExchangePairs(pairsData);
        setWallets(walletsData);
        
        // Если в URL есть параметр from_crypto, выбираем эту криптовалюту
        const fromCryptoParam = searchParams.get('from_crypto');
        if (fromCryptoParam && cryptoData.some((c: Cryptocurrency) => c.id === parseInt(fromCryptoParam))) {
          setFromCryptoId(parseInt(fromCryptoParam));
          
          // Находим подходящую пару для обмена
          const suitablePairs = pairsData.filter(
            (p: ExchangePair) => (typeof p.from_crypto === 'object' && p.from_crypto !== null ? p.from_crypto.id : p.from_crypto) === parseInt(fromCryptoParam)
          );
          
          if (suitablePairs.length > 0) {
            // Предпочитаем USDT или стейблкоины для обмена
            const usdtPair = suitablePairs.find(
              (p: ExchangePair) => (typeof p.to_crypto === 'object' && p.to_crypto !== null ? p.to_crypto.id : p.to_crypto) === 1 // Assuming USDT is represented by id 1
            );
            
            if (usdtPair) {
              setToCryptoId(
                typeof usdtPair.to_crypto === 'object' && usdtPair.to_crypto !== null
                  ? usdtPair.to_crypto.id
                  : usdtPair.to_crypto
              );
              setSelectedPair(usdtPair);
            } else {
              setToCryptoId(
                typeof suitablePairs[0].to_crypto === 'object' && suitablePairs[0].to_crypto !== null
                  ? suitablePairs[0].to_crypto.id
                  : suitablePairs[0].to_crypto
              );
              setSelectedPair(suitablePairs[0]);
            }
          }
        } else if (cryptoData.length > 0) {
          // По умолчанию выбираем первую криптовалюту с наибольшим балансом
          const userWallets = walletsData;
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
              const suitablePairs = pairsData.filter(
                (p: ExchangePair) => (typeof p.from_crypto === 'object' && p.from_crypto !== null ? p.from_crypto.id : p.from_crypto) === walletWithBalance.currency.id
              );
              
              if (suitablePairs.length > 0) {
                setToCryptoId(
                  typeof suitablePairs[0].to_crypto === 'object' && suitablePairs[0].to_crypto !== null
                    ? suitablePairs[0].to_crypto.id
                    : suitablePairs[0].to_crypto
                );
                setSelectedPair(suitablePairs[0]);
              }
            } else {
              // Если нет кошельков с балансом, выбираем первую криптовалюту
              setFromCryptoId(cryptoData[0].id);
              
              // И первую доступную пару обмена
              const firstPair = pairsData.find(
                (p: ExchangePair) => (typeof p.from_crypto === 'object' && p.from_crypto !== null ? p.from_crypto.id : p.from_crypto) === cryptoData[0].id
              );
              
              if (firstPair) {
                setToCryptoId(
                  typeof firstPair.to_crypto === 'object' && firstPair.to_crypto !== null
                    ? firstPair.to_crypto.id
                    : firstPair.to_crypto
                );
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
        p => (typeof p.from_crypto === 'object' && p.from_crypto !== null ? p.from_crypto.id : p.from_crypto) === fromCryptoId && (typeof p.to_crypto === 'object' && p.to_crypto !== null ? p.to_crypto.id : p.to_crypto) === toCryptoId
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

  // 1. Загрузка курсов при монтировании
  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const resp = await api.get('/crypto/prices/latest/');
        const data = Array.isArray(resp) ? resp : (resp as any).data;
        setPrices(data);
      } catch (error) {
        console.error('Ошибка при загрузке курсов:', error);
        setPrices([]);
      }
    };
    fetchPrices();
  }, []);

  // 2. Калькулятор на фронте
  useEffect(() => {
    const calculate = () => {
      if (
        !fromCryptoId ||
        !toCryptoId ||
        !amount ||
        isNaN(+amount) ||
        +amount <= 0 ||
        !selectedPair ||
        cryptocurrencies.length === 0 ||
        prices.length === 0
      ) {
        setCalculation(null);
        return;
      }
      // Для отладки
      console.log('prices', prices);
      // Для вашей структуры: crypto_id и prices.usd
      const fromPriceObj = prices.find((p: any) => p.crypto_id === fromCryptoId);
      const toPriceObj = prices.find((p: any) => p.crypto_id === toCryptoId);
      const fromPrice = fromPriceObj?.prices?.usd;
      const toPrice = toPriceObj?.prices?.usd;
      if (!fromPrice || !toPrice) {
        setCalculation(null);
        return;
      }
      const rate = parseFloat(String(fromPrice)) / parseFloat(String(toPrice));
      const rawToAmount = parseFloat(amount) * rate;
      let commission = 0;
      if (selectedPair?.custom_fee_percentage) {
        commission = parseFloat(selectedPair.custom_fee_percentage);
      } else if (
        typeof selectedPair?.from_crypto === 'object' &&
        selectedPair.from_crypto?.fee_percentage
      ) {
        commission = parseFloat(selectedPair.from_crypto.fee_percentage);
      }
      const fee = rawToAmount * (commission / 100);
      const toAmount = rawToAmount - fee;
      setCalculation({
        from_amount: parseFloat(amount),
        from_crypto: cryptocurrencies.find(c => c.id === fromCryptoId)!,
        to_amount: toAmount,
        to_crypto: cryptocurrencies.find(c => c.id === toCryptoId)!,
        rate,
        fee_percentage: commission,
        fee_amount: fee,
      });
    };
    calculate();
  }, [fromCryptoId, toCryptoId, amount, prices, selectedPair, cryptocurrencies]);

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

    // Найти первую доступную пару для нового fromCryptoId
    const suitablePairs = exchangePairs.filter(
      p => (typeof p.from_crypto === 'object' && p.from_crypto !== null ? p.from_crypto.id : p.from_crypto) === cryptoId
    );
    if (suitablePairs.length > 0) {
      setToCryptoId(
        typeof suitablePairs[0].to_crypto === 'object' && suitablePairs[0].to_crypto !== null
          ? suitablePairs[0].to_crypto.id
          : suitablePairs[0].to_crypto
      );
      setSelectedPair(suitablePairs[0]);
    } else {
      setToCryptoId(null);
      setSelectedPair(null);
    }
  };

  const handleToCryptoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setToCryptoId(Number(e.target.value));
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

  // Функция для обновления кошельков пользователя
  const refetchWallets = async () => {
    try {
      const walletsResp = await api.get('/crypto/wallets/');
      const walletsData = Array.isArray(walletsResp) ? walletsResp : (walletsResp as any).data;
      setWallets(walletsData);
    } catch (e) {
      // Можно обработать ошибку, если нужно
    }
  };

  // Отправка формы обмена
  const handleExchange = async () => {
    if (!selectedPair || !amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      setError("Пожалуйста, введите корректную сумму для обмена.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const exchangeData = {
        from_crypto_id: (typeof selectedPair.from_crypto === 'object' && selectedPair.from_crypto !== null ? selectedPair.from_crypto.id : selectedPair.from_crypto),
        to_crypto_id: (typeof selectedPair.to_crypto === 'object' && selectedPair.to_crypto !== null ? selectedPair.to_crypto.id : selectedPair.to_crypto),
        amount: parseFloat(amount),
      };

      const response = await api.post('/crypto/exchange/execute/', exchangeData);

      // Если response — это уже JSON-объект:
      if (response.success) {
        setError(null);
        setSuccess(true);
        setExchangeId(response.exchange_id);
        await refetchWallets(); // обязательно обновить кошельки!
      } else {
        setError(response.error || 'Произошла неизвестная ошибка при обмене.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Не удалось выполнить обмен. Проверьте баланс и попробуйте снова.');
    } finally {
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
              onClick={() => {
                setSuccess(false);
                setError(null);
              }} 
              className="text-purple-400 hover:text-purple-300 transition"
            >
              Новый обмен
            </button>
          </div>
        </div>
      </div>
    );
  }

  console.log('calculation', calculation);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Обмен криптовалют</h1>
        
        {!success && error && (
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
                <select aria-label="Криптовалюта для отправки" 
                  value={fromCryptoId || ''}
                  onChange={handleFromCryptoChange}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="" disabled>Выберите</option>
                  {cryptocurrencies.map(crypto => (
                    <option key={crypto.id} value={crypto.id}>
                      {crypto.symbol} (id={crypto.id})
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
              <button aria-label="Обмен местами"
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
                <div className="flex-1 bg-gray-600 border border-gray-600 rounded-lg px-4 py-3 text-white flex items-center" style={{ minHeight: 48 }}>
                  {(calculation &&
                    calculation.to_crypto.id === toCryptoId &&
                    typeof calculation.to_amount === 'number' &&
                    !isNaN(calculation.to_amount))
                    ? calculation.to_amount.toFixed(8)
                    : ''}
                </div>
                <select
                  aria-label="Криптовалюта для получения"
                  value={toCryptoId || ''}
                  onChange={handleToCryptoChange}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="" disabled>Выберите</option>
                  {exchangePairs
                    .filter(pair => (typeof pair.from_crypto === 'object' && pair.from_crypto !== null ? pair.from_crypto.id : pair.from_crypto) === fromCryptoId)
                    .map(pair => {
                      const toCryptoIdLocal = typeof pair.to_crypto === 'object' && pair.to_crypto !== null ? pair.to_crypto.id : pair.to_crypto;
                      const crypto = cryptocurrencies.find(c => c.id === toCryptoIdLocal);
                      return (
                        <option
                          key={toCryptoIdLocal}
                          value={toCryptoIdLocal}
                        >
                          {crypto ? `${crypto.symbol} (${crypto.name}) (id=${crypto.id})` : `id=${toCryptoIdLocal}`}
                        </option>
                      );
                    })}
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
                    <span>
                      1 {calculation.from_crypto.symbol} = {calculation.rate.toFixed(8)} {calculation.to_crypto.symbol}
                    </span>
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

        {/* Отладочная информация */}
        <pre style={{ color: 'white', background: '#222', fontSize: 12, marginTop: 16 }}>
          {JSON.stringify({ prices, fromCryptoId, toCryptoId, selectedPair, amount, calculation }, null, 2)}
        </pre>
      </div>
    </div>
  );
}

// Обёртка для requirements Suspense
export default function ExchangePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-white">Загрузка...</div>}>
      <ExchangePageClientInner />
    </Suspense>
  );
}