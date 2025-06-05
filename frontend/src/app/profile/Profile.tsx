"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "@/lib/ThemeProvider";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

export const Profile = () => {
  const { theme, toggleTheme } = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    console.log(`[Profile useEffect] Running. authLoading: ${authLoading}, isAuthenticated: ${isAuthenticated}`);
    if (!authLoading) {
      if (!isAuthenticated) {
        console.log(`[Profile useEffect] Condition met: !authLoading (${!authLoading}) && !isAuthenticated (${!isAuthenticated}). Redirecting to /login.`);
        router.push('/login?from=profile');
      } else {
        console.log(`[Profile useEffect] Condition met: !authLoading (${!authLoading}) && isAuthenticated (${isAuthenticated}). User is authenticated. No redirect.`);
      }
    } else {
      console.log(`[Profile useEffect] authLoading is true. Waiting for auth check to complete.`);
    }
  }, [isAuthenticated, authLoading, router]);

  console.log(`[Profile Render] authLoading: ${authLoading}, isAuthenticated: ${isAuthenticated}, user: ${user ? user.email : 'null'}`);

  if (authLoading) {
    console.log("[Profile Render] Displaying loading state because authLoading is true.");
    return (
      <div className="flex w-full min-h-screen bg-[#0d0d0d] text-white items-center justify-center">
        <div>Загрузка данных профиля...</div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    console.log(`[Profile Render] authLoading is false. Condition !isAuthenticated (${!isAuthenticated}) || !user (${!user}) is true. Returning null to allow useEffect to redirect or handle.`);
    return null;
  }

  console.log("[Profile Render] Proceeding to render profile content.");

  const userEmail = user.email || "N/A";
  const userName = user.username || user.first_name || "Пользователь";
  const userInitials = userName.substring(0, 2).toUpperCase();

  return (
    <div className="flex w-full min-h-screen bg-[#0d0d0d] text-white">
      {/* Боковая панель */}
      <div className="w-16 bg-black/30 flex flex-col items-center py-6">
        <div className="mb-8 flex flex-col gap-1">
          {[1, 2, 3].map((line) => (
            <div key={line} className="w-5 h-0.5 bg-white/70" />
          ))}
        </div>

        {/* Иконки навигации */}
        <div className="flex flex-col items-center gap-6">
          <button className="relative w-10 h-10 bg-white/10 rounded flex items-center justify-center">
            <div className="absolute left-[-8px] w-1 h-full bg-purple-600 rounded-sm" />
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 12L5 10M5 10L12 3L19 10M5 10V20C5 20.5523 5.44772 21 6 21H9M19 10L21 12M19 10V20C19 20.5523 18.5523 21 18 21H15M9 21C9.55228 21 10 20.5523 10 20V16C10 15.4477 10.4477 15 11 15H13C13.5523 15 14 15.4477 14 16V20C14 20.5523 14.4477 21 15 21M9 21H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <button className="w-10 h-10 flex items-center justify-center">
            <svg className="w-5 h-5 text-white/70" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 5H7C5.89543 5 5 5.89543 5 7V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V7C19 5.89543 18.1046 5 17 5H15M9 5C9 6.10457 9.89543 7 11 7H13C14.1046 7 15 6.10457 15 5M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5M12 12H15M12 16H15M9 12H9.01M9 16H9.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <button className="w-10 h-10 flex items-center justify-center">
            <svg className="w-5 h-5 text-white/70" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 19V13C9 11.8954 8.10457 11 7 11H5M9 19V6C9 4.89543 9.89543 4 11 4H13C14.1046 4 15 4.89543 15 6V19M9 19H5M15 19H19M15 8H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        <div className="mt-auto">
          <button onClick={toggleTheme} className="w-10 h-10 flex items-center justify-center text-white/70 hover:text-white">
            {theme === 'dark' ? (
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 3V4M12 20V21M21 12H20M4 12H3M18.364 18.364L17.657 17.657M6.343 6.343L5.636 5.636M18.364 5.636L17.657 6.343M6.343 17.657L5.636 18.364M16 12C16 14.2091 14.2091 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Основной контент */}
      <div className="flex-1 py-4 px-6">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <div className="bg-purple-600 rounded-full w-10 h-10 flex items-center justify-center text-sm font-medium">{userInitials}</div>
            <div>
              <p className="text-lg font-medium">{userName}</p>
              <p className="text-xs text-gray-400">С нами с {user.date_joined ? new Date(user.date_joined).toLocaleDateString('ru-RU') : 'недавно'}</p>
            </div>
          </div>
          <div className="flex gap-4">
            <button className="flex items-center justify-center w-10 h-10 bg-white/10 rounded hover:bg-white/20 transition-colors">
              <svg className="w-5 h-5 text-white/70" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 17H20L18.5951 15.5951C18.2141 15.2141 18 14.6973 18 14.1585V11C18 8.38757 16.3304 6.16509 14 5.34142V5C14 3.89543 13.1046 3 12 3C10.8954 3 10 3.89543 10 5V5.34142C7.66962 6.16509 6 8.38757 6 11V14.1585C6 14.6973 5.78595 15.2141 5.40493 15.5951L4 17H9M15 17V18C15 19.6569 13.6569 21 12 21C10.3431 21 9 19.6569 9 18V17M15 17H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <button className="flex items-center justify-center w-10 h-10 bg-white/10 rounded hover:bg-white/20 transition-colors">
              <svg className="w-5 h-5 text-white/70" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10.325 4.317C10.751 2.561 13.249 2.561 13.675 4.317C13.7389 4.5808 13.8642 4.82578 14.0407 5.032C14.2172 5.23822 14.4399 5.39985 14.6907 5.50375C14.9414 5.60764 15.2132 5.65085 15.4838 5.62987C15.7544 5.60889 16.0162 5.5243 16.248 5.383C17.791 4.443 19.558 6.209 18.618 7.753C18.4769 7.98466 18.3924 8.24634 18.3715 8.51677C18.3506 8.78721 18.3938 9.05877 18.4975 9.30938C18.6013 9.55999 18.7627 9.78258 18.9687 9.95905C19.1747 10.1355 19.4194 10.2609 19.683 10.325C21.439 10.751 21.439 13.249 19.683 13.675C19.4192 13.7389 19.1742 13.8642 18.968 14.0407C18.7618 14.2172 18.6001 14.4399 18.4963 14.6907C18.3924 14.9414 18.3491 15.2132 18.3701 15.4838C18.3911 15.7544 18.4757 16.0162 18.617 16.248C19.557 17.791 17.791 19.558 16.247 18.618C16.0153 18.4769 15.7537 18.3924 15.4832 18.3715C15.2128 18.3506 14.9412 18.3938 14.6906 18.4975C14.44 18.6013 14.2174 18.7627 14.0409 18.9687C13.8645 19.1747 13.7391 19.4194 13.675 19.683C13.249 21.439 10.751 21.439 10.325 19.683C10.2611 19.4192 10.1358 19.1742 9.95929 18.968C9.7828 18.7618 9.56011 18.6001 9.30935 18.4963C9.05859 18.3924 8.78683 18.3491 8.51621 18.3701C8.24559 18.3911 7.98375 18.4757 7.752 18.617C6.209 19.557 4.442 17.791 5.382 16.247C5.5231 16.0153 5.60755 15.7537 5.62848 15.4832C5.64942 15.2128 5.60624 14.9412 5.50247 14.6906C5.3987 14.44 5.23726 14.2174 5.03127 14.0409C4.82529 13.8645 4.58056 13.7391 4.317 13.675C2.561 13.249 2.561 10.751 4.317 10.325C4.5808 10.2611 4.82578 10.1358 5.032 9.95929C5.23822 9.7828 5.39985 9.56011 5.50375 9.30935C5.60764 9.05859 5.65085 8.78683 5.62987 8.51621C5.60889 8.24559 5.5243 7.98375 5.383 7.752C4.443 6.209 6.209 4.442 7.753 5.382C8.753 5.99 10.049 5.452 10.325 4.317Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M15 12C15 13.6569 13.6569 15 12 15C10.3431 15 9 13.6569 9 12C9 10.3431 10.3431 9 12 9C13.6569 9 15 10.3431 15 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        {/* Баланс и информация */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-black/30 rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Личный счет</span>
              <span className="text-xs px-2 py-1 bg-gray-800 rounded-full">USDT</span>
            </div>
            <div className="text-2xl font-bold mb-1">170.43 USDT</div>
            <div className="flex gap-2">
              <button className="bg-purple-600 hover:bg-purple-700 rounded-full text-white text-sm py-1 px-4 transition-colors">
                Пополнить
              </button>
              <button className="bg-gray-800 hover:bg-gray-700 rounded-full text-white text-sm py-1 px-4 transition-colors">
                Вывести
              </button>
            </div>
          </div>

          <div className="bg-black/30 rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Партнерский счет</span>
              <span className="text-xs px-2 py-1 bg-gray-800 rounded-full">USDT</span>
            </div>
            <div className="text-2xl font-bold mb-1">**** USDT</div>
            <div className="flex gap-2">
              <button className="bg-purple-600 hover:bg-purple-700 rounded-full text-white text-sm py-1 px-4 transition-colors">
                Пополнить
              </button>
              <button className="bg-gray-800 hover:bg-gray-700 rounded-full text-white text-sm py-1 px-4 transition-colors">
                Вывести
              </button>
            </div>
          </div>
        </div>

        {/* Пользовательская информация */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-black/30 rounded-lg p-5">
            <h3 className="text-lg font-medium mb-4">Информация о пользователе</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">ID пользователя</span>
                <span>{user.id || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Верификация</span>
                <span className={user.is_verified ? "text-green-400" : "text-red-400"}>
                  {user.is_verified ? "Верифицирован" : "Не верифицирован"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Тип пользователя</span>
                <span>Личный</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">VIP уровень</span>
                <span>Нету</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Почта</span>
                <span>{userEmail}</span>
              </div>
            </div>
          </div>

          <div className="bg-black/30 rounded-lg p-5">
            <h3 className="text-lg font-medium mb-4">Реферальная программа</h3>
            <div className="mb-4">
              <p className="text-sm text-gray-400 mb-2">Ваша реферальная ссылка</p>
              <div className="flex">
                <input 
                  type="text" 
                  value={`https://crypto.com/referral/${user.username || user.id}`}
                  readOnly 
                  className="bg-gray-800 rounded-l-lg px-3 py-2 flex-1 outline-none"
                />
                <button className="bg-purple-600 hover:bg-purple-700 rounded-r-lg px-3 text-sm">
                  Копировать
                </button>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-2">Приглашено пользователей</p>
              <div className="flex items-center gap-3">
                <span className="text-xl font-bold">0</span>
                <span className="text-sm text-gray-400">Заработано: 0.00 USDT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Инвестиции */}
        <h2 className="text-2xl font-semibold mb-4">Инвестиции</h2>
        <div className="grid grid-cols-3 gap-4 mb-8">
          {['BTC', 'ETH', 'USDT'].map((coin, index) => (
            <div key={coin} className="bg-black/30 rounded-lg p-4">
              <div className="flex justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/10">
                    {coin === 'BTC' && (
                      <svg className="w-5 h-5 text-yellow-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,2C6.48,2,2,6.48,2,12s4.48,10,10,10s10-4.48,10-10S17.52,2,12,2z M16.15,11.53l-0.01,0c-0.12,0.47-0.38,0.79-0.77,0.99 c-0.36,0.19-0.82,0.3-1.35,0.3h-1.35v1.86h-0.65V12.5H10.4v2.18H9.75V12.5H8.54v-0.69h1.21v-4.5H8.54V6.64h1.21V4.91h0.65v1.73 h1.61V4.91h0.65v1.73h0.3c0.65,0,1.15,0.16,1.52,0.45c0.42,0.33,0.65,0.82,0.65,1.4c0,0.21-0.03,0.4-0.08,0.58 c-0.06,0.18-0.14,0.34-0.25,0.49s-0.24,0.27-0.4,0.37c-0.13,0.09-0.29,0.15-0.45,0.21v0.01c0.2,0.03,0.39,0.08,0.56,0.16 c0.21,0.09,0.39,0.21,0.55,0.37c0.16,0.16,0.28,0.36,0.37,0.59c0.09,0.23,0.12,0.5,0.12,0.81C16.26,11,16.22,11.28,16.15,11.53z"></path>
                        <path d="M12.57,8.74h-1.96v1.7h1.94c0.36,0,0.63-0.08,0.84-0.27c0.21-0.18,0.32-0.42,0.32-0.71c0-0.06-0.01-0.12-0.02-0.18 c-0.01-0.06-0.03-0.12-0.06-0.18c-0.03-0.06-0.06-0.11-0.11-0.16c-0.04-0.05-0.09-0.09-0.15-0.13c-0.07-0.04-0.16-0.08-0.25-0.1 c-0.09-0.02-0.2-0.04-0.3-0.05c-0.08-0.01-0.16-0.01-0.24-0.01C12.54,8.74,12.55,8.74,12.57,8.74z"></path>
                        <path d="M13.02,11.01h-2.4v1.31h2.38c0.41,0,0.72-0.06,0.93-0.21c0.21-0.15,0.32-0.35,0.32-0.61c0-0.31-0.15-0.55-0.38-0.68 C13.62,10.69,13.32,11.01,13.02,11.01z"></path>
                      </svg>
                    )}
                    {coin === 'ETH' && (
                      <svg className="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,1.75L5.75,12.25L12,16L18.25,12.25L12,1.75z M5.75,13.5L12,22.25L18.25,13.5L12,17.25L5.75,13.5z"></path>
                      </svg>
                    )}
                    {coin === 'USDT' && (
                      <svg className="w-5 h-5 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,2C6.48,2,2,6.48,2,12s4.48,10,10,10s10-4.48,10-10S17.52,2,12,2z M13.5,16.5H13v1h-2v-1H7.5v-2H9 c0.55,0,1-0.45,1-1V10c0-0.55-0.45-1-1-1H7.5V7.5h2V6.5h2v1h4V9.5H13c-0.55,0-1,0.45-1,1V14c0,0.55,0.45,1,1,1h2.5V16.5z"></path>
                      </svg>
                    )}
                  </div>
                  <div>
                    <div className="font-medium">{coin}</div>
                    <div className="text-xs text-gray-400">
                      {coin === 'BTC' && 'Bitcoin'}
                      {coin === 'ETH' && 'Ethereum'}
                      {coin === 'USDT' && 'Tether'}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  {['1г', '6м', '1м', '1н', '1д', '1ч'].map((period) => (
                    <button 
                      key={period} 
                      className={`text-xs px-1 py-0.5 rounded ${period === '1н' ? 'bg-purple-600' : 'hover:bg-gray-700'}`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* График (заглушка) */}
              <div className="h-40 bg-gray-800/50 rounded-lg mb-2 overflow-hidden">
                <div className="h-full w-full relative">
                  <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-transparent to-purple-500/20"></div>
                  <div className="absolute bottom-0 left-0 right-0 border-t border-purple-500/70"></div>
                  <svg className="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <path
                      d={`M0,${30 - (Math.random() * 10)} ${Array.from({length: 20}, (_, i) => {
                        return `L${i * 5},${30 - (Math.random() * 15)}`
                      }).join(' ')} L100,${30 - (Math.random() * 10)} V40 H0 Z`}
                      fill="rgba(147, 51, 234, 0.1)"
                      stroke="rgba(147, 51, 234, 0.5)"
                      strokeWidth="0.5"
                    />
                  </svg>
                </div>
              </div>
              
              <div className="flex justify-between mb-4 text-xs text-gray-400">
                <div>День: {index === 0 ? '+3.59%' : index === 1 ? '+2.83%' : '-0.01%'}</div>
                <div>Месяц: {index === 0 ? '+16.85%' : index === 1 ? '+10.76%' : '+0.01%'}</div>
              </div>
              
              <div className="flex gap-2">
                <button className="flex-1 bg-purple-600 hover:bg-purple-700 rounded-full text-white text-sm py-1 transition-colors">
                  Инвестировать
                </button>
                <button className="flex-1 bg-gray-800 hover:bg-gray-700 rounded-full text-white text-sm py-1 transition-colors">
                  Вывести
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 