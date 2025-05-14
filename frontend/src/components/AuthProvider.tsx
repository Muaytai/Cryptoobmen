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
      // Проверяем флаг disableAutoLogin в localStorage
      const storedDisableAutoLogin = localStorage.getItem('disableAutoLogin') === 'true';
      
      // Проверяем наличие сессионной куки
      const hasSession = document.cookie.includes('sessionid=') || 
                          document.cookie.includes('dj_session_id=') ||
                          document.cookie.includes('auth_token=') ||
                          document.cookie.includes('csrftoken=');
      
      console.log('AuthProvider init: hasSession =', hasSession, 'disableAutoLogin =', storedDisableAutoLogin);
      
      // Если был установлен флаг отключения автовхода, принудительно очищаем куки
      if (storedDisableAutoLogin) {
        console.log('Флаг отключения автовхода активен, блокируем автоматический вход');
        
        // Дополнительно очищаем куки, если есть флаг disableAutoLogin
        document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'dj_session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        
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
    // Пропускаем страницы логина/регистрации и первую загрузку
    if (!['/login', '/register'].includes(pathname) && isInitialized && !disableAutoLogin) {
      // Проверяем наличие сессионной куки
      const hasSession = document.cookie.includes('sessionid=') || 
                          document.cookie.includes('dj_session_id=') ||
                          document.cookie.includes('auth_token=') ||
                          document.cookie.includes('csrftoken=');
      
      // Если есть сессионная кука, но не авторизованы в состоянии - проверяем статус
      if (hasSession && !isAuthenticated) {
        console.log('Есть сессионная кука, но не авторизованы в состоянии - проверяем статус');
        localStorage.removeItem('disableAutoLogin');
        setDisableAutoLogin(false);
        checkAuthStatus();
      }
      // Если нет сессии, но статус авторизации true - выполняем проверку
      else if (!hasSession && isAuthenticated) {
        console.log('Нет сессионной куки, но статус авторизации true - проверяем статус');
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