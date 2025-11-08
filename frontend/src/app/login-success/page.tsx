'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';

export default function LoginSuccessPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const user = useAuthStore((state) => state.user);
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus);
  
  // Добавляем локальное состояние для отслеживания процесса проверки
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    console.log('LoginSuccessPage: Mounted');
    
    let isMounted = true;
    
    const checkAuth = async () => {
      if (!authChecked) {
        try {
          await checkAuthStatus();
          if (isMounted) {
            setAuthChecked(true);
          }
        } catch (error) {
          console.error('Ошибка при проверке статуса авторизации:', error);
          if (isMounted) {
            setAuthChecked(true);
          }
        }
      }
    };
    
    checkAuth();
    
    return () => {
      isMounted = false;
    };
  }, [checkAuthStatus, authChecked]);

  useEffect(() => {
    if (authChecked && !isLoading) {
      console.log(`LoginSuccessPage: Auth state change - isLoading: ${isLoading}, isAuthenticated: ${isAuthenticated}`);
      
      if (isAuthenticated && user) {
        console.log('LoginSuccessPage: Authenticated, redirecting to /profile');
        setTimeout(() => {
          router.replace('/profile');
        }, 100);
      } else {
        console.log('LoginSuccessPage: Not authenticated after check, redirecting to /login');
        setTimeout(() => {
          router.replace('/login?error=social_auth_failed');
        }, 100);
      }
    }
  }, [isAuthenticated, isLoading, user, router, authChecked]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
      <p>Завершение входа...</p>
      {/* Можно добавить простой спиннер/лоадер здесь */}
      <p style={{ marginTop: '10px', fontSize: '0.8em', color: 'gray' }}>
        (Вы будете автоматически перенаправлены)
      </p>
    </div>
  );
} 