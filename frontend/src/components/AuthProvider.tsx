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
      const urlParams = new URLSearchParams(window.location.search);
      const forceLogin = urlParams.get('force_login') === 'true';

      if (forceLogin) {
        console.log('AuthProvider: Принудительная очистка данных авторизации из-за force_login');
        const cookiesToClear = [
          'access_token', 'refresh_token', 'sessionid',
          'dj_session_id', 'csrftoken', 'auth_token',
          // 'next_hmr_refresh_hash' // этот можно оставить
        ];
        cookiesToClear.forEach(cookie => {
          document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
          document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
          document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        });
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        localStorage.removeItem('auth-storage'); // zustand persist key
        // sessionStorage.clear(); // Если используется
        
        localStorage.setItem('disableAutoLogin', 'true');
        setDisableAutoLogin(true); // Обновляем состояние в store
        setIsInitialized(true);
        return;
      }

      const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
      console.log('AuthProvider init: storedDisableAutoLogin =', storedDisableAutoLogin, ', Zustand disableAutoLogin =', disableAutoLogin);

      if (storedDisableAutoLogin) {
        console.log('AuthProvider init: Флаг disableAutoLogin активен, автоматический вход не будет выполнен.');
        if (!disableAutoLogin) { // Синхронизируем состояние Zustand, если оно отличается
            setDisableAutoLogin(true);
        }
        checkAuthStatus().finally(() => {
          console.log('[AuthProvider Init] checkAuthStatus completed. Final store state:', { 
            isAuthenticated: useAuthStore.getState().isAuthenticated, 
            user: useAuthStore.getState().user,
            tokens: useAuthStore.getState().tokens,
            disableAutoLogin: useAuthStore.getState().disableAutoLogin 
          });
          setIsInitialized(true);
        }); 
        return; 
      }

      // Если автологин не отключен (storedDisableAutoLogin === false), проверяем наличие токенов
      const accessTokenCookie = document.cookie.includes('access_token=');
      const refreshTokenCookie = document.cookie.includes('refresh_token=');
      const accessTokenLocal = localStorage.getItem('access_token');
      const refreshTokenLocal = localStorage.getItem('refresh_token');

      const hasAnyToken = accessTokenCookie || refreshTokenCookie || !!accessTokenLocal || !!refreshTokenLocal;
      console.log('AuthProvider init: Результаты проверки токенов:', {
        accessTokenCookie,
        refreshTokenCookie,
        hasAccessTokenLocal: !!accessTokenLocal,
        hasRefreshTokenLocal: !!refreshTokenLocal,
        hasAnyToken
      });

      if (hasAnyToken) {
        console.log('AuthProvider init: Обнаружены токены, пытаемся проверить авторизацию.');
        // Если есть токены, убеждаемся, что disableAutoLogin сброшен (на случай если он был true в Zustand, но false в localStorage)
        if (disableAutoLogin) {
            setDisableAutoLogin(false);
        }
        localStorage.removeItem('disableAutoLogin'); // Убираем из localStorage, если был
        checkAuthStatus();
      } else {
        console.log('AuthProvider init: Токены не обнаружены, автоматический вход невозможен. Пользователь не авторизован.');
        // Если токенов нет и disableAutoLogin не был активен, пользователь просто не залогинен.
        // Не нужно устанавливать disableAutoLogin в true здесь, это задача logout или force_login.
        // Убедимся, что isAuthenticated в store false, если checkAuthStatus не будет вызван.
        // Это должно быть обработано в checkAuthStatus или начальном состоянии store.
      }
      setIsInitialized(true);
    }
  }, [isInitialized, checkAuthStatus, setDisableAutoLogin, disableAutoLogin]);

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