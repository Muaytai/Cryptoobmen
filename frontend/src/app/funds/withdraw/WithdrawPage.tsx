"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/lib/api/fetch";
import Image from "next/image";
import Link from "next/link";

// Типы данных
interface Wallet {
  id: number;
  currency: {
    id: number;
    name: string;
    symbol: string;
    icon: string;
    network?: string;
  };
  balance: string;
  available_balance: string;
  locked_balance: string;
  address: string;
}

interface CryptoPrice {
  crypto_id: number;
  name: string;
  symbol: string;
  prices: { usd: number };
}

interface WithdrawalData {
  wallet: number;
  amount: number;
  destination_address: string;
  crypto_id?: number;
  memo?: string;
}

// Добавляем интерфейс для статуса транзакции
interface WithdrawalStatus {
  id: number;
  transaction: {
    id: number;
    transaction_id: string;
    status: string;
    status_display: string;
  };
  destination_address: string;
}

export const WithdrawPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const {
    user,
    isAuthenticated,
    isLoading: authLoading,
  } = useAuthStore();

  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [withdrawalId, setWithdrawalId] = useState<string | null>(null);
  const [showInfoTips, setShowInfoTips] = useState<boolean>(true);

  // Данные формы
  const [selectedWalletId, setSelectedWalletId] = useState<number | null>(null);
  const [amount, setAmount] = useState<string>("");
  const [destinationAddress, setDestinationAddress] = useState<string>("");
  const [fee, setFee] = useState<string>("0");
  const [feeUsd, setFeeUsd] = useState<string>("0");
  const [netAmount, setNetAmount] = useState<string>("0");

  // В компоненте WithdrawPage добавим состояние для отслеживания статуса вывода
  const [withdrawalStatus, setWithdrawalStatus] =
    useState<WithdrawalStatus | null>(null);
  const [cancelling, setCancelling] = useState<boolean>(false);

  // Состояния для MEMO
  const [requiresMemo, setRequiresMemo] = useState<boolean>(false);
  const [memo, setMemo] = useState<string>("");

  // Состояния для расчета стоимости вывода
  const [withdrawalCost, setWithdrawalCost] = useState<{
    withdrawal_amount: string;
    gas_cost: string;
    platform_fee: string;
    total_cost: string;
    calculation_method: string;
    currency_symbol: string;
  } | null>(null);
  const [costLoading, setCostLoading] = useState<boolean>(false);
  const [maxAmountLoading, setMaxAmountLoading] = useState<boolean>(false);

  // Гарантируем, что wallets — массив (Мемоизация для устранения warning)
  const walletsArr = useMemo(() => {
    return Array.isArray(wallets) ? wallets : [];
  }, [wallets]);

  // Функция загрузки кошельков (useCallback)
  const fetchWallets = useCallback(async () => {
    try {
      const walletsResponse = await api.get<any>("/crypto/wallets/");
      console.log("API wallets response:", walletsResponse);
      // Если ответ содержит results (DRF pagination)
      const data = walletsResponse as { results?: Wallet[] } | Wallet[];
      const resultArr = Array.isArray(data)
        ? data
        : Array.isArray(data.results)
        ? data.results
        : [];
      setWallets(resultArr);
      console.log("walletsArr after set:", resultArr);
    } catch (err) {
      setWallets([]);
    }
  }, []);

  // Загрузка кошельков при маунте
  useEffect(() => {
    fetchWallets();
  }, [fetchWallets]);

  // Получение данных кошельков пользователя и цен
  useEffect(() => {
    if (authLoading) {
      console.log(
        "WithdrawPage: authLoading is true, ожидаем завершения проверки сессии..."
      );
      setLoading(true);
      return;
    }

    console.log(
      `WithdrawPage: authLoading is false. isAuthenticated: ${isAuthenticated}, user: ${!!user}`
    );

    if (!isAuthenticated || !user) {
      console.log(
        "WithdrawPage: Пользователь НЕ аутентифицирован (после authLoading: false). Перенаправление на /login."
      );
      const currentParams = searchParams.toString();
      const redirectPath = `/funds/withdraw${
        currentParams ? `?${currentParams}` : ""
      }`;
      router.push(`/login?redirect=${encodeURIComponent(redirectPath)}`);
      return;
    }

    // Если пользователь аутентифицирован, загружаем данные страницы
    const fetchData = async () => {
      console.log(
        "WithdrawPage: Пользователь аутентифицирован. Загрузка данных страницы..."
      );
      setLoading(true);
      try {
        const pricesResponse = await api.get<CryptoPrice[]>("/crypto/prices/latest/");
        setPrices(Array.isArray(pricesResponse) ? pricesResponse : []);
        
        const walletIdParam = searchParams.get("wallet_id");
        // Используем fetchWallets, который уже вызван в другом эффекте, но здесь нам нужны актуальные данные
        // Поэтому проверяем состояние wallets, если оно уже загружено
        
        // Логика выбора кошелька перенесена в отдельный useEffect, зависящий от walletsArr
        
        setError(null);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Не удалось загрузить данные";
        console.error(
          "WithdrawPage: Ошибка при получении данных страницы:",
          err
        );
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [authLoading, isAuthenticated, user, router, searchParams]);

  // useEffect для авто-выбора кошелька после загрузки
  useEffect(() => {
    if (walletsArr.length > 0 && !selectedWalletId) {
      const walletIdParam = searchParams.get("wallet_id");
      if (
        walletIdParam &&
        walletsArr.some((w) => w.id === Number(walletIdParam))
      ) {
        setSelectedWalletId(Number(walletIdParam));
      } else {
        setSelectedWalletId(walletsArr[0].id);
      }
    }
  }, [walletsArr, selectedWalletId, searchParams]);

  const selectedWallet = useMemo(() => 
    walletsArr.find((w) => w.id === Number(selectedWalletId)),
  [walletsArr, selectedWalletId]);

  // Безопасный поиск цены для выбранного кошелька
  const cryptoPrice = useMemo(() => {
    if (selectedWallet && selectedWallet.currency && Array.isArray(prices)) {
      if (selectedWallet.currency.symbol === 'USDT') {
        return prices.find(p => p.symbol === 'USDT');
      } else {
        return prices.find(
          (p) => p.crypto_id === selectedWallet.currency.id
        );
      }
    }
    return null;
  }, [selectedWallet, prices]);

  // Расчет стоимости вывода с учетом газа и комиссий (useCallback)
  const calculateWithdrawalCost = useCallback(async (walletId: number, amountStr: string, destAddr: string, memoStr?: string) => {
    try {
      setCostLoading(true);
      console.log('=== РАСЧЕТ СТОИМОСТИ ВЫВОДА ===');
      console.log('Параметры запроса:', {
        walletId,
        amount: amountStr,
        destAddr,
        memo: memoStr
      });

      // Получаем crypto_id из выбранного кошелька
      // Используем walletsArr из замыкания или прокидываем
      const wallet = walletsArr.find((w) => w.id === walletId);
      if (!wallet) {
        throw new Error('Кошелек не найден');
      }

      const requestData = {
        crypto_id: wallet.currency.id,
        destination_address: destAddr,
        amount: parseFloat(amountStr)
      };

      console.log('Данные для отправки:', requestData);

      const response = await api.post<any>('/transactions/withdrawals/calculate-cost/', requestData);
      
      if (response) {
        setWithdrawalCost(response);
      }

      return response;
    } catch (error: any) {
      console.error('Ошибка при расчете стоимости вывода:', error);
      setWithdrawalCost(null);
      throw error;
    } finally {
      setCostLoading(false);
    }
  }, [walletsArr]); // Зависимость от walletsArr

  // Обновление расчета комиссии при изменении суммы или кошелька
  useEffect(() => {
    if (selectedWalletId && amount && !isNaN(parseFloat(amount)) && destinationAddress) {
      calculateWithdrawalCost(
        selectedWalletId,
        amount,
        destinationAddress,
        requiresMemo ? memo || undefined : undefined
      );
    } else {
      setFee("0");
      setFeeUsd("0");
      setNetAmount("0");
      setWithdrawalCost(null);
    }
  }, [selectedWalletId, amount, destinationAddress, memo, requiresMemo, calculateWithdrawalCost]); // Добавлены зависимости

  // Обновление отображения комиссий на основе данных от API
  useEffect(() => {
    if (withdrawalCost && selectedWallet) {
      // Используем данные от API
      setFee(withdrawalCost.platform_fee);
      setNetAmount(withdrawalCost.withdrawal_amount);
      
      // Для USD конвертации используем старую логику
      let priceInfo = null;
      if (selectedWallet.currency.symbol === 'USDT') {
        priceInfo = prices.find(p => p.symbol === 'USDT');
      } else {
        priceInfo = prices.find(p => p.crypto_id === selectedWallet.currency.id);
      }
      
      if (priceInfo) {
        setFeeUsd((parseFloat(withdrawalCost.platform_fee) * priceInfo.prices.usd).toFixed(2));
      }
    }
  }, [withdrawalCost, selectedWallet, prices]);

  // Обработчики изменения полей формы
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Разрешаем только числа и одну точку
    if (/^\d*\.?\d*$/.test(value) || value === "") {
      setAmount(value);
    }
  };

  // Получение максимально доступной суммы для вывода
  const getMaxAvailableAmount = (): string => {
    if (!selectedWallet) return "0";
    return selectedWallet.available_balance;
  };

  // Установка максимальной доступной суммы с учетом газа и комиссий
  const setMaxAmount = async () => {
    console.log('=== КНОПКА МАКС НАЖАТА ===');
    
    if (!selectedWalletId || !destinationAddress) {
      // Если нет выбранного кошелька или адреса, используем старую логику
      console.log('Нет кошелька или адреса, используем старую логику');
      const maxAmountVal = getMaxAvailableAmount();
      setAmount(maxAmountVal);
      return;
    }

    setMaxAmountLoading(true);
    setError(null);

    try {
      const wallet = walletsArr.find((w) => w.id === selectedWalletId);
      if (!wallet) return;

      const availableBalance = parseFloat(wallet.available_balance);
      
      // Используем бинарный поиск для нахождения максимальной суммы
      let left = 0;
      let right = availableBalance;
      let maxWithdrawable = 0;
      const precision = 0.00000001; // 8 знаков после запятой
      
      while (right - left > precision) {
        const mid = (left + right) / 2;
        const testAmount = mid.toFixed(8);
        
        try {
          const response = await calculateWithdrawalCost(
            selectedWalletId,
            testAmount,
            destinationAddress,
            requiresMemo ? memo || undefined : undefined
          );
          
          if (response && response.total_cost) {
            const totalCost = parseFloat(response.total_cost);
            const withdrawalAmount = parseFloat(response.withdrawal_amount);
            
            // Проверяем, что общая стоимость не превышает доступный баланс
            if (totalCost <= availableBalance) {
              maxWithdrawable = withdrawalAmount;
              left = mid;
            } else {
              right = mid;
            }
          } else {
            right = mid;
          }
        } catch (error) {
          // Если расчет не удался (например, сумма слишком мала), уменьшаем диапазон
          right = mid;
        }
      }
      
      if (maxWithdrawable > 0) {
        const maxAmountVal = maxWithdrawable.toFixed(8);
        setAmount(maxAmountVal);
        setError(null);
      } else {
        setAmount("0");
        setError("Недостаточно средств для покрытия комиссий и газа");
      }
    } catch (error) {
      console.error('Ошибка при расчете максимальной суммы:', error);
      // Fallback на старую логику
      const maxAmountVal = getMaxAvailableAmount();
      setAmount(maxAmountVal);
    } finally {
      setMaxAmountLoading(false);
    }
  };

  // Получение requires_memo для выбранного кошелька
  useEffect(() => {
    const fetchRequiresMemo = async () => {
      if (!selectedWallet) {
        setRequiresMemo(false);
        return;
      }

      // Для Solana не требуется MEMO, поэтому сразу устанавливаем false
      if (selectedWallet.currency.symbol === "SOL") {
        setRequiresMemo(false);
        return;
      }

      if (selectedWallet.currency.symbol === "XRP") {
        setRequiresMemo(false);
        setMemo("");
        return;
      }

      try {
        // Запрашиваем у API адрес для пополнения, чтобы узнать requires_memo
        const resp = await api.get<any>(`/crypto/withdraw-info/?currency=${selectedWallet.currency.symbol}&network=${selectedWallet.currency.network}`);
        setRequiresMemo(!!resp.requires_memo);
      } catch (error) {
        console.error("Error fetching requires_memo:", error);
        setRequiresMemo(false);
      }
    };
    fetchRequiresMemo();
  }, [selectedWallet]);

  // Очистка MEMO если он не требуется
  useEffect(() => {
    if (!requiresMemo && memo) {
      setMemo("");
    }
  }, [requiresMemo, memo]); // Добавлена зависимость memo

  // Отправка формы
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !selectedWalletId ||
      !amount ||
      isNaN(parseFloat(amount)) ||
      parseFloat(amount) <= 0
    ) {
      setError(
        "Пожалуйста, выберите кошелек и введите корректную сумму вывода"
      );
      return;
    }

    if (!destinationAddress) {
      setError("Пожалуйста, введите адрес кошелька для вывода");
      return;
    }

    if (requiresMemo && !memo) {
      setError("Для этой валюты требуется MEMO/Tag");
      return;
    }

    const wallet = walletsArr.find((w) => w.id === selectedWalletId);
    if (!wallet) {
      setError("Выбранный кошелек не найден");
      return;
    }

    const amountValue = parseFloat(amount);
    const availableBalance = parseFloat(wallet.available_balance);

    if (amountValue > availableBalance) {
      setError(
        `Недостаточно средств. Доступно: ${availableBalance} ${wallet.currency.symbol}`
      );
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const withdrawalData: WithdrawalData = {
        wallet: selectedWalletId,
        amount: amountValue,
        destination_address: destinationAddress,
      };
      if (requiresMemo) {
        withdrawalData.memo = memo;
      }

      const response = await api.post<{ data: WithdrawalStatus }>(
        "/transactions/withdrawals/",
        withdrawalData
      );

      setSuccess(true);
      if (response && response.data) {
        setWithdrawalId(response.data.transaction.transaction_id);
        setWithdrawalStatus(response.data);
      }

      // Очищаем форму
      setAmount("");
      setDestinationAddress("");
      setMemo("");
    } catch (err: any) {
      console.error("Ошибка при отправке запроса на вывод:", err);
      setError(err.message || "Не удалось создать запрос на вывод средств");
    } finally {
      setSubmitting(false);
    }
  };

  // Добавим функцию для отмены вывода средств
  const cancelWithdrawal = async (withdrawalId: number) => {
    if (!withdrawalId) return;

    try {
      setCancelling(true);
      await api.post(`/transactions/withdrawals/${withdrawalId}/cancel/`, {});
      // Обновляем статус вывода после отмены
      const updatedWithdrawal = await api.get<{ data: WithdrawalStatus }>(
        `/transactions/withdrawals/${withdrawalId}/`
      );
      // Здесь предполагаем, что updatedWithdrawal может быть обернут в data
      const statusData = (updatedWithdrawal as any).data || updatedWithdrawal;
      setWithdrawalStatus(statusData);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Не удалось отменить вывод средств");
    } finally {
      setCancelling(false);
    }
  };

  if (authLoading || loading) {
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
          <svg
            className="w-16 h-16 text-green-500 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>

          <h2 className="text-2xl font-bold mb-4">Запрос на вывод успешно создан!</h2>
          <p className="mb-6 text-sm text-gray-400">
            зайдите на почту email вашего пользователя для подтверждения транзакции вывода
          </p>
          <div className="flex flex-col space-y-3">
            <Link
              href="/wallet"
              className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700 transition"
            >
              Вернуться к кошельку
            </Link>
            <Link
              href="/transactions"
              className="text-purple-400 hover:text-purple-300 transition"
            >
              Перейти к истории транзакций
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedWallet) {
    // Если кошельки загружены, но ничего не выбрано (значит список пуст)
    if (walletsArr.length === 0 && !loading) {
       return <div className="text-center py-8 text-gray-400">У вас пока нет кошельков для вывода.</div>;
    }
    return <div className="text-center py-8 text-gray-400">Загрузка кошелька...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-center">
          Вывод криптовалюты
        </h1>

        {/* Обучающая панель */}
        {showInfoTips && (
          <div className="bg-indigo-900 bg-opacity-50 rounded-xl p-6 mb-8 border border-indigo-700">
            <div className="flex justify-between items-start mb-3">
              <h2 className="text-xl font-bold text-indigo-300">
                ℹ️ Важная информация о выводе
              </h2>
              <button
                onClick={() => setShowInfoTips(false)}
                className="text-indigo-400 hover:text-indigo-300"
                title="Скрыть подсказку"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>

            <div className="space-y-3 text-indigo-100">
              <p>
                При выводе криптовалюты обратите внимание на следующие моменты:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                <li>
                  Убедитесь, что вы указываете правильный адрес кошелька
                  получателя. Транзакции в блокчейне необратимы!
                </li>
                <li>
                  Проверьте, что выбранная сеть (например, TRC20)
                  совместима с кошельком получателя.
                </li>
                <li>Комиссия за вывод составляет 0.1% от суммы.</li>
                <li>
                  Время обработки вывода может занимать от 15 минут до
                  нескольких часов в зависимости от загруженности сети.
                </li>
              </ul>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-900 bg-opacity-20 p-4 rounded-lg mb-6 border-l-4 border-red-500">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="bg-gray-800 rounded-xl p-6 shadow-lg"
        >
          {/* Выбор кошелька */}
          <div className="mb-6">
            <label
              htmlFor="wallet"
              className="block text-sm font-medium text-gray-400 mb-2"
            >
              Выберите кошелек для вывода:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {walletsArr
                .filter(
                  (wallet) =>
                    wallet.currency.symbol !== "USD" &&
                    wallet.currency.symbol !== "RUB"
                )
                .map((wallet) => (
                  <button
                    key={wallet.id}
                    type="button"
                    onClick={() => setSelectedWalletId(wallet.id)}
                    className={`p-4 rounded-lg flex items-center ${
                      selectedWalletId === wallet.id
                        ? "bg-purple-700 border-2 border-purple-500"
                        : "bg-gray-700 hover:bg-gray-650"
                    } transition`}
                  >
                    <div className="flex-shrink-0 mr-3">
                      {wallet.currency.icon && wallet.currency.icon.trim() !== '' ? (
                        <Image
                          src={wallet.currency.icon.startsWith('http') 
                            ? wallet.currency.icon 
                            : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${wallet.currency.icon}`
                          }
                          alt={wallet.currency.symbol}
                          width={32}
                          height={32}
                          className="rounded-full"
                          unoptimized
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const fallback = target.nextElementSibling as HTMLElement;
                            if (fallback) fallback.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div 
                        className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center font-bold"
                        style={{ display: wallet.currency.icon ? 'none' : 'flex' }}
                      >
                        {wallet.currency.symbol.slice(0, 2)}
                      </div>
                    </div>
                    <div className="flex-grow text-left">
                      <div className="font-medium text-white">{wallet.currency.name}</div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-400">
                          {wallet.currency.symbol}{" "}
                          {wallet.currency.network
                            ? `(${wallet.currency.network})`
                            : ""}
                        </span>
                        <span className="font-medium text-white">
                          {parseFloat(wallet.available_balance).toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
            </div>
          </div>

          {/* Отображение информации о выбранном кошельке */}
          {selectedWallet && (
            <div className="mb-4 p-4 bg-gray-700 rounded-lg flex items-center">
              <div className="mr-4">
                {selectedWallet.currency.icon && (
                  <Image
                    src={selectedWallet.currency.icon.startsWith('http') 
                      ? selectedWallet.currency.icon 
                      : `${(process.env.NEXT_PUBLIC_API_URL || '').replace(/\/api\/?$/, '')}${selectedWallet.currency.icon}`
                    }
                    alt={selectedWallet.currency.symbol}
                    width={32}
                    height={32}
                    unoptimized
                  />
                )}
              </div>
              <div>
                <div className="text-white">
                  <b>
                    {selectedWallet.currency.symbol} (
                    {selectedWallet.currency.network})
                  </b>
                </div>
                <div className="text-xs text-gray-300 break-all">
                  Адрес: {selectedWallet.address}
                </div>
                <div className="text-xs text-gray-300">
                  Баланс: {selectedWallet.balance}
                </div>
              </div>
            </div>
          )}

          {/* Сумма вывода */}
          <div className="mb-6">
            <label
              htmlFor="amount"
              className="block text-sm font-medium text-gray-400 mb-2"
            >
              Сумма вывода:
            </label>
            <div className="relative">
              <input
                id="amount"
                type="text"
                value={amount}
                onChange={handleAmountChange}
                placeholder="0.0"
                className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-3 pr-20"
              />
              <button
                type="button"
                onClick={setMaxAmount}
                disabled={maxAmountLoading}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 disabled:cursor-not-allowed text-white text-xs py-1 px-2 rounded transition flex items-center gap-1"
              >
                {maxAmountLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                    <span>...</span>
                  </>
                ) : (
                  "МАКС"
                )}
              </button>
            </div>
            {selectedWallet && (
              <p className="mt-1 text-sm text-gray-400">
                Доступно: {getMaxAvailableAmount()}{" "}
                {selectedWallet.currency.symbol}
              </p>
            )}
          </div>

          {/* Адрес получателя */}
          <div className="mb-6">
            <label
              htmlFor="address"
              className="block text-sm font-medium text-gray-400 mb-2"
            >
              Адрес кошелька получателя:
            </label>
            <input
              id="address"
              type="text"
              value={destinationAddress}
              onChange={(e) => setDestinationAddress(e.target.value)}
              placeholder="Введите адрес кошелька получателя"
              className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-3"
            />
            <p className="mt-1 text-sm text-yellow-400">
              ⚠️ Внимательно проверьте адрес! Транзакции в блокчейне необратимы.
            </p>
          </div>

          {/* MEMO/tag, если требуется */}
          {requiresMemo && (
            <div className="mb-6">
              <label
                htmlFor="memo"
                className="block text-sm font-medium text-gray-400 mb-2"
              >
                MEMO / Tag (обязательно для этой валюты):
              </label>
              <input
                id="memo"
                type="text"
                value={memo}
                onChange={(e) => setMemo(e.target.value)}
                placeholder="Введите MEMO/Tag для вывода"
                className="block w-full bg-gray-700 border-gray-600 rounded-md shadow-sm text-white p-3"
                required={requiresMemo}
              />
              <p className="mt-1 text-sm text-yellow-400">
                ⚠️ Для этой валюты/сети обязательно указывать MEMO/Tag. Без него
                средства могут быть утеряны!
              </p>
            </div>
          )}

          {/* Информация о комиссии */}
          {selectedWalletId &&
            amount &&
            !isNaN(parseFloat(amount)) &&
            parseFloat(amount) > 0 && (
              <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                <h3 className="text-sm font-medium text-gray-300 mb-3">
                  Детали вывода:
                </h3>
                {costLoading ? (
                  <div className="text-center text-gray-400">
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span className="ml-2">Расчет стоимости...</span>
                  </div>
                ) : withdrawalCost ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Сумма вывода:</span>
                      <span className="text-white">
                        {withdrawalCost.withdrawal_amount}{" "}
                        {withdrawalCost.currency_symbol}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Комиссия платформы:</span>
                      <span className="text-yellow-400">
                        {withdrawalCost.platform_fee}{" "}
                        {withdrawalCost.currency_symbol}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Стоимость газа:</span>
                      <span className="text-orange-400">
                        {withdrawalCost.gas_cost}{" "}
                        {withdrawalCost.currency_symbol}
                      </span>
                    </div>
                    <div className="flex justify-between font-medium pt-2 border-t border-gray-600">
                      <span className="text-white">Общая стоимость:</span>
                      <span className="text-red-400">
                        {withdrawalCost.total_cost}{" "}
                        {withdrawalCost.currency_symbol}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      Метод расчета: {withdrawalCost.calculation_method}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Сумма вывода:</span>
                      <span className="text-white">
                        {amount}{" "}
                        {
                          walletsArr.find((w) => w.id === selectedWalletId)?.currency
                            .symbol
                        }
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Комиссия:</span>
                      <span className="text-yellow-400">
                        {fee}{" "}
                        {
                          walletsArr.find((w) => w.id === selectedWalletId)?.currency
                            .symbol
                        }{" "}
                        (≈${feeUsd})
                      </span>
                    </div>
                    <div className="flex justify-between font-medium pt-2 border-t border-gray-600">
                      <span className="text-white">Итого к получению:</span>
                      <span className="text-green-400">
                        {netAmount}{" "}
                        {
                          walletsArr.find((w) => w.id === selectedWalletId)?.currency
                            .symbol
                        }
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

          {/* Предупреждение о безопасности */}
          <div className="mb-6 p-4 bg-yellow-900 bg-opacity-20 rounded-lg border-l-4 border-yellow-500">
            <h3 className="font-medium text-yellow-300 mb-2">
              Проверка безопасности
            </h3>
            <p className="text-sm text-yellow-200">
              Перед отправкой убедитесь, что:
            </p>
            <ul className="list-disc pl-5 mt-1 space-y-1 text-sm text-yellow-200">
              <li>Вы указали правильный адрес кошелька получателя</li>
              <li>Выбранная сеть совместима с кошельком получателя</li>
              <li>Сумма вывода не превышает доступный баланс</li>
            </ul>
          </div>

          {/* Кнопка отправки */}
          <div className="flex flex-col space-y-4">
            <button
              type="submit"
              disabled={
                submitting ||
                !selectedWalletId ||
                !amount ||
                !destinationAddress ||
                isNaN(parseFloat(amount)) ||
                parseFloat(amount) <= 0
              }
              className={`w-full py-3 px-4 rounded-lg flex items-center justify-center ${
                submitting ||
                !selectedWalletId ||
                !amount ||
                !destinationAddress ||
                isNaN(parseFloat(amount)) ||
                parseFloat(amount) <= 0
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-red-600 hover:bg-red-700"
              } text-white transition`}
            >
              {submitting ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Обработка...
                </>
              ) : (
                <>Вывести средства</>
              )}
            </button>

            <Link
              href="/wallet"
              className="text-center text-purple-400 hover:text-purple-300 transition"
            >
              Вернуться к кошельку
            </Link>
          </div>
        </form>

        {/* После компонента формы добавим компонент успешного вывода */}
        {success && (
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 shadow-lg mb-6">
            <div className="flex items-center mb-4">
              <div className="bg-green-900 rounded-full p-2 mr-3">
                <svg
                  className="w-6 h-6 text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white">
                Запрос на вывод средств отправлен
              </h3>
            </div>

            <p className="text-gray-300 mb-4">
              Ваш запрос на вывод средств был успешно создан и находится в
              обработке.
            </p>

            {withdrawalId && (
              <p className="text-sm text-gray-400 mb-2">
                ID транзакции: <span className="font-mono">{withdrawalId}</span>
              </p>
            )}

            {withdrawalStatus && (
              <div className="mt-4 p-4 bg-gray-700 rounded-lg border border-gray-600">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-400">Статус:</span>
                  <span
                    className={`font-medium px-2 py-1 rounded-full text-sm ${
                      withdrawalStatus.transaction.status === "completed"
                        ? "bg-green-900 text-green-300"
                        : withdrawalStatus.transaction.status === "pending"
                        ? "bg-yellow-900 text-yellow-300"
                        : withdrawalStatus.transaction.status === "processing"
                        ? "bg-blue-900 text-blue-300"
                        : withdrawalStatus.transaction.status === "cancelled"
                        ? "bg-gray-900 text-gray-300"
                        : withdrawalStatus.transaction.status === "failed"
                        ? "bg-red-900 text-red-300"
                        : "bg-gray-900 text-gray-300"
                    }`}
                  >
                    {withdrawalStatus.transaction.status_display ||
                      withdrawalStatus.transaction.status}
                  </span>
                </div>

                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-400">Адрес получателя:</span>
                  <span className="font-mono text-sm truncate max-w-[200px] text-gray-300">
                    {withdrawalStatus.destination_address}
                  </span>
                </div>

                {(withdrawalStatus.transaction.status === "pending" ||
                  withdrawalStatus.transaction.status === "processing") && (
                  <button
                    onClick={() => cancelWithdrawal(withdrawalStatus.id)}
                    disabled={cancelling}
                    className="mt-3 w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md transition-colors disabled:opacity-50"
                  >
                    {cancelling ? "Отмена..." : "Отменить вывод"}
                  </button>
                )}
              </div>
            )}

            <div className="mt-4">
              <button
                onClick={() => setSuccess(false)}
                className="text-purple-400 hover:text-purple-300 underline"
              >
                Создать новый запрос на вывод
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};