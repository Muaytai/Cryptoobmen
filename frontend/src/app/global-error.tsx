'use client';

import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap"
});

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <div className="flex flex-col items-center justify-center min-h-screen text-center">
        <h1 className="text-4xl font-bold mb-4">Что-то пошло не так!</h1>
        <p className="mb-8 text-lg">Произошла глобальная ошибка при загрузке приложения.</p>
        <button
          onClick={reset}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Попробовать снова
        </button>
      </div>
    </div>
  );
} 