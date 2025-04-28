'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Input } from '@/components/ui/Input';
import { useAuthStore } from '@/store/useAuthStore';
import styles from './Register.module.css';
import { FaEye, FaEyeSlash, FaGoogle, FaApple } from 'react-icons/fa';

export default function RegisterForm() {
  const router = useRouter();
  const { register, isLoading, error } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [passwordError, setPasswordError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agree, setAgree] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setPasswordError('Пароли не совпадают');
      return;
    }
    if (!agree) {
      setPasswordError('Необходимо согласиться с условиями');
      return;
    }
    setPasswordError('');
    try {
      await register(formData);
      router.push('/login');
    } catch (err) {
      // обработка ошибок
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className={styles.formBox}>
        <div className={styles.title}>Регистрация</div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          <Input
            type="text"
            name="username"
            placeholder="Имя пользователя"
            value={formData.username}
            onChange={handleChange}
            required
          />
          <div className="relative">
            <Input
              type={showPassword ? 'text' : 'password'}
              name="password"
              placeholder="Пароль"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <button type="button" onClick={() => setShowPassword(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary">
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </button>
          </div>
          <Input
            type={showPassword ? 'text' : 'password'}
            name="confirmPassword"
            placeholder="Подтвердите пароль"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
          />
          <div className="flex items-center gap-2 mt-2">
            <input type="checkbox" id="agree" checked={agree} onChange={e => setAgree(e.target.checked)} className="accent-primary" />
            <label htmlFor="agree" className="text-sm text-gray-400">Я принимаю <Link href="/terms" className="underline text-primary">условия использования</Link></label>
          </div>
          {(error || passwordError) && (
            <p className="text-red-500 text-sm">{error || passwordError}</p>
          )}
          <button type="submit" className="button w-full mt-2" disabled={isLoading}>
            Зарегистрироваться
          </button>
          <div className="flex items-center my-6">
            <div className="flex-1 h-px bg-[#23233a]" />
            <span className="mx-4 text-gray-400 text-sm">или</span>
            <div className="flex-1 h-px bg-[#23233a]" />
          </div>
          <div className="flex gap-4">
            <button type="button" className="flex-1 button-outline flex items-center justify-center gap-2">
              <FaGoogle /> Google
            </button>
            <button type="button" className="flex-1 button-outline flex items-center justify-center gap-2">
              <FaApple /> Apple
            </button>
          </div>
          <div className="mt-4 text-center">
            Уже есть аккаунт?{' '}
            <Link href="/login" className={styles.link}>Войти</Link>
          </div>
        </form>
      </div>
    </div>
  );
} 