'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import LogoComponent from '@/components/Logo';
import { useTheme } from '@/lib/ThemeProvider';
import styles from './Header.module.css';

// Компонент навигационной ссылки
const NavLink = ({ href, children, isDefault = false }: { href: string; children: React.ReactNode; isDefault?: boolean }) => {
  const pathname = usePathname();
  // Если это главная страница (/) или указан флаг isDefault, считаем ссылку активной
  const isActive = pathname === href || (pathname === '/' && isDefault);
  
  return (
    <Link 
      href={href} 
      className={`${styles.navLink} ${isActive ? styles.activeNavLink : ''}`}
    >
      {children}
    </Link>
  );
};

// Компонент иконки для темной темы (луна)
const MoonIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// Компонент иконки для светлой темы (солнце)
const SunIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="5" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="12" y1="1" x2="12" y2="3" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="12" y1="21" x2="12" y2="23" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="1" y1="12" x2="3" y2="12" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="21" y1="12" x2="23" y2="12" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="#9B81F8" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);
  const isLoading = useAuthStore((state) => state.isLoading);
  const setDisableAutoLogin = useAuthStore((state) => state.setDisableAutoLogin);
  const { theme, toggleTheme } = useTheme();
  const [isClientMounted, setIsClientMounted] = useState(false);

  // Отмечаем, что компонент монтирован для предотвращения проблем с гидратацией
  useEffect(() => {
    setIsClientMounted(true);
  }, []);

  // Функция для обработки нажатия на кнопку "Войти"
  const handleLogin = () => {
    // Очищаем cookie disableAutoLogin перед переходом на страницу входа
    document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    // Очищаем флаг в localStorage
    localStorage.removeItem('disableAutoLogin');
    // Обновляем состояние в store
    setDisableAutoLogin(false);
    
    // Добавляем параметр force_login для принудительного входа
    window.location.href = '/login?force_login=true';
  };

  // Функция для обработки нажатия на имя пользователя
  const handleProfileClick = (e: React.MouseEvent) => {
    e.preventDefault();
    // Проверяем наличие сессионной куки
    const hasSession = document.cookie.includes('sessionid=') || 
                        document.cookie.includes('dj_session_id=') || 
                        document.cookie.includes('auth_token=') ||
                        document.cookie.includes('csrftoken=');
    
    // Если есть сессия - сбрасываем флаг блокировки автологина
    if (hasSession) {
      document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      localStorage.removeItem('disableAutoLogin');
      setDisableAutoLogin(false);
    }
    
    // Переходим на страницу профиля
    router.push('/profile');
  };

  const handleLogout = async () => {
    // Явно устанавливаем флаг в localStorage перед разлогиниванием
    localStorage.setItem('disableAutoLogin', 'true');
    
    try {
      // Блокируем использование кнопки на время выхода
      console.log('Выход из аккаунта...');
      
      // Вызываем logout из стора
      await logout();
      
      // Дополнительная проверка и очистка куки
      document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      document.cookie = 'dj_session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      
      // Убедимся, что все состояния очищены
      localStorage.removeItem('auth-storage');
      
      console.log('Выход успешно выполнен');
      
      // Принудительно обновляем страницу, чтобы сбросить все состояния приложения
      window.location.href = '/';
    } catch (error) {
      console.error('Ошибка при выходе:', error);
      // В случае ошибки всё равно принудительно обновляем страницу
      window.location.href = '/';
    }
  };

  // Используем тему напрямую из ThemeProvider для определения отображения
  const isDarkMode = theme === 'dark';

  return (
    <header className={`${styles.header} ${!isDarkMode ? styles.light : ''}`}>
      {/* Логотип слева */}
      <div className={styles.logoContainer}>
        <LogoComponent />
      </div>
      {/* Навигация посередине */}
      <nav className={styles.navigation}>
        <NavLink href="/" isDefault>Главная</NavLink>
        <NavLink href="/about">О нас</NavLink>
        <NavLink href="/reviews">Отзывы</NavLink>
        <NavLink href="/faq">FAQ</NavLink>
      </nav>
      {/* Кнопки действий справа */}
      <div className={styles.actions}>
        <button 
          onClick={toggleTheme} 
          className={styles.themeToggle} 
          aria-label="Переключить тему"
        >
          {isDarkMode ? <MoonIcon /> : <SunIcon />}
        </button>
        {isClientMounted && !isLoading ? (
          isAuthenticated && user ? (
            <div className={styles.actions}>
              <button 
                onClick={handleProfileClick} 
                className={styles.userLink}
              >
                {user.username || user.email}
              </button>
              <button onClick={handleLogout} className={styles.logoutButton}>
                Выйти
              </button>
            </div>
          ) : (
            <button onClick={handleLogin} className={styles.loginButton}>
              Войти
            </button>
          )
        ) : isClientMounted && isLoading ? (
          <div className={styles.loadingText}>Загрузка...</div>
        ) : null}
      </div>
    </header>
  );
} 