'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { toast } from 'react-hot-toast';

console.log('--- Файл DepositPage.tsx ЗАГРУЖЕН (v2) ---');

// --- Interfaces ---
interface Wallet {
  id: string;
  network?: string;
  currency: {
    symbol: string;
    name: string;
    icon?: string;
  };
}
interface DepositInfo {
  address: string;
  memo?: string;
  requires_memo?: boolean;
}

interface SavedDepositInfo {
  address: string;
  memo: string;
  walletId: string;
  crypto: string;
}

interface Currency {
    id: string;
    name: string;
    symbol: string;
    icon: string;
    networks: string[];
}

type DepositStatus = 'loading' | 'select_currency' | 'waiting' | 'completed' | 'error';

// --- Custom Hook for URL Parameters ---
const useDepositParams = () => {
  const searchParams = useSearchParams();
  const walletId = searchParams.get('wallet_id');
  const crypto = searchParams.get('crypto');
  return { walletId, crypto };
};

const DEPOSIT_INFO_KEY = 'activeDepositDepositPage';

// --- Component ---
export const DepositPage: React.FC = () => {
  console.log('--- Компонент DepositPage НАЧАЛ РЕНДЕР (v3) ---');
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();
  
  console.log('DepositPage статусы: authLoading=', authLoading, 'isAuthenticated=', isAuthenticated);
  console.log('DepositPage user=', user);

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

  const { walletId, crypto } = useDepositParams();

  const handleBypass = useCallback(() => {
    console.log('DepositPage: принудительное продолжение');
    const hasToken = document.cookie.includes('access_token=') || document.cookie.includes('refresh_token=');
    if (hasToken) {
      useAuthStore.setState({ isLoading: false, isAuthenticated: true });
      setIsLoading(true);
      fetchCurrencies().finally(() => setIsLoading(false));
    } else {
      router.push('/login?redirect=/funds/deposit');
    }
  }, [router]);

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

  const fetchCurrencies = useCallback(async () => {
    console.log('DepositPage: fetchCurrencies начало выполнения');
    try {
      const resp = await api.get('/crypto/cryptocurrencies/');
      const cryptoData = Array.isArray(resp) ? resp : (resp as any).data;
      console.log('DepositPage: получены данные о криптовалютах:', cryptoData);
      
      if (!Array.isArray(cryptoData)) {
        console.error('DepositPage: данные о криптовалютах не являются массивом:', cryptoData);
        setError('Получены некорректные данные о криптовалютах');
        setStatus('error');
        return;
      }
      
      const cryptoMap = new Map<string, Currency>();

      cryptoData
        .filter((c: any) => c.currency_type === 'crypto' && c.is_active)
        .forEach((c: any) => {
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
      console.log('DepositPage: Агрегированные валюты:', aggregatedCurrencies);
      setAvailableCurrencies(aggregatedCurrencies);
      
      const walletIdParam = searchParams.get('wallet_id');
      const cryptoParam = searchParams.get('crypto');
      
      console.log('DepositPage: параметры URL:', { walletIdParam, cryptoParam });
      
      if (cryptoParam) {
        const matchedCrypto = aggregatedCurrencies.find((c: Currency) => 
          c.symbol.toLowerCase() === cryptoParam.toLowerCase()
        );
        
        if (matchedCrypto) {
          console.log('DepositPage: найдена криптовалюта из URL:', matchedCrypto);
          setSelectedCurrency(matchedCrypto.symbol);
          // Сети из кошельков пользователя
          const walletNetworks = userWallets
            .filter(w => w.currency.symbol === matchedCrypto.symbol)
            .map(w => w.network)
            .filter((n): n is string => !!n);
          const netsArr = Array.from(new Set([...(matchedCrypto.networks || []), ...walletNetworks]));
          setNetworkOptions(netsArr);
          // Если доступна только одна сеть — выбираем её автоматически
          if (netsArr.length === 1) {
            setSelectedNetwork(netsArr[0]);
          }
          setStatus('select_currency');
          return;
        } else {
          console.warn('DepositPage: криптовалюта из URL не найдена:', cryptoParam);
        }
      }
      
      setStatus('select_currency');
    } catch (err: any) {
      console.error('DepositPage: ошибка при получении списка валют:', err);
      setError(err?.message || 'Не удалось загрузить список доступных валют');
      setStatus('error');
      
      if (err?.message?.includes('Failed to fetch') || err?.message?.includes('Network Error')) {
        setError('Нет подключения к серверу. Проверьте ваше интернет-соединение и повторите попытку.');
      }
    }
  }, [searchParams]);

  // --- Fetch user wallets ---
  const fetchUserWallets = useCallback(async () => {
    try {
      const resp = await api.get('/crypto/wallets/');
      const walletsData = Array.isArray(resp) ? resp : (resp as any).data;
      setUserWallets(walletsData);
    } catch (err) {
      console.error('DepositPage: не удалось загрузить кошельки пользователя', err);
    }
  }, []);

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
    console.log('DepositPage: доступные сети для валюты:', netsArr);
    setNetworkOptions(netsArr);
      
      if (netsArr.length === 1) {
        console.log('DepositPage: автоматический выбор единственной сети:', netsArr[0]);
        setSelectedNetwork(netsArr[0]);
        
        // Если только одна сеть, можно автоматически запросить адрес после небольшой задержки
        // setTimeout(() => {
        //   if (currency.symbol === selectedCurrency) {
        //     handleRequestDeposit(new MouseEvent('click') as any);
        //   }
        // }, 500);
      }
    }, [availableCurrencies, userWallets]);

  const handleNetworkSelection = useCallback((network: string) => {
    console.log('DepositPage: выбрана сеть:', network);
    setSelectedNetwork(network);
  }, []);

  const handleRequestDeposit = useCallback(async (e: React.MouseEvent) => {
    e.preventDefault();
    console.log('DepositPage: запрос адреса для пополнения:', selectedCurrency, selectedNetwork);
    
    // Определяем актуальный список сетей для выбранной валюты
const walletNetworks = userWallets
      .filter(w => w.currency.symbol === selectedCurrency)
      .map(w => w.network)
      .filter((n): n is string => !!n);
const currencyObj = availableCurrencies.find(c => c.symbol === selectedCurrency);
const referenceNetworks = currencyObj ? currencyObj.networks || [] : [];
const allNetworks = Array.from(new Set([...walletNetworks, ...referenceNetworks]));

const networkToUse = selectedNetwork || (allNetworks.length === 1 ? allNetworks[0] : null);
    if (!selectedCurrency || !networkToUse) {
      setError('Пожалуйста, выберите криптовалюту и сеть.');
      toast.error('Выберите криптовалюту и сеть', {
        duration: 5000,
        position: 'top-center',
      });
      return;
    }
    
    // Начинаем загрузку
    setStatus('loading');
    setError(null);
    
    try {
      const payload = {
        currency_symbol: selectedCurrency,
        network: networkToUse,
      };
      
      console.log('DepositPage: отправка запроса на адрес', payload);
      toast.loading('Получение адреса для пополнения...', {
        duration: 5000,
        position: 'top-center',
      });
      
      // Прямой вызов API с именно тем URL, который нужен
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const url = `${apiBaseUrl}/crypto/deposit/info/`;
      
      console.log(`DepositPage: прямой запрос на URL = ${url}`);
      
      // Получение токена для авторизации
      const cookies = document.cookie.split('; ');
      const accessToken = cookies.find(row => row.startsWith('access_token='));
      const token = accessToken ? accessToken.split('=')[1] : '';
      
      console.log('DepositPage: доступен ли токен в cookies:', !!accessToken);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(payload),
        credentials: 'include',
      });
      
      toast.dismiss();
      
      console.log('DepositPage: получен ответ от сервера:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('DepositPage: ошибка от сервера:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          errorData = { error: errorText || `Ошибка ${response.status}: ${response.statusText}` };
        }
        
        throw new Error(errorData.error || `Ошибка ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('DepositPage: успешно получена информация для депозита:', data);
      
      if (!data || !data.address) {
        throw new Error('Сервер вернул некорректные данные без адреса');
      }
      
      setDepositInfo({
        address: data.address,
        memo: data.memo,
        requires_memo: data.requires_memo,
      });
      
      // Важно: устанавливаем статус waiting только после успешного получения всех данных
      setStatus('waiting');
      
      toast.success('Адрес для пополнения получен', {
        duration: 5000,
        position: 'top-center',
      });
    } catch (err: any) {
      toast.dismiss();
      console.error('DepositPage: ошибка при получении информации для депозита:', err);
      
      // Более подробная обработка ошибок
      let errorMessage = 'Не удалось получить данные для пополнения.';
      
      if (err?.message?.includes('Failed to fetch') || err?.message?.includes('Network Error')) {
        errorMessage = 'Нет подключения к серверу. Проверьте ваше интернет-соединение и повторите попытку.';
      } else if (err?.message?.includes('400')) {
        errorMessage = 'Неверные параметры запроса. Пожалуйста, выберите другую валюту или сеть.';
      } else if (err?.message?.includes('401') || err?.message?.includes('403')) {
        errorMessage = 'Ошибка авторизации. Пожалуйста, войдите в систему снова.';
        toast.error('Требуется повторная авторизация', {
          duration: 5000,
          position: 'top-center',
        });
        router.push('/login?redirect=/funds/deposit');
        return;
      } else if (err?.message?.includes('500')) {
        errorMessage = 'Ошибка сервера. Пожалуйста, повторите попытку позже.';
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      toast.error(errorMessage, {
        duration: 5000,
        position: 'top-center',
      });
      setError(errorMessage);
      setStatus('error');
    }
  }, [selectedCurrency, selectedNetwork, router]);

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

  // Первичная загрузка и проверка авторизации
  useEffect(() => {
    // Если компонент монтируется, проверить авторизацию
    const init = async () => {
      try {
        if (authLoading) {
          console.log('DepositPage: Авторизация всё ещё в процессе...');
          await useAuthStore.getState().checkAuthStatus();
          // После завершения checkAuthStatus() берём АКТУАЛЬНОЕ значение из стора
          const { isAuthenticated: currentAuth } = useAuthStore.getState();
          if (!currentAuth) {
            console.log('DepositPage: Пользователь не авторизован, редирект на логин');
            router.push('/login?redirect=/funds/deposit');
            return;
          }
        }
        
        // Когда авторизация завершена и пользователь авторизован
        if (!authLoading && isAuthenticated) {
          console.log('DepositPage: Пользователь авторизован, загружаем данные');
          setIsLoading(true);
          await Promise.all([fetchCurrencies(), fetchUserWallets()]);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('DepositPage: Ошибка при инициализации:', error);
      }
    };
    
    init();
    
    // Запускаем таймер для обхода авторизации
    const bypassTimer = setTimeout(() => {
      if (authLoading) {
        setShowBypass(true);
      }
    }, 5000);
    
    return () => {
      clearTimeout(bypassTimer);
    };
  }, [authLoading, isAuthenticated, router, fetchCurrencies]);

  useEffect(() => {
    if (!isLoading && availableCurrencies.length > 0) {
      const walletIdParam = searchParams.get('wallet_id');
      const cryptoParam = searchParams.get('crypto');
      
      console.log('DepositPage: параметры в URL:', { walletIdParam, cryptoParam });
      
      if (cryptoParam) {
        console.log('DepositPage: параметр crypto в URL:', cryptoParam);
        
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
          console.log('DepositPage: найдена криптовалюта из URL:', matchedCrypto);
          setSelectedCurrency(matchedCrypto.symbol);
          
          if (matchedCrypto.networks && matchedCrypto.networks.length > 0) {
            console.log('DepositPage: доступные сети для валюты:', matchedCrypto.networks);
            setNetworkOptions(matchedCrypto.networks);
            
            // Если для валюты только одна сеть - выбираем её автоматически
            if (matchedCrypto.networks.length === 1) {
              console.log('DepositPage: автоматический выбор сети (одна опция):', matchedCrypto.networks[0]);
              setSelectedNetwork(matchedCrypto.networks[0]);
              
              // Автоматически запрашиваем адрес после небольшой задержки если есть единственная сеть
              const timer = setTimeout(() => {
                const button = document.querySelector('[data-testid="request-deposit-button"]');
                if (button && button instanceof HTMLButtonElement) {
                  console.log('DepositPage: автоматический клик по кнопке запроса адреса');
                  button.click();
                } else {
                  console.log('DepositPage: кнопка запроса адреса не найдена');
                }
              }, 1500);
              
              return () => clearTimeout(timer);
            }
          }
        } else {
          console.warn('DepositPage: криптовалюта из URL не найдена:', cryptoParam);
        }
      }
    }
  }, [isLoading, availableCurrencies, searchParams]);

  // WebSocket Connection
  useEffect(() => {
    if (!depositInfo || (!depositInfo.memo && !depositInfo.address)) {
      return; // Нет данных для WebSocket
    }
    
    if (wsRef.current) {
      // Соединение уже установлено
      console.log('DepositPage: WebSocket соединение уже существует');
      return;
    }

    const connect = () => {
      let wsUrl = '';
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NEXT_PUBLIC_WS_BASE_URL 
        ? process.env.NEXT_PUBLIC_WS_BASE_URL 
        : `${protocol}//${window.location.hostname}:8000`;
      if (depositInfo.memo) {
        wsUrl = `${host}/ws/deposit_status/${depositInfo.memo}/`;
        console.log(`DepositPage: подключение к WebSocket по memo: ${wsUrl}`);
      } else if (depositInfo.address) {
        wsUrl = `${host}/ws/deposit_status/address/${depositInfo.address}/`;
        console.log(`DepositPage: подключение к WebSocket по адресу: ${wsUrl}`);
      } else {
        return;
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log(`WebSocket подключен: ${wsUrl}`);
          toast.success('Подключение к системе мониторинга установлено', {
            duration: 5000,
            position: 'top-center',
          });
        };

        ws.onmessage = (event) => {
          try {
            console.log('Получено WebSocket сообщение:', event.data);
            const data = JSON.parse(event.data);
            // Для memo
            if (depositInfo.memo && data.memo === depositInfo.memo && data.status) {
              if (data.status === 'used') {
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
            }
            // Для адреса
            if (depositInfo.address && data.address === depositInfo.address && data.status) {
              if (data.status === 'used') {
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
            }
          } catch (error) {
            console.error('Ошибка при обработке сообщения WebSocket:', error);
          }
        };

        ws.onerror = (event) => {
          console.error('Ошибка WebSocket:', event);
        };

        ws.onclose = (event) => {
          console.log('WebSocket отключен.', event.reason || 'причина не указана');
          wsRef.current = null;
          if (status === 'waiting') {
            // Попытка переподключения через 5 секунд
            console.log('Переподключение WebSocket через 5 сек...');
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
        console.log('Закрытие WebSocket соединения при размонтировании компонента');
        const ws = wsRef.current;
        wsRef.current = null;
        ws.onclose = null;
        ws.close();
      }
    };
  }, [depositInfo, status]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated]);

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
    console.log('DepositPage: не авторизован и нет активного пополнения, редирект');
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
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold text-red-300 mb-4">Произошла ошибка</h2>
            <p className="text-red-200 mb-4">{error}</p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button 
                onClick={() => {
                  setIsLoading(true);
                  fetchCurrencies().finally(() => setIsLoading(false));
                }}
                className="bg-red-700 hover:bg-red-600 text-white py-2 px-6 rounded-lg transition"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 inline mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
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
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md">
            <h2 className="text-xl font-bold mb-6 text-center">Выберите валюту для пополнения</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-400 mb-2">Криптовалюта:</label>
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
            
            {selectedCurrency && networkOptions.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">Выберите сеть:</label>
                <div className="grid grid-cols-1 gap-2">
                  {networkOptions.map(network => (
                    <button
                      key={network}
                      onClick={() => handleNetworkSelection(network)}
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
                {networkOptions.length > 1 && (
                  <p className="text-xs text-yellow-500 mt-2">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Важно: выберите ту же сеть, которую будете использовать для перевода
                  </p>
                )}
              </div>
            )}
            
            <button
              onClick={handleRequestDeposit}
              disabled={!selectedCurrency || !selectedNetwork}
              data-testid="request-deposit-button"
              className={`w-full py-3 px-4 rounded-lg transition flex items-center justify-center 
                ${(!selectedCurrency || !selectedNetwork) 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700 text-white'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Получить адрес для пополнения
            </button>
          </div>
        );
        
      case 'completed':
        return (
          <div className="text-center p-8 bg-green-900 bg-opacity-20 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
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
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md">
            <div className="flex items-center justify-center mb-6">
              {selectedCurrency && (
                <Image
                  src={`${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${availableCurrencies.find(c => c.symbol === selectedCurrency)?.icon || ''}`}
                  alt={selectedCurrency}
                  width={48}
                  height={48}
                  className="rounded-full mr-3"
                  unoptimized
                />
              )}
              <div>
                <h2 className="text-xl font-bold">{selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.name}</h2>
                <p className="text-gray-400">{selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.symbol} ({selectedNetwork})</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="deposit-address" className="block text-sm font-medium text-gray-400">Адрес кошелька для пополнения:</label>
              <div className="mt-1 relative">
                <input
                  id="deposit-address"
                  type="text"
                  readOnly
                  value={depositInfo.address}
                  className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-2 pr-10"
                />
                <button 
                  onClick={() => copyToClipboard(depositInfo.address, 'address')}
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
            {depositInfo.requires_memo && (
              <>
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
                      onClick={() => copyToClipboard(depositInfo.memo || '', 'memo')}
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
                    <li>Отправляйте только {selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.symbol} в сети {selectedNetwork}.</li>
                    <li>Обязательно укажите MEMO в комментарии к транзакции.</li>
                    <li>Средства, отправленные без MEMO, могут быть утеряны.</li>
                    <li>Минимальная сумма пополнения: 10 {selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.symbol}.</li>
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
              </>
            )}
            
            <div className="mt-4 text-center text-blue-400 animate-pulse flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Ожидаем поступления средств... ({depositInfo.memo})
            </div>
            
            <div className="mt-6 text-center">
              <button 
                onClick={handleCancel}
                className="text-purple-400 hover:text-purple-300 transition"
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
    </div>
  );
};

export default DepositPage;
