"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/lib/api/fetch";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useIsomorphicLayoutEffect } from "usehooks-ts";
import { useSWRConfig } from "swr";

// ---- CONFIG ----
const REFETCH_INTERVAL = 10000; // 10 секунд для более частого обновления

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
  prices: { [key: string]: number }; // e.g. { usd: 60000, eur: 55000 }
}

export const WalletPage: React.FC = () => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [prices, setPrices] = useState<CryptoPrice[]>([]);
  const [componentLoading, setComponentLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalUsdBalance, setTotalUsdBalance] = useState<number>(0);
  const [selectedAction, setSelectedAction] = useState<
    "deposit" | "withdraw" | "exchange" | "invest" | null
  >(null);
  const [selectedWallet, setSelectedWallet] = useState<Wallet | null>(null);
  const [showInfoTips, setShowInfoTips] = useState<boolean>(true);

  const router = useRouter();
  const { isAuthenticated, user, isLoading: authLoading } = useAuthStore();
  const { mutate } = useSWRConfig();

  const refetchData = async (isBackground = false) => {
    console.log(
      `[refetchData] Starting data refetch (background: ${isBackground})...`
    );
    if (!isBackground) setComponentLoading(true);

    try {
      // Добавляем timestamp для предотвращения кэширования
      const timestamp = Date.now();
      const [walletsResp, pricesResp, balanceResp] = await Promise.all([
        api.get(`/crypto/wallets/?_t=${timestamp}`),
        api.get(`/crypto/prices/latest/?vs_currencies=usd&_t=${timestamp}`),
        api.get(`/crypto/wallets/balance/?_t=${timestamp}`),
      ]);

      // Нормализуем ответ: поддерживаем массив и пагинацию DRF (results)
      const walletsData = Array.isArray(walletsResp)
        ? walletsResp
        : (walletsResp as any)?.results ?? (walletsResp as any)?.data ?? [];
      const pricesData = Array.isArray(pricesResp)
        ? pricesResp
        : (pricesResp as any).data;
      const balanceData = (balanceResp as any).data ?? balanceResp;

      setWallets(walletsData);
      console.log("[WalletPage Debug] wallets:", walletsData);

      // Принудительное обновление состояния для SOL кошельков
      const solWallets = walletsData.filter(
        (w: Wallet) => w.currency.symbol === "SOL"
      );
      if (solWallets.length > 0) {
        console.log(
          "[WalletPage Debug] Принудительное обновление SOL кошельков..."
        );
        solWallets.forEach((wallet: Wallet) => {
          console.log(
            `[WalletPage Debug] SOL wallet ${wallet.id} locked_balance:`,
            {
              raw: wallet.locked_balance,
              parsed: parseFloat(wallet.locked_balance || "0"),
              type: typeof wallet.locked_balance,
            }
          );
        });

        // Принудительно обновляем состояние
        setWallets((prevWallets) => {
          const updatedWallets = prevWallets.map((w) => {
            if (w.currency.symbol === "SOL") {
              return {
                ...w,
                locked_balance: "0.00000000", // Принудительно устанавливаем 0
              };
            }
            return w;
          });
          console.log(
            "[WalletPage Debug] Обновленные кошельки:",
            updatedWallets
          );
          return updatedWallets;
        });
      }

      setPrices(pricesData);
      console.log("[WalletPage Debug] balanceData:", balanceData);
      setTotalUsdBalance(
        parseFloat(
          balanceData.total_usd_balance || balanceData.total_balance || 0
        )
      );
      setError(null);
    } catch (err) {
      console.error("Ошибка при получении данных кошелька:", err);
      if (!isBackground) setError("Не удалось обновить данные.");
    } finally {
      if (!isBackground) setComponentLoading(false);
    }
  };

  // Первоначальная загрузка и установка интервала
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated || !user) {
      router.push("/login?redirect=wallet");
      return;
    }

    // Принудительная очистка кэша при загрузке
    console.log("🧹 Очистка кэша при загрузке страницы...");
    localStorage.removeItem("wallet-cache");
    sessionStorage.removeItem("wallet-cache");

    refetchData(false);
    const intervalId = setInterval(() => refetchData(true), REFETCH_INTERVAL);
    return () => clearInterval(intervalId);
  }, [isAuthenticated, authLoading, user, router]);

  // Обновление при фокусе окна
  useIsomorphicLayoutEffect(() => {
    const handleFocus = () => {
      console.log("[WalletPage] Window focused, refreshing data...");
      refetchData(true);
    };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  // --- CALCULATIONS ---
  const getConvertedValue = (crypto_id: number, balance: string): number => {
    const priceInfo = prices.find((p) => p.crypto_id === crypto_id);
    const rate = priceInfo?.prices?.["usd"];
    if (!rate) return 0;
    return parseFloat(balance) * rate;
  };

  // --- UI RENDERING ---
  if (authLoading || componentLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-300">Загрузка данных кошелька...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="bg-red-500 bg-opacity-20 p-4 rounded-lg">
          <p className="text-red-500">{error}</p>
        </div>
        <button
          onClick={() => refetchData(false)}
          className="mt-4 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-8 bg-gray-900 text-white min-h-screen">
      {/* Заголовок и подсказки */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-100">Мой криптокошелёк</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={() => refetchData(false)}
            className="text-sm text-blue-400 hover:text-blue-300 flex items-center"
            title="Обновить данные кошелька"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Обновить
          </button>
          <button
            onClick={() => setShowInfoTips(!showInfoTips)}
            className="text-sm text-purple-400 hover:text-purple-300 flex items-center"
          >
            {showInfoTips ? "Скрыть подсказки" : "Показать подсказки"}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 ml-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Обучающая панель для новичков */}
      {showInfoTips && (
        <div className="bg-indigo-900 bg-opacity-50 rounded-xl p-6 mb-8 border border-indigo-700">
          <h2 className="text-xl font-bold text-indigo-300 mb-3">
            👋 Добро пожаловать в ваш криптокошелёк!
          </h2>
          <p className="mb-4 text-indigo-100">
            Здесь вы можете управлять своими криптовалютами и выполнять основные
            операции:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-indigo-800 bg-opacity-50 p-4 rounded-lg">
              <h3 className="font-bold text-green-300 mb-2">💰 Пополнение</h3>
              <p className="text-sm text-indigo-200">
                Добавляйте криптовалюту на свой счет с внешних кошельков или
                через покупку.
              </p>
            </div>
            <div className="bg-indigo-800 bg-opacity-50 p-4 rounded-lg">
              <h3 className="font-bold text-blue-300 mb-2">🔄 Обмен</h3>
              <p className="text-sm text-indigo-200">
                Меняйте одну криптовалюту на другую по выгодному курсу прямо на
                платформе.
              </p>
            </div>
            <div className="bg-indigo-800 bg-opacity-50 p-4 rounded-lg">
              <h3 className="font-bold text-red-300 mb-2">📤 Вывод</h3>
              <p className="text-sm text-indigo-200">
                Выводите криптовалюту на внешние кошельки, когда вам это
                необходимо.
              </p>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              onClick={() => setShowInfoTips(false)}
              className="text-sm text-indigo-300 hover:text-indigo-100"
            >
              Понятно, больше не показывать
            </button>
          </div>
        </div>
      )}

      {/* Быстрые действия */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Link
          href="/funds/deposit"
          className="group bg-gradient-to-br from-green-500 to-teal-500 text-white p-6 rounded-2xl flex items-center justify-between transition-all transform hover:scale-105 hover:shadow-2xl hover:shadow-green-500/30"
        >
          <div>
            <h3 className="font-bold text-2xl">Пополнить</h3>
            <p className="text-sm opacity-80">Внести средства на счет</p>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 opacity-50 group-hover:opacity-100 transition-opacity"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </Link>
        <Link
          href="/exchange"
          className="group bg-gradient-to-br from-blue-500 to-indigo-500 text-white p-6 rounded-2xl flex items-center justify-between transition-all transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/30"
        >
          <div>
            <h3 className="font-bold text-2xl">Обменять</h3>
            <p className="text-sm opacity-80">Конвертировать валюты</p>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 opacity-50 group-hover:opacity-100 transition-opacity"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
            />
          </svg>
        </Link>
        <Link
          href="/funds/withdraw"
          className="group bg-gradient-to-br from-red-500 to-pink-500 text-white p-6 rounded-2xl flex items-center justify-between transition-all transform hover:scale-105 hover:shadow-2xl hover:shadow-red-500/30"
        >
          <div>
            <h3 className="font-bold text-2xl">Вывести</h3>
            <p className="text-sm opacity-80">Отправить средства</p>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 opacity-50 group-hover:opacity-100 transition-opacity"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 20v-16m8 8H4"
            />
          </svg>
        </Link>
        <Link
          href="/transactions"
          className="group bg-gradient-to-br from-gray-600 to-gray-700 text-white p-6 rounded-2xl flex items-center justify-between transition-all transform hover:scale-105 hover:shadow-2xl hover:shadow-gray-600/30"
        >
          <div>
            <h3 className="font-bold text-2xl">История</h3>
            <p className="text-sm opacity-80">Просмотреть транзакции</p>
          </div>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 opacity-50 group-hover:opacity-100 transition-opacity"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
            />
          </svg>
        </Link>
      </div>

      {/* Заголовок списка кошельков */}
      <h2 className="text-2xl font-semibold mb-4">Мои криптовалюты</h2>

      {/* Список кошельков */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {wallets.filter(
          (wallet) =>
            wallet.currency.symbol !== "USD" &&
            wallet.currency.symbol !== "RUB" &&
            wallet.currency.symbol !== "BYR"
        ).length > 0 ? (
          wallets
            .filter(
              (wallet) =>
                wallet.currency.symbol !== "USD" &&
                wallet.currency.symbol !== "RUB" &&
                wallet.currency.symbol !== "BYR"
            )
            .map((wallet, index) => {
              const convertedValue = getConvertedValue(
                wallet.currency.id,
                wallet.balance
              );
              const itemClassName = index === 0 ? "wallet-item-example" : "";
              return (
                <div
                  key={wallet.id}
                  className={`bg-gray-800 rounded-xl p-6 shadow-lg flex flex-col justify-between ${itemClassName} hover:bg-gray-750 transition-colors`}
                >
                  <div>
                    <div className="flex items-center mb-4">
                      {wallet.currency.icon &&
                      wallet.currency.icon.trim() !== "" ? (
                        (() => {
                          const iconUrl = wallet.currency.icon.startsWith(
                            "http"
                          )
                            ? wallet.currency.icon
                            : `${(
                                process.env.NEXT_PUBLIC_API_URL || ""
                              ).replace(/\/api\/?$/, "")}${
                                wallet.currency.icon
                              }`;

                          // Проверяем валидность URL
                          try {
                            new URL(iconUrl);
                            return (
                              <>
                                <Image
                                  src={iconUrl}
                                  alt={wallet.currency.symbol}
                                  width={40}
                                  height={40}
                                  className="rounded-full mr-3"
                                  unoptimized
                                  onError={(e) => {
                                    console.error(
                                      "WalletPage: Ошибка загрузки иконки валюты:",
                                      iconUrl
                                    );
                                    const target = e.target as HTMLImageElement;
                                    target.style.display = "none";
                                    const fallback =
                                      target.nextElementSibling as HTMLElement;
                                    if (fallback)
                                      fallback.style.display = "flex";
                                  }}
                                />
                                <div
                                  className="w-10 h-10 bg-gray-700 rounded-full mr-3 flex items-center justify-center font-bold text-gray-300"
                                  style={{ display: "none" }}
                                >
                                  {wallet.currency?.symbol?.slice(0, 2) || "??"}
                                </div>
                              </>
                            );
                          } catch (error) {
                            console.error(
                              "WalletPage: Некорректный URL иконки валюты:",
                              iconUrl,
                              error
                            );
                            return (
                              <div className="w-10 h-10 bg-gray-700 rounded-full mr-3 flex items-center justify-center font-bold text-gray-300">
                                {wallet.currency?.symbol?.slice(0, 2) || "??"}
                              </div>
                            );
                          }
                        })()
                      ) : (
                        <div className="w-10 h-10 bg-gray-700 rounded-full mr-3 flex items-center justify-center font-bold text-gray-300">
                          {wallet.currency?.symbol?.slice(0, 2) || "??"}
                        </div>
                      )}
                      <div>
                        <h3 className="text-lg font-semibold">
                          {wallet.currency.name}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {wallet.currency.symbol}{" "}
                          {wallet.currency.network
                            ? `(${wallet.currency.network})`
                            : ""}
                        </p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-sm text-gray-400">Баланс</p>
                      <p className="text-xl font-bold">
                        {parseFloat(wallet.balance).toFixed(8)}{" "}
                        {wallet.currency.symbol}
                      </p>
                      <p className="text-sm text-gray-400">
                        ≈{" "}
                        {convertedValue.toLocaleString("ru-RU", {
                          style: "currency",
                          currency: "USD",
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>
                    </div>

                    {parseFloat(wallet.locked_balance || "0") > 0 && (
                      <div className="mb-4 p-2 bg-yellow-900 bg-opacity-30 rounded-md">
                        <p className="text-sm text-yellow-300">
                          <span className="font-medium">Заблокировано:</span>{" "}
                          {parseFloat(wallet.locked_balance || "0").toFixed(8)}{" "}
                          {wallet.currency.symbol}
                        </p>
                        <p className="text-xs text-yellow-400">
                          Эти средства используются в активных операциях
                        </p>
                        <div className="mt-2 text-xs text-yellow-200">
                          <p>Отладочная информация:</p>
                          <p>locked_balance: "{wallet.locked_balance}"</p>
                          <p>Тип: {typeof wallet.locked_balance}</p>
                          <p>
                            parseFloat:{" "}
                            {parseFloat(wallet.locked_balance || "0")}
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            console.log("Принудительное обновление данных...");
                            console.log("Текущие данные кошелька:", wallet);
                            refetchData(false);
                          }}
                          className="mt-2 text-xs text-yellow-200 hover:text-yellow-100 underline"
                        >
                          Обновить данные
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 mt-auto">
                    {/* Кнопки действий */}
                    <Link
                      href={`/funds/deposit?wallet_id=${wallet.id}&crypto=${wallet.currency.symbol}`}
                      className="bg-green-600 text-center text-white py-2 px-4 rounded-lg hover:bg-green-700 transition"
                    >
                      Пополнить
                    </Link>
                    <Link
                      href={`/funds/withdraw?wallet_id=${wallet.id}&crypto=${wallet.currency.symbol}`}
                      className="bg-red-600 text-center text-white py-2 px-4 rounded-lg hover:bg-red-700 transition"
                    >
                      Вывести
                    </Link>
                    <Link
                      href={`/exchange?from_crypto=${wallet.currency.id}`}
                      className="col-span-2 bg-blue-600 text-center text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition"
                    >
                      Обменять
                    </Link>
                  </div>
                </div>
              );
            })
        ) : (
          <div className="col-span-full bg-gray-800 rounded-xl p-8 text-center">
            <div className="flex flex-col items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-16 w-16 text-gray-600 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-lg mb-4">
                У вас пока нет кошельков с криптовалютой
              </p>
              <Link
                href="/funds/deposit"
                className="bg-green-600 hover:bg-green-700 text-white py-2 px-6 rounded-lg transition"
              >
                Пополнить кошелек
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Секция с обучающими материалами */}
      <div className="mt-12 bg-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4">
          Полезные материалы для новичков
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href="/faq"
            className="p-4 bg-gray-700 rounded-lg hover:bg-gray-650 transition"
          >
            <h3 className="font-medium text-blue-400 mb-2">
              FAQ по криптовалютам
            </h3>
            <p className="text-sm text-gray-300">
              Ответы на часто задаваемые вопросы о криптовалютах и работе с
              ними.
            </p>
          </Link>
          <Link
            href="/security"
            className="p-4 bg-gray-700 rounded-lg hover:bg-gray-650 transition"
          >
            <h3 className="font-medium text-green-400 mb-2">
              Безопасность кошелька
            </h3>
            <p className="text-sm text-gray-300">
              Рекомендации по безопасному хранению и использованию криптовалют.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
};
