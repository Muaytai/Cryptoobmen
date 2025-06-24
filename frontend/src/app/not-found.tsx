'use client';

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      <h1 className="text-4xl font-bold mb-4">404 - Страница не найдена</h1>
      <p className="mb-8 text-lg">Запрашиваемая страница не существует.</p>
      <Link href="/" className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
        Вернуться на главную
      </Link>
    </div>
  );
} 