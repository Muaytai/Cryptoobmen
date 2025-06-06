'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import Link from 'next/link';

// --- Interfaces ---
interface Currency {
  id: number;
  name: string;
  symbol: string;
  icon: string;
  currency_type: string;
}

interface Wallet {
  id: number;
  currency: Currency;
  balance: string;
}

interface FiatCurrency {
  code: string;
  name: string;
}

interface CardDepositData {
  wallet: number;
  amount: number;
  currency: string;
  card_last4?: string;
  card_brand?: string;
}

// --- Component ---
export const DepositPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();

  // --- State ---
  // Data
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [fiatCurrencies, setFiatCurrencies] = useState<FiatCurrency[]>([]);
  
  // UI State
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [depositId, setDepositId] = useState<string | null>(null);

  // Form State
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [fiatCurrency, setFiatCurrency] = useState<string>('RUB');
  const [convertedAmount, setConvertedAmount] = useState<string>('0.00');
  const [cardNumber, setCardNumber] = useState<string>('');
  const [expiryDate, setExpiryDate] = useState<string>('');
  const [cvv, setCvv] = useState<string>('');

  // --- Effects ---
  // Initial data fetching
  useEffect(() => {
    if (authLoading) {
      setLoading(true);
      return;
    }
    if (!isAuthenticated) {
      const redirectPath = `/funds/deposit${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
      router.push(`/login?redirect=${encodeURIComponent(redirectPath)}`);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const [walletsResponse, fiatResponse] = await Promise.all([
          api.get('/crypto/wallets/'),
          api.get('/crypto/fiat/'),
        ]);

        const cryptoWallets = walletsResponse.data.filter((w: Wallet) => w.currency.currency_type.toLowerCase() !== 'fiat');
        setWallets(cryptoWallets);
        setFiatCurrencies(fiatResponse.data);

        // Set default fiat currency if available
        if (fiatResponse.data.length > 0) {
          setFiatCurrency(fiatResponse.data[0].code);
        }

        // Pre-select wallet if ID is in URL
        const walletIdParam = searchParams.get('wallet_id');
        if (walletIdParam) {
          const walletId = parseInt(walletIdParam);
          if (cryptoWallets.some((w: Wallet) => w.id === walletId)) {
            setSelectedWalletId(walletId);
          }
        }
        
      } catch (err) {
        console.error('Failed to fetch deposit page data:', err);
        setError('Не удалось загрузить данные. Пожалуйста, попробуйте обновить страницу.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [authLoading, isAuthenticated, router, searchParams]);

  // Exchange rate calculation
  useEffect(() => {
    const calculateRate = async () => {
      if (!selectedWalletId || !amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0 || wallets.length === 0) {
        setConvertedAmount('0.00');
        return;
      }
      const selectedWallet = wallets.find(w => w.id === selectedWalletId);
      if (!selectedWallet) return;

      try {
        const params = new URLSearchParams({
          source_currency_symbol: fiatCurrency,
          target_currency_symbol: selectedWallet.currency.symbol,
        });
        const response = await api.get(`/crypto/exchange-rate/?${params.toString()}`);
        const rate = response.data.rate;
        if (rate) {
          setConvertedAmount((parseFloat(amount) * rate).toFixed(8));
        }
      } catch (error) {
        console.error('Error fetching exchange rate:', error);
        setConvertedAmount('0.00');
      }
    };

    const timer = setTimeout(calculateRate, 300);
    return () => clearTimeout(timer);
  }, [selectedWalletId, amount, fiatCurrency, wallets]);

  // --- Memoized Values ---
  const selectedWallet = useMemo(() => wallets.find(w => w.id === selectedWalletId), [selectedWalletId, wallets]);

  // --- Handlers ---
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\s/g, '');
    const formattedValue = value.replace(/(\d{4})/g, '$1 ').trim();
    if (formattedValue.length <= 19) {
      setCardNumber(formattedValue);
    }
  };

  const handleExpiryDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/[^\d]/g, '');
    if (value.length > 2 && value.indexOf('/') === -1) {
      value = value.slice(0, 2) + '/' + value.slice(2);
    }
    if (value.length <= 5) {
      setExpiryDate(value);
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWalletId || !amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0 || !cardNumber || !expiryDate || !cvv) {
      setError('Пожалуйста, заполните все поля корректно.');
      return;
    }
    
    // Card Validation
    if (cardNumber.replace(/\s/g, '').length !== 16) {
        setError('Номер карты должен состоять из 16 цифр.');
        return;
    }
    if (!/^\d{3}$/.test(cvv)) {
        setError('CVV должен состоять из 3 цифр.');
        return;
    }
    const expiryRegex = /^(0[1-9]|1[0-2])\/?([0-9]{2})$/;
    const match = expiryDate.match(expiryRegex);
    if (!match) {
        setError('Неверный формат срока действия. Используйте ММ/ГГ.');
        return;
    }
    const [, month, year] = match;
    const currentYear = new Date().getFullYear() % 100;
    const currentMonth = new Date().getMonth() + 1;
    if (Number(year) < currentYear || (Number(year) === currentYear && Number(month) < currentMonth)) {
        setError('Срок действия карты истек.');
        return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const depositData: CardDepositData = {
        wallet: selectedWalletId,
        amount: parseFloat(amount),
        currency: fiatCurrency,
        card_last4: cardNumber.replace(/\s/g, '').slice(-4),
        card_brand: 'Unknown', // Logic can be added to detect brand from number
      };
      
      const response = await api.post('/crypto/card-deposits/', depositData);

      if (response && response.data && response.data.deposit_id) {
        setSuccess(true);
        setDepositId(response.data.deposit_id);
      } else {
        setError((response.data as any)?.detail || 'Произошла ошибка при создании депозита.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Неизвестная ошибка сервера.');
    } finally {
      setSubmitting(false);
    }
  };

  // --- Render Logic ---
  if (loading) {
    return <div className="text-center p-10">Загрузка...</div>;
  }
  
  if (error) {
    return <div className="container mx-auto p-4 text-center text-red-500">{error}</div>;
  }

  if (success) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h2 className="text-2xl font-bold text-green-500 mb-4">Заявка на пополнение принята!</h2>
        <p>Ваша заявка на пополнение (ID: {depositId}) успешно создана и находится в обработке.</p>
        <p>Средства поступят на ваш кошелек в ближайшее время.</p>
        <Link href="/wallet" className="mt-6 inline-block bg-indigo-600 text-white font-bold py-2 px-4 rounded hover:bg-indigo-700">
          Вернуться в кошелек
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6 text-center">Пополнение кошелька</h1>
      <div className="max-w-lg mx-auto bg-gray-800 p-8 rounded-lg shadow-lg">
        <form onSubmit={handleSubmit}>
          {/* Wallet Selector */}
          <div className="mb-4">
            <label htmlFor="wallet" className="block text-sm font-medium text-gray-300 mb-2">
              Выберите кошелек для пополнения
            </label>
            <select
              id="wallet"
              value={selectedWalletId ?? ''}
              onChange={(e) => setSelectedWalletId(Number(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm p-2.5 text-white focus:ring-indigo-500 focus:border-indigo-500"
              required
            >
              <option value="" disabled>-- Выберите криптовалюту --</option>
              {wallets.map((wallet) => (
                <option key={wallet.id} value={wallet.id}>
                  {wallet.currency.name} ({wallet.currency.symbol})
                </option>
              ))}
            </select>
          </div>

          {/* Amount and Fiat Currency */}
          <div className="mb-4">
            <label htmlFor="amount" className="block text-sm font-medium text-gray-300 mb-2">
              Сумма
            </label>
            <div className="flex items-center">
              <input
                type="number"
                id="amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="flex-grow w-full bg-gray-700 border border-gray-600 rounded-l-md p-2.5 text-white focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="1000"
                required
                min="0"
                step="any"
              />
              <select
                id="fiat-currency"
                value={fiatCurrency}
                onChange={(e) => setFiatCurrency(e.target.value)}
                className="bg-gray-700 border-t border-b border-r border-gray-600 rounded-r-md p-2.5 text-white focus:ring-indigo-500 focus:border-indigo-500 h-[46px]"
              >
                {fiatCurrencies.map(fiat => (
                  <option key={fiat.code} value={fiat.code}>
                    {fiat.code}
                  </option>
                ))}
              </select>
            </div>
            {selectedWallet && parseFloat(amount) > 0 && (
              <p className="text-sm text-gray-400 mt-2">
                Вы получите примерно: {convertedAmount} {selectedWallet.currency.symbol}
              </p>
            )}
          </div>

          {/* Card Details */}
          <div className="mb-4">
            <h3 className="text-lg font-medium mb-2">Данные банковской карты</h3>
            <div className="mb-4">
              <label htmlFor="cardNumber" className="block text-sm font-medium text-gray-300 mb-2">
                Номер карты
              </label>
              <input
                type="text"
                id="cardNumber"
                value={cardNumber}
                onChange={handleCardNumberChange}
                className="w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm p-2.5 text-white"
                placeholder="0000 0000 0000 0000"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="expiryDate" className="block text-sm font-medium text-gray-300 mb-2">
                  Срок (MM/YY)
                </label>
                <input
                  type="text"
                  id="expiryDate"
                  value={expiryDate}
                  onChange={handleExpiryDateChange}
                  className="w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm p-2.5 text-white"
                  placeholder="ММ/ГГ"
                  required
                />
              </div>
              <div>
                <label htmlFor="cvv" className="block text-sm font-medium text-gray-300 mb-2">
                  CVV
                </label>
                <input
                  type="text"
                  id="cvv"
                  value={cvv}
                  onChange={(e) => setCvv(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm p-2.5 text-white"
                  placeholder="123"
                  required
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || loading}
            className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-500 transition-colors"
          >
            {submitting ? 'Обработка...' : 'Пополнить'}
          </button>
        </form>
      </div>
    </div>
  );
};
