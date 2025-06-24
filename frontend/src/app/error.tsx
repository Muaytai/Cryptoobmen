'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      <h1 className="text-4xl font-bold mb-4">Что-то пошло не так!</h1>
      <p className="mb-8 text-lg">Произошла ошибка при загрузке страницы.</p>
      <div className="flex gap-4">
        <button
          onClick={reset}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Попробовать снова
        </button>
        <Link href="/" className="px-6 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
          Вернуться на главную
        </Link>
      </div>
    </div>
  );
} 