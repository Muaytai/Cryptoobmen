'use client';

import React from 'react';
import Link from 'next/link';
import { FaCheckCircle } from 'react-icons/fa';
import { useSearchParams } from 'next/navigation';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error');
  
  // Всегда показываем сообщение об успешной верификации
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f0f1f]">
      <div className="max-w-md w-full bg-[#142e20] rounded-lg shadow-lg p-8 text-center">
        <div className="flex justify-center mb-6">
          <FaCheckCircle className="text-green-500 text-6xl" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-4">Вы успешно зарегистрированы!</h1>
        <div className="bg-green-600 text-white p-4 rounded-lg mb-6">
          <p className="text-lg">
            Ваш email был успешно подтвержден. Теперь вы можете войти в свой аккаунт и получить доступ ко всем функциям платформы.
          </p>
        </div>
        <Link href="/login?verified=true" className="inline-block bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-300">
          Перейти на страницу входа
        </Link>
      </div>
    </div>
  );
}
