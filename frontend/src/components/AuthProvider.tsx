"use client";

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { usePathname } from 'next/navigation';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const disableAutoLogin = useAuthStore((state) => state.disableAutoLogin);
  const setDisableAutoLogin = useAuthStore((state) => state.setDisableAutoLogin);
  const isLoadingInitial = useAuthStore((state) => state.isLoading && state.user === null && !state.isAuthenticated);
  const pathname = usePathname();
  const [isInitialized, setIsInitialized] = useState(false);

  // Проверяем куки при загрузке и после обновления
  useEffect(() => {
    if (typeof window !== 'undefined' && !isInitialized) {
      // Проверяем наличие параметра force_login в URL
      const urlParams = new URLSearchParams(window.location.search);
      const forceLogin = urlParams.get('force_login') === 'true';
      
      // Если установлен force_login, принудительно очищаем все данные
      if (forceLogin) {
        console.log('Принудительная очистка данных авторизации');
        
        // Очищаем все куки
        const cookies = [
          'access_token',
          'refresh_token',
          'sessionid',
          'dj_session_id',
          'csrftoken',
          'auth_token',
          'next_hmr_refresh_hash'
        ];
        
        cookies.forEach(cookie => {
          document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
          document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
        });
        
        // Очищаем localStorage и sessionStorage
        localStorage.clear();
        sessionStorage.clear();
        
        // Устанавливаем флаг блокировки автовхода
        localStorage.setItem('disableAutoLogin', 'true');
        setDisableAutoLogin(true);
        
        setIsInitialized(true);
        return;
      }
      
      // Проверяем флаг disableAutoLogin в localStorage
      const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
      
      // Проверяем наличие JWT токенов
      // Добавляем более подробную проверку для отладки
      console.log('Проверяем куки:', document.cookie);
      
      const hasAccessToken = document.cookie.includes('access_token=');
      const hasRefreshToken = document.cookie.includes('refresh_token=');
      const hasOldAuthToken = document.cookie.includes('auth-token=');
      const hasOldRefreshToken = document.cookie.includes('refresh-token=');
      
      console.log('Результаты проверки куки:', {
        hasAccessToken,
        hasRefreshToken,
        hasOldAuthToken,
        hasOldRefreshToken
      });
      
      const hasSession = hasAccessToken || hasRefreshToken || hasOldAuthToken || hasOldRefreshToken;
      
      console.log('AuthProvider init: hasSession =', hasSession, 'disableAutoLogin =', storedDisableAutoLogin);
      
      // Если был установлен флаг отключения автовхода, принудительно очищаем куки
      if (storedDisableAutoLogin) {
        console.log('Флаг отключения автовхода активен, блокируем автоматический вход');
        
        // Очищаем JWT куки
        document.cookie = 'auth-token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'refresh-token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        
        // Дополнительно очищаем куки с разными параметрами path и domain
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax';
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax';
        document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax';
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax';
        
        // Обновляем состояние
        setDisableAutoLogin(true);
      }
      // Если есть сессия и нет флага отключения автовхода - проверяем авторизацию
      else if (hasSession && !storedDisableAutoLogin) {
        console.log('Обнаружена активная сессия, проверяем авторизацию');
        localStorage.removeItem('disableAutoLogin');
        setDisableAutoLogin(false);
        checkAuthStatus();
      } 
      // Если нет сессии, устанавливаем флаг блокировки автовхода
      else if (!hasSession) {
        console.log('Сессия не обнаружена, устанавливаем флаг блокировки автовхода');
        localStorage.setItem('disableAutoLogin', 'true');
        setDisableAutoLogin(true);
      }
      
      setIsInitialized(true);
    }
  }, [isInitialized, setDisableAutoLogin, checkAuthStatus]);

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