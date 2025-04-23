'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatCurrency } from '@/lib/utils';

// Временные данные о криптовалютах (в реальном приложении будут приходить с API)
const CURRENCIES = [
  { id: 1, code: 'BTC', name: 'Bitcoin', symbol: '₿', logo_url: '/crypto/btc.png', exchange_rate: 60000, is_active: true },
  { id: 2, code: 'ETH', name: 'Ethereum', symbol: 'Ξ', logo_url: '/crypto/eth.png', exchange_rate: 3000, is_active: true },
  { id: 3, code: 'USDT', name: 'Tether', symbol: '₮', logo_url: '/crypto/usdt.png', exchange_rate: 1, is_active: true },
  { id: 4, code: 'XRP', name: 'Ripple', symbol: 'XRP', logo_url: '/crypto/xrp.png', exchange_rate: 0.5, is_active: true },
  { id: 5, code: 'SOL', name: 'Solana', symbol: 'SOL', logo_url: '/crypto/sol.png', exchange_rate: 100, is_active: true },
];

export default function ExchangePage() {
  const [fromCurrency, setFromCurrency] = useState(CURRENCIES[0]);
  const [toCurrency, setToCurrency] = useState(CURRENCIES[2]);
  const [fromAmount, setFromAmount] = useState<number | ''>('');
  const [toAmount, setToAmount] = useState<number | ''>('');

  // Функция для расчета обмена
  const calculateExchange = (amount: number, from: typeof CURRENCIES[0], to: typeof CURRENCIES[0]) => {
    return (amount * from.exchange_rate) / to.exchange_rate;
  };

  // Обработчик изменения суммы "from"
  const handleFromAmountChange = (value: number | '') => {
    setFromAmount(value);
    if (value !== '') {
      const calculatedAmount = calculateExchange(value, fromCurrency, toCurrency);
      setToAmount(parseFloat(calculatedAmount.toFixed(8)));
    } else {
      setToAmount('');
    }
  };

  // Обработчик изменения суммы "to"
  const handleToAmountChange = (value: number | '') => {
    setToAmount(value);
    if (value !== '') {
      const calculatedAmount = calculateExchange(value, toCurrency, fromCurrency);
      setFromAmount(parseFloat(calculatedAmount.toFixed(8)));
    } else {
      setFromAmount('');
    }
  };

  // Обработчик смены направления обмена
  const handleSwapCurrencies = () => {
    setFromCurrency(toCurrency);
    setToCurrency(fromCurrency);
    setFromAmount(toAmount);
    setToAmount(fromAmount);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">Обмен криптовалют</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Калькулятор обмена</h2>
            
            {/* Блок "Отдаете" */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Отдаете
              </label>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-3">
                  <Input
                    type="number"
                    value={fromAmount === '' ? '' : fromAmount.toString()}
                    onChange={(e) => handleFromAmountChange(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    placeholder="Введите сумму"
                    min={0}
                  />
                </div>
                <div className="md:col-span-1">
                  <select
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={fromCurrency.code}
                    onChange={(e) => {
                      const currency = CURRENCIES.find(c => c.code === e.target.value);
                      if (currency) {
                        setFromCurrency(currency);
                        if (fromAmount !== '') {
                          handleFromAmountChange(fromAmount);
                        }
                      }
                    }}
                  >
                    {CURRENCIES.map((currency) => (
                      <option key={currency.id} value={currency.code}>
                        {currency.code} - {currency.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            {/* Кнопка смены направления */}
            <div className="flex justify-center my-4">
              <Button
                variant="ghost"
                onClick={handleSwapCurrencies}
                className="rounded-full p-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </Button>
            </div>
            
            {/* Блок "Получаете" */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Получаете
              </label>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-3">
                  <Input
                    type="number"
                    value={toAmount === '' ? '' : toAmount.toString()}
                    onChange={(e) => handleToAmountChange(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    placeholder="Сумма к получению"
                    min={0}
                  />
                </div>
                <div className="md:col-span-1">
                  <select
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={toCurrency.code}
                    onChange={(e) => {
                      const currency = CURRENCIES.find(c => c.code === e.target.value);
                      if (currency) {
                        setToCurrency(currency);
                        if (fromAmount !== '') {
                          handleFromAmountChange(fromAmount);
                        }
                      }
                    }}
                  >
                    {CURRENCIES.map((currency) => (
                      <option key={currency.id} value={currency.code}>
                        {currency.code} - {currency.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            
            {/* Информация о курсе */}
            {fromAmount && toAmount ? (
              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md text-sm">
                <p>Курс обмена: 1 {fromCurrency.code} = {formatCurrency(fromCurrency.exchange_rate / toCurrency.exchange_rate, toCurrency.code)} {toCurrency.code}</p>
                <p>Минимальная сумма: {formatCurrency(0.001, fromCurrency.code)} {fromCurrency.code}</p>
                <p>Комиссия: 0.5%</p>
              </div>
            ) : null}
            
            {/* Кнопка обмена */}
            <div className="mt-6">
              <Button
                className="w-full py-3"
                disabled={!fromAmount || !toAmount || fromAmount <= 0}
              >
                Обменять {fromAmount ? `${fromAmount} ${fromCurrency.code} на ${toAmount} ${toCurrency.code}` : ''}
              </Button>
            </div>
          </div>
        </div>
        
        {/* Дополнительная информация */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Как работает обмен</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700 dark:text-gray-300">
            <li>Выберите криптовалюту, которую хотите обменять, и укажите сумму.</li>
            <li>Выберите криптовалюту, которую хотите получить.</li>
            <li>Система автоматически рассчитает сумму к получению по текущему курсу.</li>
            <li>Нажмите кнопку "Обменять" и следуйте инструкциям для завершения транзакции.</li>
            <li>После подтверждения транзакции средства будут отправлены на ваш кошелек.</li>
          </ol>
        </div>
      </div>
    </div>
  );
} 