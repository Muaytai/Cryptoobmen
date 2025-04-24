'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/useAuthStore';
import { Input } from '@/components/ui/Input';
import { authConfig } from '@/config/auth';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error } = useAuthStore();
  
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(credentials);
      router.push('/dashboard');
    } catch (err) {
      console.error('Ошибка входа:', err);
    }
  };

  const handleGoogleLogin = () => {
    const { clientId, redirectUri } = authConfig.google;
    const scope = 'email profile';
    const responseType = 'code';
    
    const url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=${responseType}&scope=${scope}`;
    window.location.href = url;
  };

  const handleYandexLogin = () => {
    const { clientId, redirectUri } = authConfig.yandex;
    const scope = 'login:email login:info';
    const responseType = 'code';
    
    const url = `https://oauth.yandex.ru/authorize?response_type=${responseType}&client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    window.location.href = url;
  };

  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
    background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(30, 27, 75, 0.1) 100%)',
  };

  const formContainerStyle = {
    width: '100%',
    maxWidth: '400px',
    padding: '40px',
    borderRadius: '16px',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  };

  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '32px',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: 600,
    color: '#fff',
    textAlign: 'center' as const,
    marginBottom: '8px',
  };

  const subtitleStyle = {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center' as const,
    marginBottom: '32px',
  };

  const socialButtonsStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
    marginTop: '24px',
  };

  const socialButtonStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '40px',
    padding: '0 16px',
    borderRadius: '8px',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    color: '#fff',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  };

  return (
    <div style={containerStyle}>
      <div style={formContainerStyle}>
        <div style={logoStyle}>
          <img src="/logo.svg" alt="Logo" width={40} height={40} />
        </div>

        <h1 style={titleStyle}>Войти</h1>
        <p style={subtitleStyle}>
          Нет аккаунта?{' '}
          <Link href="/register" style={{ color: '#8B5CF6' }}>
            Зарегистрироваться
          </Link>
        </p>

        <form onSubmit={handleSubmit}>
          <Input
            type="text"
            placeholder="Email или телефон"
            value={credentials.username}
            onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            required
          />

          <Input
            type="password"
            placeholder="Пароль"
            value={credentials.password}
            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            required
          />

          <div style={{ textAlign: 'right', marginBottom: '24px' }}>
            <Link href="/forgot-password" style={{ color: '#8B5CF6', fontSize: '14px' }}>
              Забыли пароль?
            </Link>
          </div>

          {error && (
            <div style={{ 
              padding: '12px', 
              borderRadius: '8px', 
              backgroundColor: 'rgba(239, 68, 68, 0.1)', 
              color: '#ef4444',
              marginBottom: '16px',
              fontSize: '14px',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            style={{
              width: '100%',
              height: '40px',
              backgroundColor: '#8B5CF6',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'background-color 0.2s ease',
              marginBottom: '24px',
            }}
            disabled={isLoading}
          >
            {isLoading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div style={{ position: 'relative', marginBottom: '24px' }}>
          <div style={{ 
            position: 'absolute', 
            top: '50%', 
            left: 0, 
            right: 0, 
            height: '1px', 
            backgroundColor: 'rgba(255, 255, 255, 0.1)' 
          }} />
          <div style={{ 
            position: 'relative', 
            textAlign: 'center' 
          }}>
            <span style={{ 
              backgroundColor: 'var(--background)', 
              padding: '0 12px',
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: '14px',
            }}>
              или
            </span>
          </div>
        </div>

        <div style={socialButtonsStyle}>
          <button 
            type="button" 
            style={socialButtonStyle}
            onClick={handleGoogleLogin}
          >
            Google
          </button>
          <button 
            type="button" 
            style={socialButtonStyle}
            onClick={handleYandexLogin}
          >
            Yandex
          </button>
        </div>
      </div>
    </div>
  );
} 