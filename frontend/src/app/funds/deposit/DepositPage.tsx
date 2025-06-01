'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import axios from 'axios';
import Image from 'next/image';
import Link from 'next/link';

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

interface CardDepositData {
  wallet: number;
  amount: number;
  currency: string;
  card_last4?: string;
  card_brand?: string;
}

export const DepositPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { tokens, user, isAuthenticated } = useAuthStore();
  const token = tokens?.access;

  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [depositId, setDepositId] = useState<string | null>(null);

  // Данные формы
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [currency, setCurrency] = useState<string>('RUB');
  const [cryptoAmount, setCryptoAmount] = useState<string>('0');
  const [exchangeRate, setExchangeRate] = useState<number>(0);
  const [cardNumber, setCardNumber] = useState<string>('');
  const [cardExpiry, setCardExpiry] = useState<string>('');
  const [cardCvv, setCardCvv] = useState<string>('');
  const [cardHolder, setCardHolder] = useState<string>('');

  // Новое состояние для отслеживания инициализации авторизации
  const [authInitialized, setAuthInitialized] = useState(false);

  useEffect(() => {
    // Если user !== undefined, значит, авторизация уже определена
    if (user !== undefined) {
      setAuthInitialized(true);
    }
  }, [user]);

  // Получение данных кошельков пользователя
  useEffect(() => {
    if (!authInitialized) return; // Ждём инициализации

    const fetchData = async () => {
      // Проверяем наличие токена и авторизации
      if (!token || !isAuthenticated) {
        console.log('Нет токена или не авторизован, перенаправляем на страницу входа');
        router.push('/login?redirect=funds/deposit');
        return;
      }
      
      // Дополнительная проверка на наличие токена в заголовках
      if (!token) {
        console.log('Токен отсутствует в заголовках');
        router.push('/login?redirect=funds/deposit');
        return;
      }

      try {
        setLoading(true);
        
        // Получаем кошельки пользователя
        const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/wallets/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Получаем последние цены криптовалют
        const pricesResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/prices/latest/`);
        
        // Маппинг структуры данных
        const mappedWallets = walletsResponse.data.map((w: any) => ({
          ...w,
          crypto: {
            id: w.crypto_id,
            name: w.crypto_name,
            symbol: w.crypto_symbol,
            icon: w.crypto_icon,
          },
        }));
        setWallets(mappedWallets);
        setPrices(pricesResponse.data);
        
        // Если в URL есть параметр wallet_id, выбираем этот кошелек
        const walletId = searchParams.get('wallet_id');
        if (walletId && walletsResponse.data.some((w: Wallet) => w.id === parseInt(walletId))) {
          setSelectedWalletId(parseInt(walletId));
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Ошибка при получении данных:', err);
        setError('Не удалось загрузить данные. Пожалуйста, попробуйте позже.');
        setLoading(false);
      }
    };

    fetchData();
  }, [token, isAuthenticated, authInitialized, router, searchParams]);

  // Обновление расчета криптовалюты при изменении суммы или кошелька
  useEffect(() => {
    if (selectedWalletId && amount && !isNaN(parseFloat(amount))) {
      const selectedWallet = wallets.find(w => w.id === selectedWalletId);
      if (selectedWallet) {
        const cryptoPrice = prices.find(p => p.crypto.id === selectedWallet.crypto.id);
        if (cryptoPrice) {
          // Курс обмена: сколько криптовалюты за 1 единицу фиатной валюты
          // Для простоты используем курс USD, в реальном приложении нужно использовать API для конвертации валют
          const rate = 1 / parseFloat(cryptoPrice.price_usd);
          // Для рубля используем примерный курс к USD
          const rubToUsdRate = 0.011; // примерно 90 рублей за 1 доллар
          
          let finalRate = rate;
          if (currency === 'RUB') {
            finalRate = rate * rubToUsdRate;
          }
          
          setExchangeRate(finalRate);
          setCryptoAmount((parseFloat(amount) * finalRate).toFixed(8));
        }
      }
    } else {
      setCryptoAmount('0');
    }
  }, [selectedWalletId, amount, currency, wallets, prices]);

  // Форматирование номера карты
  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }

    if (parts.length) {
      return parts.join(' ');
    } else {
      return value;
    }
  };

  // Форматирование срока действия карты
  const formatCardExpiry = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    
    if (v.length >= 2) {
      return `${v.substring(0, 2)}/${v.substring(2, 4)}`;
    }
    
    return v;
  };

  // Обработчики изменения полей формы
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCardNumber(formatCardNumber(value));
  };

  const handleCardExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCardExpiry(formatCardExpiry(value));
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Разрешаем только числа и одну точку
    if (/^\d*\.?\d*$/.test(value) || value === '') {
      setAmount(value);
    }
  };

  // Отправка формы
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedWalletId || !amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      setError('Пожалуйста, выберите кошелек и введите корректную сумму пополнения');
      return;
    }
    
    if (!cardNumber || !cardExpiry || !cardCvv || !cardHolder) {
      setError('Пожалуйста, заполните все данные карты');
      return;
    }
    
    // Базовая валидация карты
    if (cardNumber.replace(/\s/g, '').length !== 16) {
      setError('Неверный номер карты');
      return;
    }
    
    if (cardCvv.length !== 3) {
      setError('Неверный CVV код');
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      const depositData: CardDepositData = {
        wallet: selectedWalletId,
        amount: parseFloat(amount),
        currency: currency,
        card_last4: cardNumber.replace(/\s/g, '').slice(-4),
        card_brand: cardNumber.startsWith('4') ? 'Visa' : 
                    cardNumber.startsWith('5') ? 'MasterCard' : 
                    cardNumber.startsWith('3') ? 'American Express' : 'Unknown'
      };
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/card-deposits/`, 
        depositData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSuccess(true);
      setDepositId(response.data.deposit_id);
      
      // Очищаем форму
      setAmount('');
      setCardNumber('');
      setCardExpiry('');
      setCardCvv('');
      setCardHolder('');
      
      setSubmitting(false);
    } catch (err: any) {
      console.error('Ошибка при отправке запроса:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.');
      setSubmitting(false);
    }
  };

  if (!authInitialized) {
    return (
      <div className="container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Проверка авторизации...</p>
      </div>
    );
  }

  if (loading) {
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
          <h2 className="text-2xl font-bold mb-4">Запрос на пополнение успешно создан!</h2>
          <p className="mb-6">Идентификатор операции: {depositId}</p>
          <p className="mb-6 text-sm text-gray-400">
            Средства будут зачислены на ваш кошелек после подтверждения платежа. 
            Обычно это занимает от нескольких минут до часа.
          </p>
          <div className="flex flex-col space-y-3">
            <Link href="/wallet" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
              Вернуться к кошельку
            </Link>
            <Link href="/profile" className="text-purple-400 hover:text-purple-300 transition">
              Перейти в профиль
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Пополнение кошелька</h1>
        
        {error && (
          <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
            <p className="text-red-500">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-6 shadow-lg">
          {/* Выбор кошелька */}
          <div className="mb-6">
            <label className="block text-gray-300 mb-2">Выберите кошелек для пополнения</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {wallets.map((wallet) => (
                <div 
                  key={wallet.id}
                  onClick={() => setSelectedWalletId(wallet.id)}
                  className={`
                    border rounded-lg p-3 cursor-pointer transition
                    ${selectedWalletId === wallet.id 
                      ? 'border-purple-500 bg-purple-900 bg-opacity-20' 
                      : 'border-gray-700 hover:border-gray-500'}
                  `}
                >
                  <div className="flex items-center">
                    {wallet.crypto && wallet.crypto.icon ? (
                      <Image 
                        src={
                          wallet.crypto.icon.startsWith('http')
                            ? wallet.crypto.icon
                            : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${wallet.crypto.icon}`
                        }
                        alt={wallet.crypto.symbol}
                        width={32}
                        height={32}
                        className="rounded-full mr-3"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-700 rounded-full mr-3 flex items-center justify-center">
                        {wallet.crypto && wallet.crypto.symbol ? wallet.crypto.symbol.slice(0, 2) : ''}
                      </div>
                    )}
                    <div>
                      <p className="font-medium">{wallet.crypto.name}</p>
                      <p className="text-sm text-gray-400">{wallet.crypto.symbol}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Сумма и валюта */}
          <div className="mb-6">
            <label htmlFor="amount" className="block text-gray-300 mb-2">Сумма пополнения</label>
            <div className="flex">
              <input
                type="text"
                id="amount"
                value={amount}
                onChange={handleAmountChange}
                placeholder="0.00"
                className="flex-grow bg-gray-700 border border-gray-600 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-r-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>
          
          {/* Расчет криптовалюты */}
          {selectedWalletId && amount && parseFloat(amount) > 0 && (
            <div className="mb-6 bg-gray-700 p-4 rounded-lg">
              <p className="text-sm text-gray-300 mb-1">Вы получите примерно:</p>
              <p className="text-xl font-bold text-purple-400">
                {cryptoAmount} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Курс обмена: 1 {currency} = {exchangeRate.toFixed(8)} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Точная сумма будет рассчитана в момент зачисления средств
              </p>
            </div>
          )}
          
          {/* Данные карты */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">Данные банковской карты</h3>
            
            <div className="mb-4">
              <label htmlFor="cardNumber" className="block text-gray-300 mb-2">Номер карты</label>
              <input
                type="text"
                id="cardNumber"
                value={cardNumber}
                onChange={handleCardNumberChange}
                placeholder="0000 0000 0000 0000"
                maxLength={19}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label htmlFor="cardExpiry" className="block text-gray-300 mb-2">Срок действия</label>
                <input
                  type="text"
                  id="cardExpiry"
                  value={cardExpiry}
                  onChange={handleCardExpiryChange}
                  placeholder="MM/YY"
                  maxLength={5}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label htmlFor="cardCvv" className="block text-gray-300 mb-2">CVV</label>
                <input
                  type="password"
                  id="cardCvv"
                  value={cardCvv}
                  onChange={(e) => e.target.value.length <= 3 && setCardCvv(e.target.value.replace(/\D/g, ''))}
                  placeholder="123"
                  maxLength={3}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="cardHolder" className="block text-gray-300 mb-2">Имя держателя карты</label>
              <input
                type="text"
                id="cardHolder"
                value={cardHolder}
                onChange={(e) => setCardHolder(e.target.value.toUpperCase())}
                placeholder="IVAN IVANOV"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
          
          {/* Кнопка отправки */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={submitting}
              className={`
                w-full py-3 px-6 rounded-lg text-white font-medium transition
                ${submitting 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-purple-600 hover:bg-purple-700'}
              `}
            >
              {submitting ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></span>
                  Обработка...
                </span>
              ) : (
                'Пополнить кошелек'
              )}
            </button>
          </div>
          
          <p className="text-xs text-gray-400 mt-4 text-center">
            Нажимая кнопку "Пополнить кошелек", вы соглашаетесь с условиями использования сервиса и политикой конфиденциальности
          </p>
        </form>
      </div>
    </div>
  );
};
