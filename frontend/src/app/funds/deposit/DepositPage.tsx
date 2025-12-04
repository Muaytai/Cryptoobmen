'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { toast } from 'react-hot-toast';
import GasWarningModal from '@/components/modalWindows/GasWarningModal';

console.log('--- Файл DepositPage.tsx ЗАГРУЖЕН (v2 Fixed) ---');

// --- Interfaces ---
interface Wallet {
  id: string;
  network?: string;
  deposit_address?: string;
  currency: {
    id: string;
    symbol: string;
    name: string;
    icon?: string;
  };
}
interface DepositInfo {
  address: string;
  memo?: string | null;
  requires_memo?: boolean;
  qr_code?: string;
  currency_symbol?: string;
  network?: string;
  gas_info?: {
    estimated_gas_cost: string;
    currency_symbol: string;
    calculation_method: string;
  };
}

interface CurrencyApi {
  id: string;
  name: string;
  symbol: string;
  icon: string;
  network?: string | null;
  currency_type?: string;
  is_active?: boolean;
}

interface Currency {
    id: string;
    name: string;
    symbol: string;
    icon: string;
    networks: string[];
}

type DepositStatus = 'loading' | 'select_currency' | 'waiting' | 'completed' | 'error';

type DepositRequestParams =
  | { currency_id: string | number }
  | { currency_id: string | number; network: string | null };

interface PendingDepositData {
  address: string;
  memo?: string | null;
  requires_memo?: boolean;
  qr_code?: string;
  currency_symbol?: string;
  network?: string;
  gas_info?: DepositInfo['gas_info'];
}

const DEPOSIT_INFO_KEY = 'activeDepositDepositPage';

