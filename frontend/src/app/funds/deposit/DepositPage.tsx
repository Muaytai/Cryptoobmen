'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { toast } from 'react-hot-toast';

// --- Interfaces ---
interface DepositInfo {
  system_wallet_address: string;
  memo: string;
}

interface Currency {
    id: number;
    name: string;
    symbol: string;
    icon: string;
    network: string; // e.g., 'TRC20', 'BEP20'
}

type DepositStatus = 'loading' | 'select_currency' | 'waiting' | 'completed' | 'error';

// --- Component ---
export const DepositPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();

  // --- State ---
  const wsRef = useRef<WebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [depositInfo, setDepositInfo] = useState<DepositInfo | null>(null);
  const [status, setStatus] = useState<DepositStatus>('loading');
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState<Currency | null>(null);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('');
  const [networkOptions, setNetworkOptions] = useState<string[]>([]);
  const [copiedAddress, setCopiedAddress] = useState<boolean>(false);
  const [copiedMemo, setCopiedMemo] = useState<boolean>(false);

  // Загрузка доступных валют
  const fetchCurrencies = useCallback(async () => {
    try {
      const response = await api.get('/crypto/cryptocurrencies/');
      // Фильтруем только криптовалюты (не фиатные)
      const cryptos = response.data.filter((c: any) => c.currency_type === 'crypto');
      setCurrencies(cryptos);
      
      // Проверяем параметры URL
      const walletIdParam = searchParams.get('wallet_id');
      const cryptoParam = searchParams.get('crypto');
      
      if (cryptoParam) {
        const matchedCrypto = cryptos.find((c: Currency) => c.symbol.toLowerCase() === cryptoParam.toLowerCase());
        if (matchedCrypto) {
          setSelectedCurrency(matchedCrypto);
          setSelectedNetwork(matchedCrypto.network);
          return;
        }
      }
      
      setStatus('select_currency');
    } catch (err) {
      console.error('Ошибка при получении списка валют:', err);
      setError('Не удалось загрузить список доступных валют');
      setStatus('error');
    }
  }, [searchParams]);

  // Загрузка информации для депозита
  const fetchDepositInfo = useCallback(async () => {
    if (!selectedCurrency || !selectedNetwork) return;
    
    setStatus('loading');
    setError(null);
    try {
      // console.log('Requesting deposit info for:', { 
      //   currency_symbol: selectedCurrency.symbol, 
      //   network: selectedNetwork 
      // });
      const response = await api.post('/crypto/deposit/info/', {
        currency_symbol: selectedCurrency.symbol,
        network: selectedNetwork,
      });
      setDepositInfo({
          system_wallet_address: response.data.address,
          memo: response.data.memo,
      });
      setStatus('waiting');

    } catch (err: any) {
      console.error('Failed to fetch deposit info:', err);
      setError(err.message || 'Не удалось получить данные для пополнения.');
      setStatus('error');
    }
  }, [selectedCurrency, selectedNetwork]);

  // Обработка выбора валюты
  const handleCurrencySelect = (currency: Currency) => {
    setSelectedCurrency(currency);
    
    // Получаем доступные сети для выбранной валюты
    const networks = currencies
      .filter(c => c.symbol === currency.symbol)
      .map(c => c.network)
      .filter(Boolean);
    
    setNetworkOptions(networks);
    
    if (networks.length === 1) {
      setSelectedNetwork(networks[0]);
    } else if (networks.includes('TRC20')) {
      // По умолчанию выбираем TRC20 как самую распространенную и дешевую
      setSelectedNetwork('TRC20');
    } else {
      setSelectedNetwork(networks[0] || '');
    }
  };

  // Копирование в буфер обмена
  const copyToClipboard = (text: string, type: 'address' | 'memo') => {
    navigator.clipboard.writeText(text).then(
      () => {
        if (type === 'address') {
          setCopiedAddress(true);
          setTimeout(() => setCopiedAddress(false), 2000);
        } else {
          setCopiedMemo(true);
          setTimeout(() => setCopiedMemo(false), 2000);
        }
      },
      (err) => {
        console.error('Не удалось скопировать текст: ', err);
      }
    );
  };

  // Начальная загрузка
  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated) {
      router.push('/login?redirect=/funds/deposit');
      return;
    }

    fetchCurrencies();
  }, [authLoading, isAuthenticated, router, fetchCurrencies]);

  // Запрос информации о депозите при выборе валюты и сети
  useEffect(() => {
    console.log('useEffect triggered. selectedCurrency:', selectedCurrency, 'selectedNetwork:', selectedNetwork, 'depositInfo:', depositInfo);
    if (selectedCurrency && selectedNetwork && !depositInfo) {
      fetchDepositInfo();
    }
  }, [selectedCurrency, selectedNetwork, fetchDepositInfo, depositInfo]);

  // WebSocket Connection
  useEffect(() => {
    if (!depositInfo?.memo) return;

    if (wsRef.current) {
      wsRef.current.close();
    }
    
    const wsUrl = `ws://${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}/ws/deposit_status/${depositInfo.memo}/`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connection opened for memo:', depositInfo.memo);
      toast.success('Подключено к WebSocket для отслеживания депозита!');
    };

    wsRef.current.onmessage = (event) => {
      console.log('Received WebSocket message:', event.data);
      try {
        const data = JSON.parse(event.data);
        const st = data.status;
        if (st === 'used' || st === 'confirmed') {
          setStatus('completed');
          toast.success('Пополнение успешно подтверждено!');
          wsRef.current?.close();
        } else if (st === 'expired') {
          setStatus('error');
          toast.error('Срок действия пополнения истек.');
          wsRef.current?.close();
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
        toast.error('Ошибка при обработке данных пополнения.');
      }
    };

    wsRef.current.onerror = (event) => {
      console.error('WebSocket error:', event);
      toast.error('Ошибка WebSocket соединения.');
      setStatus('error');
      wsRef.current?.close();
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [depositInfo]);

  if (authLoading) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Проверка авторизации...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Перенаправление происходит в useEffect
  }
  
  const renderContent = () => {
    switch (status) {
      case 'loading':
        return (
          <div className="flex flex-col items-center justify-center p-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            <p className="mt-4 text-gray-300">Загрузка данных для пополнения...</p>
          </div>
        );
        
      case 'error':
        return (
          <div className="bg-red-900 bg-opacity-20 p-6 rounded-lg text-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold text-red-300 mb-4">Произошла ошибка</h2>
            <p className="text-red-200 mb-4">{error}</p>
            <button 
              onClick={() => setStatus('select_currency')}
              className="bg-red-700 hover:bg-red-600 text-white py-2 px-6 rounded-lg transition"
            >
              Попробовать снова
            </button>
          </div>
        );
        
      case 'select_currency':
        return (
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md">
            <h2 className="text-xl font-bold mb-6 text-center">Выберите валюту для пополнения</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-400 mb-2">Криптовалюта:</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {currencies
                  .filter((c, index, self) => 
                    index === self.findIndex(t => t.symbol === c.symbol)
                  )
                  .map(currency => (
                    <button
                      key={`${currency.symbol}`}
                      onClick={() => handleCurrencySelect(currency)}
                      className={`p-3 rounded-lg flex flex-col items-center justify-center transition ${
                        selectedCurrency?.symbol === currency.symbol 
                          ? 'bg-purple-700 border-2 border-purple-500' 
                          : 'bg-gray-700 hover:bg-gray-650'
                      }`}
                    >
                      {currency.icon ? (
                        <Image
                          src={currency.icon.startsWith('http') ? currency.icon : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${currency.icon}`}
                          alt={currency.symbol}
                          width={32}
                          height={32}
                          className="rounded-full mb-2"
                          unoptimized
                        />
                      ) : (
                        <div className="w-8 h-8 bg-gray-600 rounded-full mb-2 flex items-center justify-center font-bold">
                          {currency.symbol.slice(0, 2)}
                        </div>
                      )}
                      <span className="text-sm">{currency.symbol}</span>
                    </button>
                  ))
                }
              </div>
            </div>
            
            {selectedCurrency && networkOptions.length > 1 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">Сеть:</label>
                <div className="grid grid-cols-2 gap-3">
                  {networkOptions.map(network => (
                    <button
                      key={network}
                      onClick={() => setSelectedNetwork(network)}
                      className={`p-3 rounded-lg text-center transition ${
                        selectedNetwork === network 
                          ? 'bg-purple-700 border-2 border-purple-500' 
                          : 'bg-gray-700 hover:bg-gray-650'
                      }`}
                    >
                      {network}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {selectedCurrency && selectedNetwork && (
              <button
                onClick={fetchDepositInfo}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg transition flex items-center justify-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Получить адрес для пополнения
              </button>
            )}
          </div>
        );
        
      case 'completed':
        return (
          <div className="text-center p-8 bg-green-900 bg-opacity-20 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <h2 className="text-2xl font-bold text-green-300 mb-4">Пополнение успешно!</h2>
            <p className="text-green-200 mb-6">Ваш баланс был успешно пополнен.</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/wallet" className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-6 rounded-lg transition">
                Перейти к кошельку
              </Link>
              <button 
                onClick={() => setStatus('select_currency')}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg transition"
              >
                Пополнить еще
              </button>
            </div>
          </div>
        );
        
      case 'waiting':
        console.log('Rendering waiting state. Current depositInfo:', depositInfo);
        if (!depositInfo) return null;
        
        return (
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md">
            <div className="flex items-center justify-center mb-6">
              {selectedCurrency?.icon ? (
                <Image
                  src={selectedCurrency.icon.startsWith('http') ? selectedCurrency.icon : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${selectedCurrency.icon}`}
                  alt={selectedCurrency.symbol}
                  width={48}
                  height={48}
                  className="rounded-full mr-3"
                  unoptimized
                />
              ) : (
                <div className="w-12 h-12 bg-gray-700 rounded-full mr-3 flex items-center justify-center font-bold">
                  {selectedCurrency?.symbol.slice(0, 2) || '??'}
                </div>
              )}
              <div>
                <h2 className="text-xl font-bold">{selectedCurrency?.name}</h2>
                <p className="text-gray-400">{selectedCurrency?.symbol} ({selectedNetwork})</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="deposit-address" className="block text-sm font-medium text-gray-400">Адрес кошелька для пополнения:</label>
              <div className="mt-1 relative">
                <input
                  id="deposit-address"
                  type="text"
                  readOnly
                  value={depositInfo.system_wallet_address}
                  className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-2 pr-10"
                />
                <button 
                  onClick={() => copyToClipboard(depositInfo.system_wallet_address, 'address')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                  title="Копировать адрес"
                >
                  {copiedAddress ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            
            <div className="mb-6">
              <label htmlFor="deposit-memo" className="block text-sm font-medium text-gray-400">MEMO (обязательно для зачисления):</label>
              <div className="mt-1 relative">
                <input
                  id="deposit-memo"
                  type="text"
                  readOnly
                  value={depositInfo.memo}
                  className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-2 pr-10"
                />
                <button 
                  onClick={() => copyToClipboard(depositInfo.memo, 'memo')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                  title="Копировать MEMO"
                >
                  {copiedMemo ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            
            <div className="bg-yellow-900 border-l-4 border-yellow-500 text-yellow-200 p-4 rounded-md mb-6">
              <h4 className="font-bold flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                ВАЖНО!
              </h4>
              <ul className="list-disc pl-5 mt-2 space-y-1 text-sm">
                <li>Отправляйте только {selectedCurrency?.symbol} в сети {selectedNetwork}.</li>
                <li>Обязательно укажите MEMO в комментарии к транзакции.</li>
                <li>Средства, отправленные без MEMO, могут быть утеряны.</li>
                <li>Минимальная сумма пополнения: 10 {selectedCurrency?.symbol}.</li>
              </ul>
            </div>
            
            <div className="bg-blue-900 border-l-4 border-blue-500 text-blue-200 p-4 rounded-md mb-6">
              <h4 className="font-bold flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Как пополнить кошелек:
              </h4>
              <ol className="list-decimal pl-5 mt-2 space-y-1 text-sm">
                <li>Скопируйте адрес и MEMO, нажав на соответствующие кнопки.</li>
                <li>Откройте ваш внешний кошелек или биржу.</li>
                <li>Создайте новый перевод на указанный адрес.</li>
                <li>Обязательно укажите MEMO в поле комментария/примечания.</li>
                <li>После отправки средств дождитесь подтверждения сети.</li>
              </ol>
            </div>
            
            <div className="mt-4 text-center text-blue-400 animate-pulse flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Ожидаем поступления средств...
            </div>
            
            <div className="mt-6 text-center">
              <button 
                onClick={() => setStatus('select_currency')}
                className="text-purple-400 hover:text-purple-300 transition"
              >
                Выбрать другую валюту
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="container mx-auto p-4 flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-8 text-center">Пополнение кошелька</h1>
      {renderContent()}
    </div>
  );
};

export default DepositPage;
