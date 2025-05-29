'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';
import ReCaptcha from './ReCaptcha';

interface LoginFormProps {
  onSuccess?: () => void;
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [recaptchaToken, setRecaptchaToken] = useState('');
  const [attemptsLeft, setAttemptsLeft] = useState(5); // Показываем пользователю, сколько попыток осталось
  const router = useRouter();
  const { login, setTokens } = useAuthStore();

  const handleRecaptchaVerify = (token: string) => {
    setRecaptchaToken(token);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!recaptchaToken) {
      setError('Пожалуйста, дождитесь проверки reCAPTCHA');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      
      // Используем axios для первоначального входа, чтобы получить токены
      console.log('Пытаемся авторизоваться по URL:', `${process.env.NEXT_PUBLIC_API_URL}/auth/login/`);
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/auth/login/`, {
        email,
        password,
        recaptcha_token: recaptchaToken
      }, {
        withCredentials: true
      });
      
      console.log('Ответ от сервера:', response.data);
      
      if (response.data.access_token) {
        console.log('Получены токены:', response.data.access_token);
        
        // Устанавливаем токены в хранилище
        setTokens({
          access: response.data.access_token,
          refresh: response.data.refresh_token || ''
        });
        
        // Устанавливаем токены в cookies вручную
        document.cookie = `access_token=${response.data.access_token}; path=/; max-age=3600; samesite=lax;`;
        document.cookie = `refresh_token=${response.data.refresh_token || ''}; path=/; max-age=604800; samesite=lax;`;
        
        // Используем метод login из useAuthStore для аутентификации
        // Этот метод автоматически получит данные пользователя
        await login({ email, password });
        
        if (onSuccess) {
          onSuccess();
        } else {
          router.push('/dashboard');
        }
      }
    } catch (err: any) {
      console.error('Login error:', err);
      
      if (err.response) {
        // Если сервер вернул ошибку о блокировке аккаунта
        if (err.response.status === 403 && err.response.data.detail?.includes('locked')) {
          setError('Ваш аккаунт временно заблокирован из-за слишком большого количества неудачных попыток входа. Пожалуйста, попробуйте позже или воспользуйтесь функцией восстановления пароля.');
        } 
        // Если сервер вернул ошибку о неверных учетных данных
        else if (err.response.status === 400) {
          // Если сервер сообщает, сколько попыток осталось
          if (err.response.data.attempts_left !== undefined) {
            setAttemptsLeft(err.response.data.attempts_left);
          }
          
          setError(`Неверный email или пароль. Осталось попыток: ${attemptsLeft}`);
        } 
        // Другие ошибки
        else {
          setError(err.response.data.detail || 'Произошла ошибка при входе. Пожалуйста, попробуйте позже.');
        }
      } else {
        setError('Не удалось подключиться к серверу. Пожалуйста, проверьте подключение к интернету.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 shadow-md rounded-lg px-8 pt-6 pb-8 mb-4">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">Вход в аккаунт</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md">
            {error}
          </div>
        )}
        
        <div className="mb-4">
          <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="email">
            Email
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 leading-tight focus:outline-none focus:shadow-outline"
            id="email"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="password">
            Пароль
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 leading-tight focus:outline-none focus:shadow-outline"
            id="password"
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-6">
          <ReCaptcha 
            siteKey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || ''} 
            onVerify={handleRecaptchaVerify}
            action="login"
          />
        </div>
        
        <div className="flex items-center justify-between">
          <button
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            type="submit"
            disabled={loading}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
          <a
            className="inline-block align-baseline font-bold text-sm text-blue-500 hover:text-blue-800"
            href="/forgot-password"
          >
            Забыли пароль?
          </a>
        </div>
      </form>
    </div>
  );
}
