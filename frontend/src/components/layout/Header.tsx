'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';
import { Logo } from '@/components/Logo';

// Компонент навигационной ссылки
const NavLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <Link 
    href={href} 
    className="text-gray-600 hover:text-blue-600 transition-colors dark:text-gray-300 dark:hover:text-white"
  >
    {children}
  </Link>
);

export function Header() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [dark, setDark] = useState(true);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const handleThemeToggle = () => {
    setDark((prev) => !prev);
    // Здесь можно добавить реальный переключатель темы
  };

  return (
    <header className="header" style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '24px 0'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 32}}>
        <Logo />
        <nav style={{display: 'flex', gap: 24}}>
          <Link href="/" className="nav-link">Главная</Link>
          <Link href="/about" className="nav-link">О нас</Link>
          <Link href="/reviews" className="nav-link">Отзывы</Link>
          <Link href="/faq" className="nav-link">FAQ</Link>
        </nav>
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
        <button onClick={handleThemeToggle} style={{background: 'none', border: 'none', fontSize: 22, cursor: 'pointer'}} title="Переключить тему">
          {dark ? '🌙' : '☀️'}
        </button>
        <Link href="/login">
          <button className="button button-outline">Войти</button>
        </Link>
      </div>
    </header>
  );
} 