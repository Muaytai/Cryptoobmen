'use client';

import { Shield, Lock, CheckCircle, Clock } from 'lucide-react';

export function TrustIndicators() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
        Почему нам доверяют
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex items-start">
          <div className="flex-shrink-0 bg-green-100 dark:bg-green-900 p-3 rounded-full mr-4">
            <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Безопасность</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Многоуровневая защита данных и средств. SSL шифрование, защита от DDoS атак и регулярные аудиты безопасности.
            </p>
          </div>
        </div>
        
        <div className="flex items-start">
          <div className="flex-shrink-0 bg-blue-100 dark:bg-blue-900 p-3 rounded-full mr-4">
            <Lock className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Конфиденциальность</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Мы не храним ваши личные данные дольше, чем это необходимо, и никогда не передаем их третьим лицам.
            </p>
          </div>
        </div>
        
        <div className="flex items-start">
          <div className="flex-shrink-0 bg-purple-100 dark:bg-purple-900 p-3 rounded-full mr-4">
            <CheckCircle className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Надежность</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Более 10,000 успешных обменов. Средний рейтинг 4.9/5 на основе отзывов наших клиентов.
            </p>
          </div>
        </div>
        
        <div className="flex items-start">
          <div className="flex-shrink-0 bg-amber-100 dark:bg-amber-900 p-3 rounded-full mr-4">
            <Clock className="h-6 w-6 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Скорость</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Автоматические обмены 24/7. Среднее время обработки транзакции — менее 5 минут.
            </p>
          </div>
        </div>
      </div>
      
      <div className="mt-8 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap justify-center gap-4">
          <div className="flex items-center">
            <img src="/ssl-secure.svg" alt="SSL Secure" className="h-10 w-auto" />
          </div>
          <div className="flex items-center">
            <img src="/mcafee-secure.svg" alt="McAfee Secure" className="h-10 w-auto" />
          </div>
          <div className="flex items-center">
            <img src="/norton-secured.svg" alt="Norton Secured" className="h-10 w-auto" />
          </div>
        </div>
      </div>
    </div>
  );
} 