// --- Component ---
export const DepositPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();

  // --- State ---
  const wsRef = useRef<WebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userWallets, setUserWallets] = useState<Wallet[]>([]);
  const [depositInfo, setDepositInfo] = useState<DepositInfo | null>(null);
  const [status, setStatus] = useState<DepositStatus>('loading');
  const [availableCurrencies, setAvailableCurrencies] = useState<Currency[]>([]);
  const [selectedCurrency, setSelectedCurrency] = useState<string | null>(null);
  const [selectedNetwork, setSelectedNetwork] = useState<string | null>(null);
  const [networkOptions, setNetworkOptions] = useState<string[]>([]);
  const [copiedAddress, setCopiedAddress] = useState<boolean>(false);
  const [copiedMemo, setCopiedMemo] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showBypass, setShowBypass] = useState<boolean>(false);
  const [showGasWarning, setShowGasWarning] = useState<boolean>(false);
  const [pendingDepositData, setPendingDepositData] = useState<PendingDepositData | null>(null);

  // --- Fetch Logic (Pure) ---
  const fetchCurrencies = useCallback(async () => {
    console.log('DepositPage: fetchCurrencies начало выполнения');
    try {
      const resp = await api.get<CurrencyApi[]>('/crypto/cryptocurrencies/');
      const cryptoData: CurrencyApi[] = Array.isArray(resp)
        ? resp
        : ((resp as { data?: CurrencyApi[] }).data ?? []);
      
      if (!Array.isArray(cryptoData)) {
        console.error('DepositPage: данные о криптовалютах не являются массивом:', cryptoData);
        setError('Получены некорректные данные о криптовалютах');
        setStatus('error');
        return;
      }
      
      const cryptoMap = new Map<string, Currency>();

      cryptoData
        .filter((c) => c.currency_type === 'crypto' && c.is_active)
        .forEach((c) => {
          if (cryptoMap.has(c.symbol)) {
            const existing = cryptoMap.get(c.symbol)!;
            if (c.network && !existing.networks.includes(c.network)) {
              existing.networks.push(c.network);
            }
          } else {
            cryptoMap.set(c.symbol, {
              id: c.id, 
              name: c.name,
              symbol: c.symbol,
              icon: c.icon,
              networks: c.network ? [c.network] : [],
            });
          }
        });
      
      const aggregatedCurrencies = Array.from(cryptoMap.values());
      setAvailableCurrencies(aggregatedCurrencies);
    } catch (err: unknown) {
      console.error('DepositPage: ошибка при получении списка валют:', err);
      const message = err instanceof Error ? err.message : null;
      setError(message || 'Не удалось загрузить список доступных валют');
      setStatus('error');
    }
  }, []);

  const fetchUserWallets = useCallback(async () => {
    try {
      const resp = await api.get<Wallet[]>('/crypto/wallets/');
      const walletsData: Wallet[] = Array.isArray(resp)
        ? resp
        : ((resp as { data?: Wallet[] }).data ?? []);
      setUserWallets(walletsData);
    } catch (err: unknown) {
      console.error('DepositPage: не удалось загрузить кошельки пользователя', err);
    }
  }, []);

  // --- Event Handlers ---

  const handleBypass = useCallback(() => {
    console.log('DepositPage: принудительное продолжение');
    const hasToken = document.cookie.includes('access_token=') || document.cookie.includes('refresh_token=');
    if (hasToken) {
      useAuthStore.setState({ isLoading: false, isAuthenticated: true });
      setIsLoading(true);
      fetchCurrencies().then(() => fetchUserWallets()).finally(() => setIsLoading(false));
    } else {
      router.push('/login?redirect=/funds/deposit');
    }
  }, [router, fetchCurrencies, fetchUserWallets]);

  const handleOk = useCallback(() => {
    setDepositInfo(null);
    setStatus('select_currency');
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    router.push('/wallet');
  }, [router]);

  const handleCancel = useCallback(() => {
    localStorage.removeItem(DEPOSIT_INFO_KEY);
    setDepositInfo(null);
    setStatus('loading');
    if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
    }
    toast('Операция пополнения отменена.', {
      duration: 5000,
      position: 'top-center',
    });
    router.push('/funds/deposit');
  }, [router]);

  const handleGasWarningClose = useCallback(() => {
    setShowGasWarning(false);
    setPendingDepositData(null);
    setStatus('select_currency');
  }, []);

  const handleGasWarningConfirm = useCallback(() => {
    if (pendingDepositData) {
      setDepositInfo({
        address: pendingDepositData.address,
        memo: pendingDepositData.memo,
        requires_memo: pendingDepositData.requires_memo,
        qr_code: pendingDepositData.qr_code,
        currency_symbol: pendingDepositData.currency_symbol,
        network: pendingDepositData.network,
        gas_info: pendingDepositData.gas_info,
      });
      setStatus('waiting');
      setShowGasWarning(false);
      setPendingDepositData(null);
      
      toast.success('Адрес для пополнения получен', {
        duration: 5000,
        position: 'top-center',
      });
    }
  }, [pendingDepositData]);

  const handleCurrencySelection = useCallback((symbol: string) => {
    console.log('DepositPage: выбрана валюта:', symbol);
    setSelectedCurrency(symbol);
    setSelectedNetwork(null);
    
    // Получаем сети из кошельков пользователя
    const walletNetworks = userWallets
      .filter(w => w.currency.symbol === symbol)
      .map(w => w.network)
      .filter((n): n is string => !!n);

    // Если кошельков нет, используем справочные сети
    const currency = availableCurrencies.find(c => c.symbol === symbol);
    const referenceNetworks = currency ? (currency.networks || []) : [];

    const netsArr = Array.from(new Set([...walletNetworks, ...referenceNetworks]));
    setNetworkOptions(netsArr);
      
    if (netsArr.length === 1) {
      setSelectedNetwork(netsArr[0]);
    } else if (netsArr.length > 1) {
      if (walletNetworks.length === 1) {
        setSelectedNetwork(walletNetworks[0]);
      }
    }
  }, [availableCurrencies, userWallets]);

  const handleNetworkSelection = useCallback((network: string) => {
    console.log('DepositPage: выбрана сеть:', network);
    setSelectedNetwork(network);
  }, []);

  const handleRequestDeposit = useCallback(async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    console.log('DepositPage: запрос адреса для пополнения:', selectedCurrency, selectedNetwork);
    
    // Определяем актуальный список сетей для выбранной валюты
    const walletNetworks = userWallets
      .filter(w => w.currency.symbol === selectedCurrency)
      .map(w => w.network)
      .filter((n): n is string => !!n);
    const currencyObj = availableCurrencies.find(c => c.symbol === selectedCurrency);
    const referenceNetworks = currencyObj ? currencyObj.networks || [] : [];
    const allNetworks = Array.from(new Set([...walletNetworks, ...referenceNetworks]));

    let networkToUse = selectedNetwork || (allNetworks.length === 1 ? allNetworks[0] : null);
    if (selectedCurrency && selectedCurrency.toLowerCase() === 'btc') {
      networkToUse = 'bitcoin';
    }
    if (!selectedCurrency || !networkToUse) {
      setError('Пожалуйста, выберите криптовалюту и сеть.');
      toast.error('Выберите криптовалюту и сеть', {
        duration: 5000,
        position: 'top-center',
      });
      return;
    }
    
    setStatus('loading');
    setError(null);
    
    try {
      let currency: Currency | undefined;
      
      if (selectedNetwork) {
        currency = availableCurrencies.find(c => 
          c.symbol === selectedCurrency && 
          c.networks && 
          c.networks.includes(selectedNetwork)
        );
        
        if (!currency) {
          const userWalletForNetwork = userWallets.find(w => 
            w.currency.symbol === selectedCurrency && 
            w.network === selectedNetwork
          );
          
          if (userWalletForNetwork) {
            currency = availableCurrencies.find(c => c.id === userWalletForNetwork.currency.id);
          }
        }
        
        if (!currency) {
          const exactMatchCurrency = availableCurrencies.find(c => 
            c.symbol === selectedCurrency && 
            c.networks && 
            c.networks.some(network => 
              network.toLowerCase() === selectedNetwork!.toLowerCase() ||
              network.toLowerCase().includes(selectedNetwork!.toLowerCase()) ||
              selectedNetwork!.toLowerCase().includes(network.toLowerCase())
            )
          );
          if (exactMatchCurrency) {
            currency = exactMatchCurrency;
          }
        }
      }
      
      if (!currency) {
        currency = availableCurrencies.find(c => c.symbol === selectedCurrency);
      }
      
      if (!currency) {
          throw new Error("Selected currency not found");
      }

      let requestParams: DepositRequestParams;
      
      if (selectedNetwork || networkToUse) {
        requestParams = {
          currency_id: selectedCurrency,
          network: selectedNetwork || networkToUse,
        };
      } else {
        requestParams = {
          currency_id: currency.id,
        };
      }

      const response = await api.post(
        '/transactions/deposits/address/',
        requestParams,
      );

      const data = response as DepositInfo & { gas_info?: DepositInfo['gas_info'] };
      
      if (!data || !data.address) {
        throw new Error('Сервер вернул некорректные данные без адреса');
      }
      
      if (data.gas_info) {
        setPendingDepositData({
          address: data.address,
          memo: data.memo,
          requires_memo: data.requires_memo,
          qr_code: data.qr_code,
          currency_symbol: data.currency_symbol,
          network: data.network,
          gas_info: data.gas_info,
        });
        
        setShowGasWarning(true);
        setStatus('select_currency');
      } else {
        setDepositInfo({
          address: data.address,
          memo: data.memo || null,
          requires_memo: data.requires_memo || false,
          qr_code: data.qr_code,
          currency_symbol: data.currency_symbol,
          network: data.network,
          gas_info: data.gas_info,
        });
        
        setStatus('waiting');
        
        toast.success('Адрес для пополнения получен', {
          duration: 5000,
          position: 'top-center',
        });
      }
    } catch (err: unknown) {
      toast.dismiss();
      console.error('DepositPage: ошибка при получении информации для депозита:', err);
      
      let errorMessage = 'Не удалось получить данные для пополнения.';
      const message = err instanceof Error ? err.message : null;
      
      if (message?.includes('Failed to fetch') || message?.includes('Network Error')) {
        errorMessage = 'Нет подключения к серверу. Проверьте ваше интернет-соединение и повторите попытку.';
      } else if (message?.includes('400')) {
        errorMessage = 'Неверные параметры запроса. Пожалуйста, выберите другую валюту или сеть.';
      } else if (message?.includes('401') || message?.includes('403')) {
        errorMessage = 'Ошибка авторизации. Пожалуйста, войдите в систему снова.';
        toast.error('Требуется повторная авторизация', {
          duration: 5000,
          position: 'top-center',
        });
        router.push('/login?redirect=/funds/deposit');
        return;
      } else if (message?.includes('500')) {
        errorMessage = 'Ошибка сервера. Пожалуйста, повторите попытку позже.';
      } else if (message) {
        errorMessage = message;
      }
      
      toast.error(errorMessage, {
        duration: 5000,
        position: 'top-center',
      });
      setError(errorMessage);
      setStatus('error');
    }
  }, [selectedCurrency, selectedNetwork, router, userWallets, availableCurrencies]);

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

  // --- Effects ---

  // 1. Init: Check Auth & Fetch Data
  useEffect(() => {
    const init = async () => {
      try {
        if (authLoading) {
          await useAuthStore.getState().checkAuthStatus();
          const { isAuthenticated: currentAuth } = useAuthStore.getState();
          if (!currentAuth) {
            router.push('/login?redirect=/funds/deposit');
            return;
          }
        }
        
        if (!authLoading && isAuthenticated) {
          setIsLoading(true);
          await Promise.all([fetchCurrencies(), fetchUserWallets()]);
          setIsLoading(false);
          setStatus('select_currency');
        }
      } catch (error) {
        console.error('DepositPage: Ошибка при инициализации:', error);
      }
    };
    
    init();
    
    const bypassTimer = setTimeout(() => {
      if (authLoading) {
        setShowBypass(true);
      }
    }, 5000);
    
    return () => {
      clearTimeout(bypassTimer);
    };
  }, [authLoading, isAuthenticated, router, fetchCurrencies, fetchUserWallets]);

  // 2. Handle URL Params (depends on availableCurrencies & userWallets being ready)
  useEffect(() => {
    if (isLoading || availableCurrencies.length === 0) return;

    const cryptoParam = searchParams.get('crypto');
    
    if (cryptoParam) {
      // Поиск сначала по точному совпадению символа
      let matchedCrypto = availableCurrencies.find(c => 
        c.symbol.toLowerCase() === cryptoParam.toLowerCase()
      );
      
      // Если точного совпадения нет, ищем по частичному совпадению
      if (!matchedCrypto) {
        matchedCrypto = availableCurrencies.find(c => 
          c.symbol.toLowerCase().includes(cryptoParam.toLowerCase()) ||
          cryptoParam.toLowerCase().includes(c.symbol.toLowerCase())
        );
      }
      
      if (matchedCrypto) {
        setSelectedCurrency(matchedCrypto.symbol);
        
        // Логика определения сетей
        const walletNetworks = userWallets
          .filter(w => w.currency.symbol === matchedCrypto!.symbol)
          .map(w => w.network)
          .filter((n): n is string => !!n);

        const referenceNetworks = matchedCrypto.networks || [];
        const netsArr = Array.from(new Set([...walletNetworks, ...referenceNetworks]));
        
        setNetworkOptions(netsArr);
        
        if (netsArr.length === 1) {
          setSelectedNetwork(netsArr[0]);
          
          // Авто-запрос через 1.5 сек
          const timer = setTimeout(() => {
            const button = document.querySelector('[data-testid="request-deposit-button"]');
            if (button && button instanceof HTMLButtonElement) {
              button.click();
            }
          }, 1500);
          
          return () => clearTimeout(timer);
        }
      }
    }
  }, [isLoading, availableCurrencies, userWallets, searchParams]);

  // 3. WebSocket Connection
  useEffect(() => {
    if (!depositInfo || (!depositInfo.memo && !depositInfo.address)) {
      return; 
    }
    
    if (wsRef.current) return;

    const connect = () => {
      let wsBase = process.env.NEXT_PUBLIC_WS_URL;
      
      if (!wsBase) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        if (host.includes('localhost') || host.includes('127.0.0.1')) {
          wsBase = `${protocol}//${window.location.hostname}:8000`;
        } else {
          wsBase = `${protocol}//${host}/ws`;
        }
      }
      
      let wsUrl = '';
      let normalizedBase = wsBase.replace(/\/$/, '');
      if (!normalizedBase.endsWith('/ws')) {
        normalizedBase = normalizedBase.endsWith('/') ? `${normalizedBase}ws` : `${normalizedBase}/ws`;
      }
      
      if (depositInfo.memo) {
        wsUrl = `${normalizedBase}/deposit_status/${depositInfo.memo}/`;
      } else if (depositInfo.address) {
        wsUrl = `${normalizedBase}/deposit_status/address/${depositInfo.address}/`;
      } else {
        return;
      }

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          toast.success('Подключение к системе мониторинга установлено', {
            duration: 5000,
            position: 'top-center',
          });
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const currentDepositInfo = depositInfo;
            const successStatuses = ['used', 'completed', 'confirmed', 'pending'];
            const isSuccessStatus = data.status && successStatuses.includes(data.status);
            
            // Logic for success match...
            let matchFound = false;

            if (currentDepositInfo.memo && data.memo) {
               if (String(data.memo) === String(currentDepositInfo.memo) && isSuccessStatus) matchFound = true;
            }
            if (currentDepositInfo.address && data.address) {
               if (String(data.address).toLowerCase() === String(currentDepositInfo.address).toLowerCase() && isSuccessStatus) matchFound = true;
            }
            if (isSuccessStatus && !matchFound) {
               const hasMemoMatch = currentDepositInfo.memo && data.memo && String(data.memo) === String(currentDepositInfo.memo);
               const hasAddressMatch = currentDepositInfo.address && data.address && String(data.address).toLowerCase() === String(currentDepositInfo.address).toLowerCase();
               if (hasMemoMatch || hasAddressMatch) matchFound = true;
            }

            if (matchFound) {
                setStatus('completed');
                localStorage.removeItem(DEPOSIT_INFO_KEY);
                toast.success('Пополнение успешно зачислено!', {
                  duration: 5000,
                  position: 'top-center',
                });
                if (wsRef.current) {
                  wsRef.current.close();
                  wsRef.current = null;
                }
            }
          } catch (error) {
            console.error('DepositPage: Ошибка при обработке сообщения WebSocket:', error);
          }
        };

        ws.onclose = (event) => {
          wsRef.current = null;
          if (status === 'waiting') {
            setTimeout(() => {
              if (status === 'waiting') {
                connect();
              }
            }, 5000);
          }
        };
      } catch (error) {
        console.error('Ошибка при создании WebSocket соединения:', error);
        wsRef.current = null;
      }
    };

    const timer = setTimeout(() => {
      connect();
    }, 500);

    return () => {
      clearTimeout(timer);
      if (wsRef.current) {
        const ws = wsRef.current;
        wsRef.current = null;
        ws.onclose = null;
        ws.close();
      }
    };
  }, [depositInfo, status]); // status is needed for reconnection logic

  // --- Render ---

  if (authLoading && !depositInfo) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Проверка авторизации...</p>
        
        {showBypass && (
          <div className="mt-8 text-center">
            <p className="text-amber-400 mb-3">Авторизация занимает больше времени, чем обычно</p>
            <button
              onClick={handleBypass}
              className="bg-amber-600 hover:bg-amber-700 text-white py-2 px-4 rounded-lg text-sm"
            >
              Продолжить без проверки
            </button>
          </div>
        )}
      </div>
    );
  }

  if (!isAuthenticated && !depositInfo) {
    return null;
  }
  
  if (isLoading) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка данных...</p>
      </div>
    );
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
            <h2 className="text-xl font-bold text-red-300 mb-4">Произошла ошибка</h2>
            <p className="text-red-200 mb-4">{error}</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button 
                onClick={() => {
                  setIsLoading(true);
                  fetchCurrencies().then(() => fetchUserWallets()).finally(() => setIsLoading(false));
                }}
                className="bg-red-700 hover:bg-red-600 text-white py-2 px-6 rounded-lg transition"
              >
                Попробовать снова
              </button>
              <button 
                onClick={() => router.push('/wallet')}
                className="bg-blue-700 hover:bg-blue-600 text-white py-2 px-6 rounded-lg transition"
              >
                Вернуться в кошелек
              </button>
            </div>
          </div>
        );
        
      case 'select_currency':
        return (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold mb-6 text-center text-gray-900 dark:text-white">Выберите валюту для пополнения</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Криптовалюта:</label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {availableCurrencies
                  .filter((c, index, self) => 
                    index === self.findIndex(t => t.symbol === c.symbol)
                  )
                  .map(currency => (
                    <button
                      key={`${currency.symbol}`}
                      onClick={() => handleCurrencySelection(currency.symbol)}
                      className={`p-3 rounded-lg flex flex-col items-center justify-center transition ${
                        selectedCurrency === currency.symbol 
                          ? 'bg-purple-700 border-2 border-purple-500' 
                          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-650'
                      }`}
                    >
                      {/* Упрощенный рендер иконок для чистоты кода */}
                      <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full mb-2 flex items-center justify-center font-bold text-gray-800 dark:text-white">
                        {currency.symbol.slice(0, 2)}
                      </div>
                      <span className="text-sm text-gray-800 dark:text-white">{currency.symbol}</span>
                    </button>
                  ))
                }
              </div>
            </div>
            
            {selectedCurrency && networkOptions.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Выберите сеть:</label>
                <div className="grid grid-cols-1 gap-2">
                  {networkOptions.map(network => (
                    <button
                      key={network}
                      onClick={() => handleNetworkSelection(network)}
                      className={`p-3 rounded-lg text-center transition ${
                        selectedNetwork === network 
                          ? 'bg-purple-700 border-2 border-purple-500' 
                          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-650'
                      }`}
                    >
                      <span className="text-gray-800 dark:text-white">{network}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <button
              onClick={(e) => handleRequestDeposit(e)}
              disabled={!selectedCurrency || !selectedNetwork}
              data-testid="request-deposit-button"
              className={`w-full py-3 px-4 rounded-lg transition flex items-center justify-center 
                ${(!selectedCurrency || !selectedNetwork) 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700 text-white'}`}
            >
              Получить адрес для пополнения
            </button>
          </div>
        );
        
      case 'completed':
        return (
          <div className="text-center p-8 bg-green-900 bg-opacity-20 rounded-lg">
            <h2 className="text-2xl font-bold text-green-300 mb-4">Пополнение успешно!</h2>
            <p className="text-green-200 mb-6">Ваша заявка на пополнение одобрена.</p>
            <button 
              onClick={handleOk} 
              className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-lg transition"
            >
              ОК
            </button>
          </div>
        );
        
      case 'waiting':
        if (!depositInfo) return null;
        
        return (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center mb-6">
              <div className="w-12 h-12 bg-gray-300 dark:bg-gray-600 rounded-full mr-3 flex items-center justify-center font-bold text-gray-800 dark:text-white">
                 {selectedCurrency?.slice(0, 2)}
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">{selectedCurrency}</h2>
                <p className="text-gray-600 dark:text-gray-400">{selectedCurrency} ({selectedNetwork})</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">Адрес кошелька для пополнения:</label>
              <div className="mt-1 relative">
                <input
                  type="text"
                  readOnly
                  value={depositInfo.address}
                  className="block w-full bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-gray-900 dark:text-white p-2 pr-10"
                />
                <button 
                  onClick={() => copyToClipboard(depositInfo.address, 'address')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white"
                >
                  {copiedAddress ? <span className="text-green-500">✓</span> : <span>📋</span>}
                </button>
              </div>
            </div>

            {depositInfo.requires_memo && depositInfo.memo && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400">MEMO (Destination Tag):</label>
                <div className="mt-1 relative">
                  <input
                    type="text"
                    readOnly
                    value={depositInfo.memo}
                    className="block w-full bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-gray-900 dark:text-white p-2 pr-10"
                  />
                  <button 
                    onClick={() => copyToClipboard(depositInfo.memo || '', 'memo')}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white"
                  >
                     {copiedMemo ? <span className="text-green-500">✓</span> : <span>📋</span>}
                  </button>
                </div>
                <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-1">⚠️ Обязательно укажите MEMO при переводе</p>
              </div>
            )}
            
            {depositInfo.qr_code && (
              <div className="mb-6 flex flex-col items-center">
                <img
                  src={depositInfo.qr_code}
                  alt="QR-код"
                  className="w-40 h-40 bg-white p-2 rounded-lg shadow-md"
                  style={{ objectFit: 'contain', background: '#fff' }}
                />
              </div>
            )}
            
            {depositInfo.gas_info && (
              <div className="bg-amber-50 dark:bg-amber-900 bg-opacity-20 border-l-4 border-amber-500 p-4 rounded-md mb-6">
                <h4 className="font-bold text-amber-800 dark:text-amber-300 mb-2">Информация о газе</h4>
                <div className="text-amber-700 dark:text-amber-200 text-sm">
                  <p><strong>Сеть:</strong> {depositInfo.network}</p>
                  <p><strong>Примерная стоимость газа:</strong> {depositInfo.gas_info.estimated_gas_cost} {depositInfo.gas_info.currency_symbol}</p>
                </div>
              </div>
            )}

            <div className="mt-4 text-center text-blue-400 animate-pulse flex items-center justify-center">
              Ожидаем поступления средств...
            </div>
            
            <div className="mt-6 text-center">
              <button 
                onClick={handleCancel}
                className="text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition"
              >
                Отменить и выбрать другую валюту
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
      
      <GasWarningModal
        isOpen={showGasWarning}
        onClose={handleGasWarningClose}
        onConfirm={handleGasWarningConfirm}
        gasInfo={pendingDepositData?.gas_info || null}
        currencySymbol={pendingDepositData?.currency_symbol || selectedCurrency || ''}
        network={pendingDepositData?.network || selectedNetwork || ''}
      />
    </div>
  );
};

export default DepositPage;