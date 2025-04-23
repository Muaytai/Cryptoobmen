'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { Button } from '@/components/ui/Button';

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

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header className="border-b border-gray-200 dark:border-gray-800">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        {/* Логотип */}
        <Link href="/" className="text-2xl font-bold text-blue-600 dark:text-white">
          CryptoExchange
        </Link>

        {/* Навигация */}
        <nav className="hidden md:flex space-x-8">
          <NavLink href="/">Главная</NavLink>
          <NavLink href="/exchange">Обмен</NavLink>
          <NavLink href="/about">О нас</NavLink>
          {user && <NavLink href="/dashboard">Личный кабинет</NavLink>}
        </nav>

        {/* Кнопки авторизации */}
        <div className="flex items-center space-x-4">
          {/* Темная тема (позже добавим функционал) */}
          <button 
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Переключить тему"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"
              />
            </svg>
          </button>

          {user ? (
            <div className="flex items-center space-x-4">
              <span className="hidden md:inline text-sm">
                Привет, {user.username}
              </span>
              <Button 
                variant="ghost" 
                onClick={handleLogout}
              >
                Выйти
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Button 
                variant="ghost" 
                onClick={() => router.push('/login')}
              >
                Войти
              </Button>
              <Button 
                variant="default" 
                onClick={() => router.push('/register')}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Регистрация
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
} 