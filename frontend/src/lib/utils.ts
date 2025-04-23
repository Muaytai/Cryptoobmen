import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Функция для объединения классов Tailwind CSS
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Форматирование валюты
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
  }).format(amount);
}

// Форматирование даты
export function formatDate(date: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
}

// Обрезка текста
export function truncateText(text: string, length = 50): string {
  if (text.length <= length) return text;
  return `${text.substring(0, length)}...`;
}

// Обработка ошибок API
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}

// Проверка, выполняется ли код на клиенте
export const isClient = typeof window !== 'undefined';

// Проверка, выполняется ли код на сервере
export const isServer = typeof window === 'undefined'; 