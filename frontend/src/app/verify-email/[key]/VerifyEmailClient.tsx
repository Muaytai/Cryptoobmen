'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface Props {
  emailKey: string;
}

export default function VerifyEmailClient({ emailKey }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Подтверждаем ваш email...');

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        const response = await fetch(`/api/auth/registration/account-confirm-email/${emailKey}/`, {
          headers: {
            'Accept': 'application/json',
          },
          redirect: 'manual',
        });

        // Проверяем все возможные успешные статусы
        if ([200, 302].includes(response.status)) {
          setStatus('success');
          setMessage('Email успешно подтвержден!');
          
          // Редирект на страницу входа через 2 секунды
          setTimeout(() => {
            router.push('/login/?force_login=true');
          }, 2000);
        } else {
          throw new Error('Ошибка при подтверждении');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Произошла ошибка при подтверждении email.');
        console.error('Ошибка:', error);
      }
    };

    if (emailKey) {
      verifyEmail();
    }
  }, [emailKey, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100">
      <div className={`text-center p-8 rounded-lg shadow-lg max-w-md w-full mx-4 ${
        status === 'success' ? 'bg-green-500 text-white' :
        status === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
      }`}>
        <h1 className="text-3xl font-bold mb-6">Подтверждение Email</h1>
        <div className="text-xl">{message}</div>
      </div>
    </div>
  );
} 