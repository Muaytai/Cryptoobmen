'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import api from '@/lib/api/fetch';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import GasWarningModal from '@/components/modalWindows/GasWarningModal';

console.log('--- Файл DepositPage.tsx ЗАГРУЖЕН (v2) ---');

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
  memo?: string;
  requires_memo?: boolean;
  qr_code?: string; // добавлено поле для QR-кода
  currency_symbol?: string;
  network?: string;
  gas_info?: {
    estimated_gas_cost: string;
    currency_symbol: string;
    calculation_method: string;
  };
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
  const [showGasWarning, setShowGasWarning] = useState<boolean>(false);
  const [pendingDepositData, setPendingDepositData] = useState<any>(null);

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
      
      // Отладочные логи для icon
      aggregatedCurrencies.forEach(currency => {
        console.log(`DepositPage: Валюта ${currency.symbol} - icon: "${currency.icon}"`);
        if (!currency.icon || currency.icon.trim() === '') {
          console.warn(`DepositPage: У валюты ${currency.symbol} отсутствует или пуста иконка`);
        }
      });
      
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
    console.log('DepositPage: сети из кошельков пользователя:', walletNetworks);
    console.log('DepositPage: справочные сети:', referenceNetworks);
    setNetworkOptions(netsArr);
      
    if (netsArr.length === 1) {
      console.log('DepositPage: автоматический выбор единственной сети:', netsArr[0]);
      setSelectedNetwork(netsArr[0]);
    } else if (netsArr.length > 1) {
      console.log('DepositPage: доступно несколько сетей, пользователь должен выбрать');
      // Если есть несколько сетей, попробуем автоматически выбрать ту, которая соответствует кошельку пользователя
      if (walletNetworks.length === 1) {
        console.log('DepositPage: автоматический выбор сети из кошелька пользователя:', walletNetworks[0]);
        setSelectedNetwork(walletNetworks[0]);
      }
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
    
    // Начинаем загрузку
    setStatus('loading');
    setError(null);
    
    try {
      // Находим валюту, которая соответствует и символу, и сети
      let currency = null;
      
      // Сначала пытаемся найти валюту по символу и сети
      if (selectedNetwork) {
        // Ищем валюту, которая поддерживает выбранную сеть
        currency = availableCurrencies.find(c => 
          c.symbol === selectedCurrency && 
          c.networks && 
          c.networks.includes(selectedNetwork)
        );
        
        // Если не нашли, попробуем найти валюту, которая соответствует сети из кошельков пользователя
        if (!currency) {
          const userWalletForNetwork = userWallets.find(w => 
            w.currency.symbol === selectedCurrency && 
            w.network === selectedNetwork
          );
          
          if (userWalletForNetwork) {
            // Ищем валюту с тем же ID, что и в кошельке пользователя
            currency = availableCurrencies.find(c => c.id === userWalletForNetwork.currency.id);
            console.log('DepositPage: найдена валюта по кошельку пользователя:', {
              walletCurrencyId: userWalletForNetwork.currency.id,
              foundCurrency: currency
            });
          }
        }
        
        // Если все еще не нашли, попробуем найти валюту, которая точно соответствует сети
        if (!currency) {
          console.log('DepositPage: пытаемся найти валюту по точному соответствию сети:', selectedNetwork);
          // Ищем валюту, которая точно соответствует выбранной сети
          const exactMatchCurrency = availableCurrencies.find(c => 
            c.symbol === selectedCurrency && 
            c.networks && 
            c.networks.some(network => 
              network.toLowerCase() === selectedNetwork.toLowerCase() ||
              network.toLowerCase().includes(selectedNetwork.toLowerCase()) ||
              selectedNetwork.toLowerCase().includes(network.toLowerCase())
            )
          );
          
          if (exactMatchCurrency) {
            currency = exactMatchCurrency;
            console.log('DepositPage: найдена валюта по точному соответствию сети:', {
              symbol: exactMatchCurrency.symbol,
              id: exactMatchCurrency.id,
              networks: exactMatchCurrency.networks,
              selectedNetwork
            });
          }
        }
      }
      
      // Если не нашли по сети, ищем только по символу (fallback)
      if (!currency) {
        currency = availableCurrencies.find(c => c.symbol === selectedCurrency);
        console.log('DepositPage: fallback - найдена валюта только по символу:', {
          symbol: currency?.symbol,
          id: currency?.id,
          networks: currency?.networks
        });
      }
      
      if (!currency) {
          throw new Error("Selected currency not found");
      }

      console.log('DepositPage: выбрана валюта для запроса:', {
        symbol: currency.symbol,
        id: currency.id,
        networks: currency.networks,
        selectedNetwork
      });
      
      console.log('DepositPage: доступные валюты для отладки:', availableCurrencies.map(c => ({
        id: c.id,
        symbol: c.symbol,
        networks: c.networks
      })));
      
      console.log('DepositPage: кошельки пользователя для отладки:', userWallets.map(w => ({
        id: w.id,
        currencyId: w.currency.id,
        symbol: w.currency.symbol,
        network: w.network,
        address: w.deposit_address
      })));

      // Определяем параметры для запроса
      let requestParams: any = {};
      
      if (selectedNetwork || networkToUse) {
        // Если указана сеть, передаем symbol и network
        requestParams = {
          currency_id: selectedCurrency,  // Передаем symbol валюты
          network: selectedNetwork || networkToUse
        };
      } else {
        // Если сеть не указана, передаем currency_id
        requestParams = {
          currency_id: currency.id
        };
      }

      const response = await api.post('/transactions/deposits/address/', requestParams);
      
      const data = response;
      console.log('DepositPage: успешно получена информация для депозита:', data);
      
      if (!data || !data.address) {
        throw new Error('Сервер вернул некорректные данные без адреса');
      }
      
      // Проверяем, есть ли информация о газе (прокси кошелек)
      if (data.gas_info) {
        // Сохраняем данные для модального окна
        setPendingDepositData({
          address: data.address,
          memo: data.memo,
          requires_memo: data.requires_memo,
          qr_code: data.qr_code,
          currency_symbol: data.currency_symbol,
          network: data.network,
          gas_info: data.gas_info,
        });
        
        // Показываем модальное окно с предупреждением
        setShowGasWarning(true);
        setStatus('select_currency'); // Возвращаемся к выбору валюты до подтверждения
      } else {
        // Обычный депозит без прокси кошелька
        setDepositInfo({
          address: data.address,
          memo: data.memo,
          requires_memo: data.requires_memo,
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
      // Используем базовый адрес из env или по умолчанию
      const wsBase = process.env.NEXT_PUBLIC_WS_URL || `ws://${window.location.hostname}:8000`;
      let wsUrl = '';
      if (depositInfo.memo) {
        wsUrl = `${wsBase}/ws/deposit_status/${depositInfo.memo}/`;
      } else if (depositInfo.address) {
        wsUrl = `${wsBase}/ws/deposit_status/address/${depositInfo.address}/`;
      } else {
        return;
      }
      console.log('Финальный wsUrl:', wsUrl);
      
      console.log(`DepositPage: Попытка подключения к WebSocket: ${wsUrl}`);

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
                      {currency.icon && currency.icon.trim() !== '' ? (() => {
                        const iconUrl = currency.icon.startsWith('http') 
                          ? currency.icon 
                          : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${currency.icon}`;
                        
                        // Проверяем валидность URL
                        try {
                          new URL(iconUrl);
                          return (
                            <>
                              <Image
                                src={iconUrl}
                                alt={currency.symbol}
                                width={32}
                                height={32}
                                className="rounded-full mb-2"
                                unoptimized
                                onError={(e) => {
                                  console.error('DepositPage: Ошибка загрузки иконки валюты:', iconUrl);
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  const fallback = target.nextElementSibling as HTMLElement;
                                  if (fallback) fallback.style.display = 'flex';
                                }}
                              />
                              <div 
                                className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full mb-2 flex items-center justify-center font-bold text-gray-800 dark:text-white"
                                style={{ display: 'none' }}
                              >
                                {currency.symbol.slice(0, 2)}
                              </div>
                            </>
                          );
                        } catch (error) {
                          console.error('DepositPage: Некорректный URL иконки валюты:', iconUrl, error);
                          return (
                            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full mb-2 flex items-center justify-center font-bold text-gray-800 dark:text-white">
                              {currency.symbol.slice(0, 2)}
                            </div>
                          );
                        }
                      })() : (
                        <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full mb-2 flex items-center justify-center font-bold text-gray-800 dark:text-white">
                          {currency.symbol.slice(0, 2)}
                        </div>
                      )}
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
                {networkOptions.length > 1 && (
                  <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-2">
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
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg w-full max-w-md border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center mb-6">
              {selectedCurrency && (() => {
                const currency = availableCurrencies.find(c => c.symbol === selectedCurrency);
                const iconPath = currency?.icon;
                const baseUrl = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '');
                
                // Отладочные логи
                const proposedUrl = iconPath && iconPath.startsWith('http') ? iconPath : `${baseUrl}${iconPath || ''}`;
                console.log('DepositPage: Данные для изображения:', {
                  selectedCurrency,
                  currency,
                  iconPath,
                  baseUrl,
                  isFullUrl: iconPath?.startsWith('http') || false,
                  finalUrl: proposedUrl
                });
                
                // Проверяем корректность URL
                if (!iconPath || iconPath.trim() === '') {
                  console.warn('DepositPage: Пустой путь к иконке для валюты:', selectedCurrency);
                  return (
                    <div className="w-12 h-12 bg-gray-300 dark:bg-gray-600 rounded-full mr-3 flex items-center justify-center">
                      <span className="text-gray-800 dark:text-white font-bold text-sm">{selectedCurrency.slice(0, 2)}</span>
                    </div>
                  );
                }
                
                // Определяем финальный URL: если iconPath уже содержит http, используем его как есть
                const fullImageUrl = iconPath && iconPath.startsWith('http') ? iconPath : `${baseUrl}${iconPath || ''}`;
                
                // Проверяем валидность URL
                try {
                  new URL(fullImageUrl);
                } catch (error) {
                  console.error('DepositPage: Некорректный URL для изображения:', fullImageUrl, error);
                  return (
                    <div className="w-12 h-12 bg-gray-300 dark:bg-gray-600 rounded-full mr-3 flex items-center justify-center">
                      <span className="text-gray-800 dark:text-white font-bold text-sm">{selectedCurrency.slice(0, 2)}</span>
                    </div>
                  );
                }
                
                return (
                  <>
                    <Image
                      src={fullImageUrl}
                      alt={selectedCurrency}
                      width={48}
                      height={48}
                      className="rounded-full mr-3"
                      unoptimized
                      onError={(e) => {
                        console.error('DepositPage: Ошибка загрузки изображения:', fullImageUrl);
                        // Заменяем на fallback
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const fallback = target.nextElementSibling as HTMLElement;
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div 
                      className="w-12 h-12 bg-gray-300 dark:bg-gray-600 rounded-full mr-3 flex items-center justify-center"
                      style={{ display: 'none' }}
                    >
                      <span className="text-gray-800 dark:text-white font-bold text-sm">{selectedCurrency.slice(0, 2)}</span>
                    </div>
                  </>
                );
              })()}
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">{selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.name}</h2>
                <p className="text-gray-600 dark:text-gray-400">{selectedCurrency && availableCurrencies.find(c => c.symbol === selectedCurrency)?.symbol} ({selectedNetwork})</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="deposit-address" className="block text-sm font-medium text-gray-600 dark:text-gray-400">Адрес кошелька для пополнения:</label>
              <div className="mt-1 relative">
                <input
                  id="deposit-address"
                  type="text"
                  readOnly
                  value={depositInfo.address}
                  className="block w-full bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-gray-900 dark:text-white p-2 pr-10"
                />
                <button 
                  onClick={() => copyToClipboard(depositInfo.address, 'address')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white"
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
            {/* QR-код для депозита */}
            {depositInfo.qr_code && (
              <div className="mb-6 flex flex-col items-center">
                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">QR-код для пополнения:</label>
                <img
                  src={depositInfo.qr_code}
                  alt="QR-код для пополнения"
                  className="w-40 h-40 bg-white p-2 rounded-lg shadow-md"
                  style={{ objectFit: 'contain', background: '#fff' }}
                />
              </div>
            )}
            {depositInfo.requires_memo && (
              <>
                <div className="mb-6">
                  <label htmlFor="deposit-memo" className="block text-sm font-medium text-gray-600 dark:text-gray-400">MEMO (обязательно для зачисления):</label>
                  <div className="mt-1 relative">
                    <input
                      id="deposit-memo"
                      type="text"
                      readOnly
                      value={depositInfo.memo}
                      className="block w-full bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-gray-900 dark:text-white p-2 pr-10"
                    />
                    <button 
                      onClick={() => copyToClipboard(depositInfo.memo || '', 'memo')}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white"
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
                <div className="bg-yellow-50 dark:bg-yellow-900 border-l-4 border-yellow-500 text-yellow-800 dark:text-yellow-200 p-4 rounded-md mb-6">
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
                <div className="bg-blue-50 dark:bg-blue-900 border-l-4 border-blue-500 text-blue-800 dark:text-blue-200 p-4 rounded-md mb-6">
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
            
            {/* Информация о газе для прокси кошелька */}
            {depositInfo.gas_info && (
              <div className="bg-amber-50 dark:bg-amber-900 bg-opacity-20 dark:bg-opacity-20 border-l-4 border-amber-500 p-4 rounded-md mb-6">
                <h4 className="font-bold text-amber-800 dark:text-amber-300 mb-2 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Информация о газе
                </h4>
                <div className="text-amber-700 dark:text-amber-200 text-sm">
                  <p><strong>Сеть:</strong> {depositInfo.network}</p>
                  <p><strong>Примерная стоимость газа:</strong> {depositInfo.gas_info.estimated_gas_cost} {depositInfo.gas_info.currency_symbol}</p>
                  <p className="text-xs text-amber-600 dark:text-amber-300 mt-2">
                    * Газ будет списан дважды: при переводе на прокси и с прокси на финальный адрес
                  </p>
                </div>
              </div>
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
      
      {/* Модальное окно с предупреждением о газе */}
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
