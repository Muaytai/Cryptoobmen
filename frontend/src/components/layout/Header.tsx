'use client';

import React, { useEffect } from 'react';
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
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useTheme();

  // Эффект для применения класса темы к документу
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        document.body.style.backgroundColor = '#0A0A0A';
        document.body.style.color = 'white';
      } else {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
        document.body.style.backgroundColor = 'white';
        document.body.style.color = '#111827';
      }
    }
  }, [theme]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <LogoComponent />
      </div>
      
      <nav className={styles.nav}>
        <NavLink href="/" isDefault={true}>Главная</NavLink>
        <NavLink href="/about">О нас</NavLink>
        <NavLink href="/reviews">Отзывы</NavLink>
        <NavLink href="/faq">FAQ</NavLink>
      </nav>
      
      <div className={styles.actions}>
        <button 
          onClick={toggleTheme} 
          className={styles.themeToggle}
          aria-label="Переключить тему"
        >
          {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
        </button>
        <Link href="/login">
          <button className={styles.loginButton}>Войти</button>
        </Link>
      </div>
    </header>
  );
} 