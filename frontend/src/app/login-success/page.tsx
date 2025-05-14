'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';

export default function LoginSuccessPage() {
  const router = useRouter();
  const { checkAuthStatus, isAuthenticated, isLoading, user } = useAuthStore(
    (state) => ({
      checkAuthStatus: state.checkAuthStatus,
      isAuthenticated: state.isAuthenticated,
      isLoading: state.isLoading,
      user: state.user,
    })
  );

  useEffect(() => {
    console.log('LoginSuccessPage: Mounted');
    checkAuthStatus();
  }, [checkAuthStatus]);

  useEffect(() => {
    // Этот useEffect будет реагировать на изменения isAuthenticated и isLoading
    console.log(`LoginSuccessPage: Auth state change - isLoading: ${isLoading}, isAuthenticated: ${isAuthenticated}`);
    if (!isLoading) {
      if (isAuthenticated && user) {
        console.log('LoginSuccessPage: Authenticated, redirecting to /profile');
        router.replace('/profile'); // Перенаправляем на профиль после успешной аутентификации
      } else {
        console.log('LoginSuccessPage: Not authenticated after check, redirecting to /login');
        // Если после проверки пользователь не аутентифицирован, что-то пошло не так
        // Возможно, куки не установились или проверка не удалась
        router.replace('/login?error=social_auth_failed');
      }
    }
  }, [isAuthenticated, isLoading, user, router]);

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