"use client";

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { usePathname } from 'next/navigation';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const disableAutoLogin = useAuthStore((state) => state.disableAutoLogin);
  const setDisableAutoLogin = useAuthStore((state) => state.setDisableAutoLogin);
  const pathname = usePathname();
  const [isInitialized, setIsInitialized] = useState(false);

  // Проверяем куки при загрузке и после обновления
  useEffect(() => {
    if (typeof window !== 'undefined' && !isInitialized) {
      const urlParams = new URLSearchParams(window.location.search);
      const forceLogin = urlParams.get('force_login') === 'true';
      const cookieString = document.cookie;
      const hasAnyToken = cookieString.includes('access_token') || 
                          cookieString.includes('refresh_token') || 
                          cookieString.includes('sessionid'); // Fallback check

      if (forceLogin) {
        console.log('AuthProvider: Принудительная очистка данных авторизации из-за force_login');
        localStorage.removeItem('user');
        localStorage.removeItem('auth-storage'); 
        localStorage.setItem('disableAutoLogin', 'true');
        setDisableAutoLogin(true); 
        useAuthStore.setState({ isAuthenticated: false, user: null, isLoading: false }); // Ensure loading is false
        setIsInitialized(true);
        return;
      }

      const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
      console.log('AuthProvider init: storedDisableAutoLogin =', storedDisableAutoLogin, ', Zustand disableAutoLogin =', disableAutoLogin);

      // Новая логика: всегда вызываем checkAuthStatus, если автовход не выключен в localStorage
      if (!storedDisableAutoLogin) {
        console.log('AuthProvider init: Автовход не выключен (storedDisableAutoLogin=false). Вызов checkAuthStatus().');
        // Если Zustand disableAutoLogin был true, но localStorage говорит, что автовход разрешен, синхронизируем Zustand
        if (disableAutoLogin) { 
            setDisableAutoLogin(false); 
        }
        // checkAuthStatus() сам управляет localStorage.removeItem('disableAutoLogin') при успехе
        checkAuthStatus(); // Всегда пытаемся проверить сессию через API, если автовход не запрещен
      } else {
        // Автовход выключен через localStorage
        console.log('AuthProvider init: Автовход выключен (storedDisableAutoLogin=true). Устанавливаем неаутентифицированное состояние.');
        useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, disableAutoLogin: true });
      }
      setIsInitialized(true);
    }
  }, [isInitialized, checkAuthStatus, setDisableAutoLogin, disableAutoLogin, pathname]); // Added pathname to dependencies if urlParams are used

  // Эффект для проверки авторизации при смене страницы
  useEffect(() => {
    // Проверяем все куки для отладки
    console.log('Все куки:', document.cookie);
    
    // Проверяем токены в localStorage
    console.log('Токены в localStorage:', {
      access_token: localStorage.getItem('access_token'),
      refresh_token: localStorage.getItem('refresh_token')
    });
    
    // Выполняем логику только если не идет загрузка из useAuthStore и другие условия соблюдены
    if (!isLoading && !['/login', '/register'].includes(pathname) && isInitialized && !disableAutoLogin) {
      // Проверяем наличие JWT токенов (это упрощенная проверка, т.к. HttpOnly куки не видны)
      const hasSession = document.cookie.includes('auth-token=') || 
                        document.cookie.includes('refresh-token=') ||
                        document.cookie.includes('access_token=') || // Для обратной совместимости или не-HttpOnly токенов
                        document.cookie.includes('refresh_token='); // Для обратной совместимости

      console.log('AuthProvider (isInitialized, !isLoading, !disableAutoLogin): Проверка сессии:', { hasSession, pathname, isAuthenticated });
      
      // Если есть токены (по мнению document.cookie), но не авторизованы в состоянии - проверяем статус
      if (hasSession && !isAuthenticated) {
        console.log('AuthProvider: Есть JWT токены в куках (клиентских), но isAuthenticated false. Проверяем статус.');
        localStorage.removeItem('disableAutoLogin'); // Разрешаем автовход для этой проверки
        setDisableAutoLogin(false);
        checkAuthStatus();
      }
      // Если нет токенов (по мнению document.cookie), но статус авторизации true в состоянии
      else if (!hasSession && isAuthenticated) {
        // Проверяем, есть ли данные пользователя в сторе.
        if (!useAuthStore.getState().user) { 
          // Если данных пользователя нет, это может быть "зависшее" состояние isAuthenticated. Сбрасываем.
          console.log('AuthProvider: Нет JWT токенов в куках (клиентских), isAuthenticated был true, НО user is null. Принудительный сброс.');
          useAuthStore.setState({ isAuthenticated: false, user: null, tokens: null, isLoading: false });
          localStorage.setItem('disableAutoLogin', 'true'); // Блокируем автовход после сброса
          setDisableAutoLogin(true);
        } else {
          // Данные пользователя есть. Это, скорее всего, ситуация сразу после логина (HttpOnly куки)
          // или успешного checkAuthStatus. Доверяем состоянию стора.
          console.log('AuthProvider: Нет JWT токенов в куках (клиентских), но isAuthenticated true И user существует. Доверяем состоянию из store (возможно, HttpOnly куки).');
        }
      }
    } else if (isLoading) {
      console.log('AuthProvider: Проверка сессии пропущена, так как isLoading is true.');
    } else if (!isInitialized) {
      console.log('AuthProvider: Проверка сессии пропущена, так как isInitialized is false.');
    } else if (disableAutoLogin) {
       console.log('AuthProvider: Проверка сессии пропущена, так как disableAutoLogin is true.');
    }
  }, [pathname, isInitialized, isAuthenticated, checkAuthStatus, setDisableAutoLogin, disableAutoLogin, isLoading]); // Добавили isLoading

  // Пример глобального лоадера на время самой первой проверки сессии
  // if (isLoadingInitial) {
  //   return (
  //     <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
  //       Загрузка сессии...
  //     </div>
  //   );
  // }

  return <>{children}</>;
}; 