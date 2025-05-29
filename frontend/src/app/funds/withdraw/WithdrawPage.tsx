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

interface WithdrawalData {
  wallet: number;
  amount: number;
  destination_address: string;
}

export const WithdrawPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { tokens, user } = useAuthStore();
  const token = tokens?.access;

  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [withdrawalId, setWithdrawalId] = useState<string | null>(null);

  // Данные формы
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [destinationAddress, setDestinationAddress] = useState<string>('');
  const [fee, setFee] = useState<string>('0');
  const [feeUsd, setFeeUsd] = useState<string>('0');
  const [netAmount, setNetAmount] = useState<string>('0');

  // Получение данных кошельков пользователя
  useEffect(() => {
    const fetchData = async () => {
      if (!token) {
        router.push('/login?redirect=funds/withdraw');
        return;
      }

      try {
        setLoading(true);
        
        // Получаем кошельки пользователя
        const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/wallets/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Получаем последние цены криптовалют
        const pricesResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/crypto-prices/latest/`);
        
        setWallets(walletsResponse.data);
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
  }, [token, router, searchParams]);

  // Обновление расчета комиссии при изменении суммы или кошелька
  useEffect(() => {
    if (selectedWalletId && amount && !isNaN(parseFloat(amount))) {
      const selectedWallet = wallets.find(w => w.id === selectedWalletId);
      if (selectedWallet) {
        const cryptoPrice = prices.find(p => p.crypto.id === selectedWallet.crypto.id);
        if (cryptoPrice) {
          // Расчет комиссии (примерно 0.1% от суммы вывода)
          const feePercentage = 0.1;
          const amountValue = parseFloat(amount);
          const feeValue = (amountValue * feePercentage) / 100;
          const netAmountValue = amountValue - feeValue;
          
          setFee(feeValue.toFixed(8));
          setFeeUsd((feeValue * parseFloat(cryptoPrice.price_usd)).toFixed(2));
          setNetAmount(netAmountValue.toFixed(8));
        }
      }
    } else {
      setFee('0');
      setFeeUsd('0');
      setNetAmount('0');
    }
  }, [selectedWalletId, amount, wallets, prices]);

  // Обработчики изменения полей формы
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Разрешаем только числа и одну точку
    if (/^\d*\.?\d*$/.test(value) || value === '') {
      setAmount(value);
    }
  };

  // Получение максимально доступной суммы для вывода
  const getMaxAvailableAmount = (): string => {
    if (!selectedWalletId) return '0';
    
    const wallet = wallets.find(w => w.id === selectedWalletId);
    if (!wallet) return '0';
    
    return wallet.available_balance;
  };

  // Установка максимальной доступной суммы
  const setMaxAmount = () => {
    const maxAmount = getMaxAvailableAmount();
    setAmount(maxAmount);
  };

  // Отправка формы
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedWalletId || !amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      setError('Пожалуйста, выберите кошелек и введите корректную сумму вывода');
      return;
    }
    
    if (!destinationAddress) {
      setError('Пожалуйста, введите адрес кошелька для вывода');
      return;
    }
    
    const wallet = wallets.find(w => w.id === selectedWalletId);
    if (!wallet) {
      setError('Выбранный кошелек не найден');
      return;
    }
    
    const amountValue = parseFloat(amount);
    const availableBalance = parseFloat(wallet.available_balance);
    
    if (amountValue > availableBalance) {
      setError(`Недостаточно средств. Доступно: ${availableBalance} ${wallet.crypto.symbol}`);
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      const withdrawalData: WithdrawalData = {
        wallet: selectedWalletId,
        amount: amountValue,
        destination_address: destinationAddress
      };
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/withdrawals/`, 
        withdrawalData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSuccess(true);
      setWithdrawalId(response.data.transaction_id);
      
      // Очищаем форму
      setAmount('');
      setDestinationAddress('');
      
      setSubmitting(false);
    } catch (err: any) {
      console.error('Ошибка при отправке запроса:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.');
      setSubmitting(false);
    }
  };

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
          <h2 className="text-2xl font-bold mb-4">Запрос на вывод успешно создан!</h2>
          <p className="mb-6">Идентификатор операции: {withdrawalId}</p>
          <p className="mb-6 text-sm text-gray-400">
            Ваш запрос на вывод средств принят в обработку. Обычно вывод занимает от 15 минут до нескольких часов.
            Вы можете отслеживать статус операции в разделе "История транзакций".
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
        <h1 className="text-3xl font-bold mb-8 text-center">Вывод средств</h1>
        
        {error && (
          <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
            <p className="text-red-500">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-6 shadow-lg">
          {/* Выбор кошелька */}
          <div className="mb-6">
            <label className="block text-gray-300 mb-2">Выберите кошелек для вывода</label>
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
                    ${parseFloat(wallet.available_balance) <= 0 ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <div className="flex items-center">
                    {wallet.crypto.icon ? (
                      <Image 
                        src={`${process.env.NEXT_PUBLIC_API_URL || ''}${wallet.crypto.icon}`} 
                        alt={wallet.crypto.symbol} 
                        width={32} 
                        height={32} 
                        className="rounded-full mr-3"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-700 rounded-full mr-3 flex items-center justify-center">
                        {wallet.crypto.symbol.slice(0, 2)}
                      </div>
                    )}
                    <div>
                      <p className="font-medium">{wallet.crypto.name}</p>
                      <p className="text-sm text-gray-400">
                        Доступно: {parseFloat(wallet.available_balance).toFixed(8)} {wallet.crypto.symbol}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Сумма вывода */}
          {selectedWalletId && (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="amount" className="block text-gray-300">Сумма вывода</label>
                <button 
                  type="button"
                  onClick={setMaxAmount}
                  className="text-sm text-purple-400 hover:text-purple-300"
                >
                  Максимум: {parseFloat(getMaxAvailableAmount()).toFixed(8)}
                </button>
              </div>
              <input
                type="text"
                id="amount"
                value={amount}
                onChange={handleAmountChange}
                placeholder="0.00000000"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          )}
          
          {/* Адрес для вывода */}
          {selectedWalletId && (
            <div className="mb-6">
              <label htmlFor="destinationAddress" className="block text-gray-300 mb-2">Адрес кошелька для вывода</label>
              <input
                type="text"
                id="destinationAddress"
                value={destinationAddress}
                onChange={(e) => setDestinationAddress(e.target.value)}
                placeholder={`Введите адрес ${wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}`}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <p className="text-xs text-gray-400 mt-1">
                Внимательно проверьте адрес перед отправкой. Транзакции в блокчейне необратимы.
              </p>
            </div>
          )}
          
          {/* Расчет комиссии */}
          {selectedWalletId && amount && parseFloat(amount) > 0 && (
            <div className="mb-6 bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Детали вывода</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Сумма вывода:</span>
                  <span>
                    {amount} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Комиссия сети:</span>
                  <span className="text-yellow-400">
                    {fee} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol} (≈${feeUsd})
                  </span>
                </div>
                <div className="border-t border-gray-600 my-2 pt-2 flex justify-between font-semibold">
                  <span>Вы получите:</span>
                  <span className="text-green-400">
                    {netAmount} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                * Фактическая комиссия сети может отличаться в зависимости от загруженности блокчейна.
              </p>
            </div>
          )}
          
          {/* Предупреждение */}
          <div className="mb-6 bg-yellow-500 bg-opacity-10 p-4 rounded-lg border border-yellow-500 border-opacity-20">
            <h3 className="text-yellow-500 font-semibold mb-2">Важно!</h3>
            <ul className="text-sm text-gray-300 space-y-1 list-disc pl-5">
              <li>Убедитесь, что адрес получателя корректен и поддерживает выбранную криптовалюту.</li>
              <li>Вывод средств может занять от 15 минут до нескольких часов в зависимости от загруженности сети.</li>
              <li>Минимальная сумма вывода зависит от выбранной криптовалюты.</li>
            </ul>
          </div>
          
          {/* Кнопка отправки */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={submitting || !selectedWalletId || !amount || !destinationAddress || parseFloat(amount) <= 0}
              className={`
                w-full py-3 px-6 rounded-lg text-white font-medium transition
                ${submitting || !selectedWalletId || !amount || !destinationAddress || parseFloat(amount) <= 0
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
                'Вывести средства'
              )}
            </button>
          </div>
          
          <p className="text-xs text-gray-400 mt-4 text-center">
            Нажимая кнопку "Вывести средства", вы соглашаетесь с условиями использования сервиса и подтверждаете, что указанный адрес принадлежит вам.
          </p>
        </form>
      </div>
    </div>
  );
};
