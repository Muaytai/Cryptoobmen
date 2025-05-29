'use client';

import { useState } from 'react';
import { Shield, Lock, CheckCircle, Info } from 'lucide-react';

interface SecurityBadgeProps {
  className?: string;
  showDetails?: boolean;
}

export function SecurityBadge({ className = '', showDetails = false }: SecurityBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100 px-3 py-1.5 rounded-full hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
      >
        <Shield className="w-4 h-4" />
        <span className="text-sm font-medium">Защищено</span>
      </button>

      {(isOpen || showDetails) && (
        <div className="absolute z-50 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-200 dark:border-gray-700 right-0">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Lock className="w-5 h-5" /> 
            Безопасность и защита
          </h3>
          
          <ul className="space-y-3">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">SSL шифрование</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Все данные передаются по защищенному протоколу</p>
              </div>
            </li>
            
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">reCAPTCHA защита</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Автоматическая защита от ботов и мошенников</p>
              </div>
            </li>
            
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">2FA аутентификация</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Двухфакторная защита для всех финансовых операций</p>
              </div>
            </li>
            
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">Мониторинг транзакций</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Автоматическое обнаружение подозрительной активности</p>
              </div>
            </li>
          </ul>
          
          <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Info className="w-4 h-4" />
            <span>Ваша безопасность - наш приоритет</span>
          </div>
        </div>
      )}
    </div>
  );
} 