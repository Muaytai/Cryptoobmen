import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Вход - CTokenX | Авторизация на платформе',
  description: 'Войдите в свой аккаунт CTokenX. Безопасная авторизация через email и пароль или через социальные сети (Google, Яндекс).',
};

import LoginPageClient from './LoginForm';

export default function LoginPage() {
  return <LoginPageClient />;
}
