'use client';

import React from 'react';

export function Footer() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="py-6 border-t border-gray-200 dark:border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <p suppressHydrationWarning className="text-sm text-gray-600 dark:text-gray-400">
              &copy; {currentYear} CryptoExchange. Все права защищены.
            </p>
          </div>
          <div className="flex space-x-6">
            <a 
              href="#" 
              className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
            >
              Условия использования
            </a>
            <a 
              href="#" 
              className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
            >
              Политика конфиденциальности
            </a>
            <a 
              href="#" 
              className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
            >
              Контакты
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
} 