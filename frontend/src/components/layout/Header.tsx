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
const NavLink = ({ href, children, isDefault = false, onClick }: { href: string; children: React.ReactNode; isDefault?: boolean; onClick?: () => void }) => {
  const pathname = usePathname();
  // Если это главная страница (/) или указан флаг isDefault, считаем ссылку активной
  const isActive = pathname === href || (pathname === '/' && isDefault);
  
  return (
    <Link 
      href={href} 
      className={`${styles.navLink} ${isActive ? styles.activeNavLink : ''}`}
      onClick={onClick}
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

// Компонент иконки бургер-меню
const BurgerIcon = ({ isOpen }: { isOpen: boolean }) => (
  <svg 
    width="24" 
    height="24" 
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    className={styles.burgerIcon}
  >
    {isOpen ? (
      // Иконка крестика когда меню открыто
      <>
        <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <line x1="6" y1="18" x2="18" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      </>
    ) : (
      // Иконка бургера когда меню закрыто
      <>
        <line x1="3" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <line x1="3" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      </>
    )}
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Отмечаем, что компонент монтирован для предотвращения проблем с гидратацией
  useEffect(() => {
    setIsClientMounted(true);
  }, []);

  // Закрываем мобильное меню при изменении маршрута
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Закрываем мобильное меню при изменении размера окна
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setIsMobileMenuOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Блокируем скролл body когда мобильное меню открыто
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  // Функция для переключения мобильного меню
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Функция для закрытия мобильного меню
  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  // Функция для обработки нажатия на кнопку "Войти"
  const handleLogin = async () => {
    closeMobileMenu();
    try {
      // Сначала очищаем НЕ HttpOnly куки и localStorage
      const clientSideCookies = [
        'next_hmr_refresh_hash'
      ];

      clientSideCookies.forEach(cookie => {
        document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
        document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
        document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
      });

      // Очищаем localStorage и sessionStorage
      localStorage.removeItem('user');
      localStorage.removeItem('auth-storage');

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
    closeMobileMenu();
    // Переходим на страницу профиля только если пользователь аутентифицирован
    if (isAuthenticated && user) {
      router.push('/me');
    } else {
      router.push('/login');
    }
  };

  const handleLogout = async () => {
    closeMobileMenu();
    try {
      console.log('Выход из аккаунта...');
      await logout();
      console.log('Выход успешно выполнен');
      router.push('/');
    } catch (error) {
      console.error('Ошибка при выходе:', error);
      router.push('/');
    }
  };

  // Используем тему напрямую из ThemeProvider для определения отображения
  const isDarkMode = theme === 'dark';

  return (
    <>
      <header className={`${styles.header} ${!isDarkMode ? styles.light : ''}`}>
        {/* Логотип слева */}
        <div className={styles.logoContainer}>
          <LogoComponent />
        </div>

        {/* Кнопка бургер-меню для мобильных */}
        <button 
          className={styles.burgerButton}
          onClick={toggleMobileMenu}
          aria-label={isMobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={isMobileMenuOpen}
        >
          <BurgerIcon isOpen={isMobileMenuOpen} />
        </button>

        {/* Навигация для десктопа */}
        <nav className={styles.navigation}>
          <NavLink href="/" isDefault>Главная</NavLink>        
          <NavLink href="/wallet">Кошелек</NavLink>
          <NavLink href="/funds/deposit">Пополнение</NavLink>
          <NavLink href="/about">О нас</NavLink>
          <NavLink href="/reviews">Отзывы</NavLink>
          <NavLink href="/faq">FAQ</NavLink>
        </nav>

        {/* Кнопки действий для десктопа */}
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
              <div className={styles.userActions}>
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

      {/* Мобильное меню */}
      <div 
        className={`${styles.mobileMenuOverlay} ${isMobileMenuOpen ? styles.mobileMenuOverlayOpen : ''}`}
        onClick={closeMobileMenu}
      />
      <nav className={`${styles.mobileMenu} ${isMobileMenuOpen ? styles.mobileMenuOpen : ''} ${!isDarkMode ? styles.light : ''}`}>
        <div className={styles.mobileMenuContent}>
          {/* Навигационные ссылки */}
          <div className={styles.mobileNavLinks}>
            <NavLink href="/" isDefault onClick={closeMobileMenu}>Главная</NavLink>        
            <NavLink href="/wallet" onClick={closeMobileMenu}>Кошелек</NavLink>
            <NavLink href="/funds/deposit" onClick={closeMobileMenu}>Пополнение</NavLink>
            <NavLink href="/about" onClick={closeMobileMenu}>О нас</NavLink>
            <NavLink href="/reviews" onClick={closeMobileMenu}>Отзывы</NavLink>
            <NavLink href="/faq" onClick={closeMobileMenu}>FAQ</NavLink>
          </div>

          {/* Разделитель */}
          <div className={styles.mobileDivider} />

          {/* Действия пользователя в мобильном меню */}
          <div className={styles.mobileActions}>
            <button 
              onClick={toggleTheme} 
              className={styles.mobileThemeToggle} 
              aria-label="Переключить тему"
            >
              {isDarkMode ? (
                <>
                  <MoonIcon />
                  <span>Темная тема</span>
                </>
              ) : (
                <>
                  <SunIcon />
                  <span>Светлая тема</span>
                </>
              )}
            </button>
            
            {isClientMounted && !isLoading ? (
              isAuthenticated && user ? (
                <>
                  <button 
                    onClick={handleProfileClick} 
                    className={styles.mobileUserLink}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <span>{user.username || user.email}</span>
                  </button>
                  <button onClick={handleLogout} className={styles.mobileLogoutButton}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      <polyline points="16 17 21 12 16 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                      <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    <span>Выйти</span>
                  </button>
                </>
              ) : (
                <button onClick={handleLogin} className={styles.mobileLoginButton}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <polyline points="10 17 15 12 10 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>Войти</span>
                </button>
              )
            ) : isClientMounted && isLoading ? (
              <div className={styles.mobileLoadingText}>Загрузка...</div>
            ) : null}
          </div>
        </div>
      </nav>
    </>
  );
}
