'use client';

import React, { useState } from 'react';
import apiClient from '@/lib/api/fetch'; // Исправлен импорт на default

// Mock data, позже будем получать с бэкенда
const supportedAssets: Record<string, string[]> = {
  USDT: ['TRC20', 'ERC20', 'BEP20'],
  BTC: ['Bitcoin'],
  ETH: ['ERC20'],
};

interface DepositInfo {
  address: string;
  memo: string;
  currency: string;
  network: string;
}

const DepositForm = () => {
  const [selectedAsset, setSelectedAsset] = useState<string>('USDT');
  const [selectedNetwork, setSelectedNetwork] = useState<string>('TRC20');
  const [depositInfo, setDepositInfo] = useState<DepositInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleAssetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const asset = e.target.value;
    setSelectedAsset(asset);
    // Сбрасываем сеть при смене актива
    setSelectedNetwork(supportedAssets[asset][0]);
    setDepositInfo(null);
  };

  const handleGetAddress = async () => {
    setIsLoading(true);
    setError('');
    setDepositInfo(null);
    try {
      const response = await apiClient.post('/crypto/deposit/info/', {
        currency_symbol: selectedAsset,
        network: selectedNetwork,
      });
      setDepositInfo(response.data);
    } catch (err) {
      setError('Не удалось получить адрес. Попробуйте позже.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const networksForSelectedAsset = supportedAssets[selectedAsset] || [];

  return (
    <div className="max-w-md mx-auto p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md">
      <div className="mb-4">
        <label htmlFor="asset" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Криптовалюта
        </label>
        <select
          id="asset"
          value={selectedAsset}
          onChange={handleAssetChange}
          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          {Object.keys(supportedAssets).map((asset) => (
            <option key={asset} value={asset}>
              {asset}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-6">
        <label htmlFor="network" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Сеть
        </label>
        <select
          id="network"
          value={selectedNetwork}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedNetwork(e.target.value)}
          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          disabled={networksForSelectedAsset.length <= 1}
        >
          {networksForSelectedAsset.map((network) => (
            <option key={network} value={network}>
              {network}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleGetAddress}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
        disabled={isLoading}
      >
        {isLoading ? 'Загрузка...' : 'Получить адрес для пополнения'}
      </button>

      {error && <p className="text-red-500 text-sm mt-4 text-center">{error}</p>}

      {depositInfo && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-red-600 dark:text-red-400 font-bold text-center mb-4">
            ВНИМАНИЕ: Отправляйте только {depositInfo.currency} в сети {depositInfo.network}.
          </p>
          
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Адрес</label>
            <p className="break-all font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">{depositInfo.address}</p>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">MEMO</label>
            <p className="break-all font-mono bg-gray-100 dark:bg-gray-800 p-2 rounded">{depositInfo.memo}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DepositForm; 