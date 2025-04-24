'use client';

import React from 'react';
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

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header className="header">
      <nav className="nav">
        <Logo />

        {/* Navigation */}
        <div className="nav-menu">
          <Link href="/about" className="nav-link">
            Меню
          </Link>
          <Link href="/features" className="nav-link">
            Меню
          </Link>
          <Link href="/pricing" className="nav-link">
            Меню
          </Link>
          <Link href="/contact" className="nav-link">
            Меню
          </Link>
        </div>

        {/* Auth Button */}
        <Link href="/login">
          <button className="button button-outline">
            Войти
          </button>
        </Link>
      </nav>
    </header>
  );
} 