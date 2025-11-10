'use client';

import React, { useState, useEffect } from 'react';
import apiClient from '@/lib/api/fetch';
import { QRCodeSVG } from 'qrcode.react';

interface CryptoCurrency {
  id: number;
  symbol: string;
  name: string;
  network: string;
}

interface DepositInfo {
  address: string;
  memo: string | null;
  currency_symbol: string;
  network: string;
}

const DepositForm = () => {
  const [currencies, setCurrencies] = useState<CryptoCurrency[]>([]);
  const [selectedCurrencyId, setSelectedCurrencyId] = useState<string>('');
  const [depositInfo, setDepositInfo] = useState<DepositInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFetchingCurrencies, setIsFetchingCurrencies] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchCurrencies = async () => {
      try {
        const response = await apiClient.get('/crypto/cryptocurrencies/');
        setCurrencies(response.data.results || response.data); // Адаптация под пагинацию DRF
        if (response.data.results.length > 0) {
          setSelectedCurrencyId(String(response.data.results[0].id));
        }
      } catch (err) {
        setError('Не удалось загрузить список валют.');
        console.error(err);
      } finally {
        setIsFetchingCurrencies(false);
      }
    };
    fetchCurrencies();
  }, []);

  const handleGetAddress = async () => {
    if (!selectedCurrencyId) return;

    const selectedCurrency = currencies.find(c => c.id === parseInt(selectedCurrencyId));
    if (!selectedCurrency) return;

    setIsLoading(true);
    setError('');
    setDepositInfo(null);

    try {
      const response = await apiClient.get(
        `/crypto/deposit/info/?currency_symbol=${selectedCurrency.symbol}&network=${selectedCurrency.network}`
      );
      setDepositInfo(response.data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Не удалось получить адрес. Попробуйте позже.';
      setError(errorMessage);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetchingCurrencies) {
    return <div className="text-center p-8">Загрузка доступных валют...</div>;
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md">
      <div className="mb-4">
        <label htmlFor="asset" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Выберите валюту для пополнения
        </label>
        <select
          id="asset"
          value={selectedCurrencyId}
          onChange={(e) => setSelectedCurrencyId(e.target.value)}
          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          {currencies.map((currency) => (
            <option key={currency.id} value={currency.id}>
              {currency.name} ({currency.symbol} - {currency.network})
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleGetAddress}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
        disabled={isLoading || !selectedCurrencyId}
      >
        {isLoading ? 'Загрузка...' : 'Получить адрес для пополнения'}
      </button>

      {error && <p className="text-red-500 text-sm mt-4 text-center">{error}</p>}

      {depositInfo && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-red-600 dark:text-red-400 font-bold text-center mb-4">
            ВНИМАНИЕ: Отправляйте только {depositInfo.currency_symbol} в сети {depositInfo.network}.
          </p>
          
          <div className="flex justify-center my-4">
            <QRCodeSVG
              value={depositInfo.address}
              size={160}
              bgColor={"#ffffff"}
              fgColor={"#000000"}
              level={"Q"}
              includeMargin={false}
            />
          </div>

          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Адрес</label>
            <p className="break-all font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">{depositInfo.address}</p>
          </div>
          
          {depositInfo.memo && (
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">MEMO</label>
              <p className="break-all font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">{depositInfo.memo}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DepositForm;
