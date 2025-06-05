"use client";

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { usePathname } from 'next/navigation';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
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

      if (!storedDisableAutoLogin && hasAnyToken) {
        console.log('AuthProvider init: Обнаружены токены и автовход не выключен, пытаемся проверить авторизацию.');
        if (disableAutoLogin) {
            setDisableAutoLogin(false);
        }
        localStorage.removeItem('disableAutoLogin');
        checkAuthStatus(); // This will manage isLoading: true -> false
      } else {
        console.log('AuthProvider init: Токены не обнаружены или автовход выключен. Автоматический вход невозможен. Установка isLoading: false.');
        useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false, disableAutoLogin: storedDisableAutoLogin });
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
    
    // Пропускаем страницы логина/регистрации и первую загрузку
    if (!['/login', '/register'].includes(pathname) && isInitialized && !disableAutoLogin) {
      // Проверяем наличие JWT токенов
      const hasSession = document.cookie.includes('auth-token=') || 
                        document.cookie.includes('refresh-token=') ||
                        document.cookie.includes('access_token=') ||
                        document.cookie.includes('refresh_token=');
      
      console.log('Проверка сессии:', { hasSession, pathname, isAuthenticated });
      
      // Если есть токены, но не авторизованы в состоянии - проверяем статус
      if (hasSession && !isAuthenticated) {
        console.log('Есть JWT токены, но не авторизованы в состоянии - проверяем статус');
        localStorage.removeItem('disableAutoLogin');
        setDisableAutoLogin(false);
        checkAuthStatus();
      }
      // Если нет токенов, но статус авторизации true - выполняем проверку
      else if (!hasSession && isAuthenticated) {
        console.log('Нет JWT токенов, но статус авторизации true - проверяем статус');
        checkAuthStatus();
      }
    }
  }, [pathname, isInitialized, isAuthenticated, checkAuthStatus, setDisableAutoLogin, disableAutoLogin]);

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