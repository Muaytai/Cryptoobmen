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
  const handleLogin = async () => {
    try {
      // Сначала очищаем все куки
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

      // Очищаем localStorage
      localStorage.clear();
      sessionStorage.clear();

      // Очищаем состояние в store
      setDisableAutoLogin(true);
      
      // Принудительно очищаем состояние пользователя
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        disableAutoLogin: true
      });

      // Переходим на страницу логина с параметром force_login
      router.push('/login?force_login=true');
    } catch (error) {
      console.error('Ошибка при очистке данных:', error);
      router.push('/login?force_login=true');
    }
  };

  // Функция для обработки нажатия на имя пользователя
  const handleProfileClick = (e: React.MouseEvent) => {
    e.preventDefault();
    // Переходим на страницу профиля только если пользователь аутентифицирован
    if (isAuthenticated && user) {
      router.push('/profile');
    } else {
      router.push('/login');
    }
  };

  const handleLogout = async () => {
    try {
      // Блокируем использование кнопки на время выхода
      console.log('Выход из аккаунта...');
      
      // Вызываем logout из стора
      await logout();
      
      console.log('Выход успешно выполнен');
      
      // Используем роутер для навигации
      router.push('/');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
      // В случае ошибки всё равно перенаправляем на главную
      router.push('/');
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
        <NavLink href="/profile/investments">Инвестиции</NavLink>
        <NavLink href="/wallet">Кошелек</NavLink>
        <NavLink href="/funds/deposit">Пополнение</NavLink>
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