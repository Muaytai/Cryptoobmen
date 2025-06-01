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

interface InvestmentPlan {
  id: number;
  name: string;
  description: string;
  crypto: {
    id: number;
    name: string;
    symbol: string;
    icon: string;
  };
  interest_rate: string;
  duration_value: number;
  duration_unit: string;
  min_investment: string;
  max_investment: string;
  early_withdrawal_allowed: boolean;
  early_withdrawal_fee: string;
}

interface NewInvestmentData {
  wallet: number;
  plan: number;
  amount: number;
}

export const NewInvestmentPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { tokens, user } = useAuthStore();
  const token = tokens?.access;

  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [plans, setPlans] = useState<InvestmentPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [investmentId, setInvestmentId] = useState<string | null>(null);

  // Данные формы
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [expectedReturn, setExpectedReturn] = useState<string>('0');

  // Получение данных кошельков и инвестиционных планов
  useEffect(() => {
    const fetchData = async () => {
      if (!token) {
        router.push('/login?redirect=profile/investments/new');
        return;
      }

      try {
        setLoading(true);
        
        // Получаем кошельки пользователя
        const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/wallets/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setWallets(walletsResponse.data);
        
        // Если в URL есть параметр wallet_id, выбираем этот кошелек
        const walletId = searchParams.get('wallet_id');
        if (
          walletId &&
          walletsResponse.data.some((w: Wallet) => w.id === parseInt(walletId))
        ) {
          setSelectedWalletId(parseInt(walletId));
          const selectedWallet = walletsResponse.data.find((w: Wallet) => w.id === parseInt(walletId));
          if (selectedWallet && selectedWallet.crypto && selectedWallet.crypto.id) {
            const plansResponse = await axios.get(
              `${process.env.NEXT_PUBLIC_API_URL}/crypto/investment-plans/by_crypto/?crypto_id=${selectedWallet.crypto.id}`
            );
            setPlans(plansResponse.data);
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
  }, [token, router, searchParams]);

  // Загрузка инвестиционных планов при выборе кошелька
  useEffect(() => {
    const loadPlans = async () => {
      if (selectedWalletId) {
        try {
          const selectedWallet = wallets.find(w => w.id === selectedWalletId);
          if (selectedWallet && selectedWallet.crypto && selectedWallet.crypto.id) {
            const plansResponse = await axios.get(
              `${process.env.NEXT_PUBLIC_API_URL}/crypto/investment-plans/by_crypto/?crypto_id=${selectedWallet.crypto.id}`
            );
            setPlans(plansResponse.data);
            setSelectedPlanId(null); // Сбрасываем выбранный план при смене кошелька
            setAmount(''); // Сбрасываем сумму при смене кошелька
          }
        } catch (err) {
          console.error('Ошибка при получении инвестиционных планов:', err);
          setError('Не удалось загрузить инвестиционные планы. Пожалуйста, попробуйте позже.');
        }
      } else {
        setPlans([]);
      }
    };

    loadPlans();
  }, [selectedWalletId, wallets]);

  // Расчет ожидаемой прибыли при изменении суммы или плана
  useEffect(() => {
    if (selectedPlanId && amount && parseFloat(amount) > 0) {
      const selectedPlan = plans.find(p => p.id === selectedPlanId);
      if (selectedPlan) {
        const principal = parseFloat(amount);
        const interestRate = parseFloat(selectedPlan.interest_rate) / 100;
        
        // Расчет прибыли в зависимости от срока инвестиции
        let returnAmount = principal;
        
        // Простой расчет для примера (в реальном приложении может быть сложнее)
        if (selectedPlan.duration_unit === 'day') {
          returnAmount += principal * interestRate * (selectedPlan.duration_value / 365);
        } else if (selectedPlan.duration_unit === 'week') {
          returnAmount += principal * interestRate * (selectedPlan.duration_value * 7 / 365);
        } else if (selectedPlan.duration_unit === 'month') {
          returnAmount += principal * interestRate * (selectedPlan.duration_value / 12);
        } else if (selectedPlan.duration_unit === 'year') {
          returnAmount += principal * interestRate * selectedPlan.duration_value;
        }
        
        setExpectedReturn(returnAmount.toFixed(8));
      }
    } else {
      setExpectedReturn('0');
    }
  }, [selectedPlanId, amount, plans]);

  // Обработчики изменения полей формы
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Разрешаем только числа и одну точку
    if (/^\d*\.?\d*$/.test(value) || value === '') {
      setAmount(value);
    }
  };

  // Получение максимально доступной суммы для инвестирования
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

  // Проверка, соответствует ли сумма ограничениям плана
  const isAmountValid = (): boolean => {
    if (!selectedPlanId || !amount || parseFloat(amount) <= 0) return false;
    
    const selectedPlan = plans.find(p => p.id === selectedPlanId);
    if (!selectedPlan) return false;
    
    const amountValue = parseFloat(amount);
    const minInvestment = parseFloat(selectedPlan.min_investment);
    const maxInvestment = parseFloat(selectedPlan.max_investment);
    
    return amountValue >= minInvestment && amountValue <= maxInvestment;
  };

  // Отправка формы
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedWalletId || !selectedPlanId) {
      setError('Пожалуйста, выберите кошелек и инвестиционный план');
      return;
    }
    
    if (!amount || parseFloat(amount) <= 0) {
      setError('Пожалуйста, введите сумму инвестиции');
      return;
    }
    
    if (!isAmountValid()) {
      const selectedPlan = plans.find(p => p.id === selectedPlanId);
      setError(`Сумма инвестиции должна быть от ${selectedPlan?.min_investment} до ${selectedPlan?.max_investment} ${selectedPlan?.crypto.symbol}`);
      return;
    }
    
    try {
      setSubmitting(true);
      setError(null);
      
      const investmentData: NewInvestmentData = {
        wallet: selectedWalletId,
        plan: selectedPlanId,
        amount: parseFloat(amount)
      };
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/investments/`, 
        investmentData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSuccess(true);
      setInvestmentId(response.data.investment_id);
      
      // Очищаем форму
      setAmount('');
      setSelectedPlanId(null);
      
      setSubmitting(false);
    } catch (err: any) {
      console.error('Ошибка при отправке запроса:', err);
      setError(err.response?.data?.error || 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.');
      setSubmitting(false);
    }
  };

  // Форматирование длительности инвестиции
  const formatDuration = (plan: InvestmentPlan): string => {
    const value = plan.duration_value;
    let unit = '';
    
    switch (plan.duration_unit) {
      case 'day':
        unit = value === 1 ? 'день' : (value < 5 ? 'дня' : 'дней');
        break;
      case 'week':
        unit = value === 1 ? 'неделя' : (value < 5 ? 'недели' : 'недель');
        break;
      case 'month':
        unit = value === 1 ? 'месяц' : (value < 5 ? 'месяца' : 'месяцев');
        break;
      case 'year':
        unit = value === 1 ? 'год' : (value < 5 ? 'года' : 'лет');
        break;
    }
    
    return `${value} ${unit}`;
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
          <h2 className="text-2xl font-bold mb-4">Инвестиция успешно создана!</h2>
          <p className="mb-6">Идентификатор инвестиции: {investmentId}</p>
          <p className="mb-6 text-sm text-gray-400">
            Ваша инвестиция активирована. Вы можете отслеживать её статус и доходность в разделе "Инвестиции" вашего профиля.
          </p>
          <div className="flex flex-col space-y-3">
            <Link href="/profile/investments" className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition">
              Мои инвестиции
            </Link>
            <Link href="/wallet" className="text-purple-400 hover:text-purple-300 transition">
              Вернуться к кошельку
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">Создание новой инвестиции</h1>
        
        {error && (
          <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg mb-6">
            <p className="text-red-500">{error}</p>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-6 shadow-lg">
          {/* Выбор кошелька */}
          <div className="mb-6">
            <label className="block text-gray-300 mb-2">Выберите кошелек для инвестирования</label>
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
                        src={`${process.env.NEXT_PUBLIC_API_URL}${wallet.crypto.icon}`} 
                        alt={wallet.crypto.symbol} 
                        width={32} 
                        height={32} 
                        className="rounded-full mr-3"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-700 rounded-full mr-3 flex items-center justify-center">
                        {wallet.crypto && wallet.crypto.symbol ? (
                          wallet.crypto.symbol.slice(0, 2)
                        ) : (
                          ''
                        )}
                      </div>
                    )}
                    <div>
                      <p className="font-medium">{wallet.crypto.name}</p>
                      <p className="text-sm text-gray-400">
                        {parseFloat(wallet.available_balance).toFixed(8)} {wallet.crypto.symbol}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Выбор инвестиционного плана */}
          {selectedWalletId && (
            <div className="mb-6">
              <label className="block text-gray-300 mb-2">Выберите инвестиционный план</label>
              {plans.length > 0 ? (
                <div className="space-y-3">
                  {plans.map((plan) => (
                    <div 
                      key={plan.id}
                      onClick={() => setSelectedPlanId(plan.id)}
                      className={`
                        border rounded-lg p-4 cursor-pointer transition
                        ${selectedPlanId === plan.id 
                          ? 'border-purple-500 bg-purple-900 bg-opacity-20' 
                          : 'border-gray-700 hover:border-gray-500'}
                      `}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-lg font-semibold">{plan.name}</h3>
                        <span className="bg-purple-600 text-white px-2 py-1 rounded text-sm">
                          {plan.interest_rate}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 mb-2">{plan.description}</p>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <p className="text-gray-400">Срок:</p>
                          <p>{formatDuration(plan)}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Мин. инвестиция:</p>
                          <p>{parseFloat(plan.min_investment).toFixed(8)} {plan.crypto.symbol}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Макс. инвестиция:</p>
                          <p>{parseFloat(plan.max_investment).toFixed(8)} {plan.crypto.symbol}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Досрочный вывод:</p>
                          <p>
                            {plan.early_withdrawal_allowed 
                              ? `Доступен (комиссия ${plan.early_withdrawal_fee}%)` 
                              : 'Недоступен'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-700 p-4 rounded-lg text-center">
                  <p className="text-gray-300">
                    Для выбранной криптовалюты нет доступных инвестиционных планов
                  </p>
                </div>
              )}
            </div>
          )}
          
          {/* Сумма инвестиции */}
          {selectedWalletId && selectedPlanId && (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="amount" className="block text-gray-300">Сумма инвестиции</label>
                <button 
                  type="button"
                  onClick={setMaxAmount}
                  className="text-sm text-purple-400 hover:text-purple-300"
                >
                  Макс. доступно: {parseFloat(getMaxAvailableAmount()).toFixed(8)}
                </button>
              </div>
              <div className="flex">
                <input
                  type="text"
                  id="amount"
                  value={amount}
                  onChange={handleAmountChange}
                  placeholder="0.00000000"
                  className="flex-grow bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              {/* Ограничения по сумме */}
              {selectedPlanId && (
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>
                    Мин: {parseFloat(plans.find(p => p.id === selectedPlanId)?.min_investment || '0').toFixed(8)}
                  </span>
                  <span>
                    Макс: {parseFloat(plans.find(p => p.id === selectedPlanId)?.max_investment || '0').toFixed(8)}
                  </span>
                </div>
              )}
            </div>
          )}
          
          {/* Расчет ожидаемой прибыли */}
          {selectedPlanId && amount && parseFloat(amount) > 0 && (
            <div className="mb-6 bg-gray-700 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Ожидаемая прибыль</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Инвестиция:</p>
                  <p className="text-lg font-bold">
                    {parseFloat(amount).toFixed(8)} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Ожидаемый возврат:</p>
                  <p className="text-lg font-bold text-green-500">
                    {expectedReturn} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Прибыль:</p>
                  <p className="text-md font-medium text-green-400">
                    {(parseFloat(expectedReturn) - parseFloat(amount)).toFixed(8)} {wallets.find(w => w.id === selectedWalletId)?.crypto.symbol}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Доходность:</p>
                  <p className="text-md font-medium text-purple-400">
                    {plans.find(p => p.id === selectedPlanId)?.interest_rate}%
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-400 mt-3">
                * Расчет является приблизительным. Фактическая прибыль может отличаться.
              </p>
            </div>
          )}
          
          {/* Кнопка отправки */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={submitting || !selectedWalletId || !selectedPlanId || !amount || !isAmountValid()}
              className={`
                w-full py-3 px-6 rounded-lg text-white font-medium transition
                ${submitting || !selectedWalletId || !selectedPlanId || !amount || !isAmountValid()
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
                'Создать инвестицию'
              )}
            </button>
          </div>
          
          <p className="text-xs text-gray-400 mt-4 text-center">
            Создавая инвестицию, вы соглашаетесь с условиями инвестиционного плана и политикой платформы
          </p>
        </form>
      </div>
    </div>
  );
};
