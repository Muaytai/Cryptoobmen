"use client";

import { Shield, Lock, CheckCircle, AlertTriangle, Database, Eye, EyeOff, RefreshCw } from 'lucide-react';

export default function SecurityPageClient() {
  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-3 bg-blue-100 dark:bg-blue-900 rounded-full mb-4">
            <Shield className="h-10 w-10 text-blue-600 dark:text-blue-300" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Безопасность и защита</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Мы применяем передовые технологии для обеспечения максимальной безопасности ваших данных и средств
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center mb-4">
              <Lock className="h-8 w-8 text-blue-600 dark:text-blue-400 mr-3" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Защита данных</h2>
            </div>
            <ul className="space-y-4">
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">SSL шифрование всех данных при передаче</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Хранение паролей в хешированном виде</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Защита от SQL-инъекций и XSS атак</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">reCAPTCHA для защиты от ботов</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Блокировка после неудачных попыток входа</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Регулярные аудиты безопасности</span>
              </li>
            </ul>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center mb-4">
              <Database className="h-8 w-8 text-blue-600 dark:text-blue-400 mr-3" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Защита средств</h2>
            </div>
            <ul className="space-y-4">
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Холодное хранение большей части средств</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Мультиподпись для крупных транзакций</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Мониторинг подозрительной активности 24/7</span>
              </li>
              <li className="flex">
                <CheckCircle className="h-6 w-6 text-green-500 mr-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">Страхование средств пользователей</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 border border-gray-200 dark:border-gray-700 mb-16">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Многоуровневая защита аккаунта</h2>
          
          <div className="space-y-8">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex-shrink-0">
                <EyeOff className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Двухфакторная аутентификация (2FA)</h3>
                <p className="text-gray-700 dark:text-gray-300">
                  Защитите свой аккаунт с помощью дополнительного уровня безопасности. При входе в систему вам потребуется не только пароль, 
                  но и временный код из приложения аутентификации или SMS.
                </p>
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex-shrink-0">
                <Eye className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Подтверждение операций по email</h3>
                <p className="text-gray-700 dark:text-gray-300">
                  Все важные операции с вашим аккаунтом и средствами требуют дополнительного подтверждения через электронную почту. 
                  Это защищает вас от несанкционированного доступа.
                </p>
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex-shrink-0">
                <RefreshCw className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Автоматическая блокировка подозрительной активности</h3>
                <p className="text-gray-700 dark:text-gray-300">
                  Наша система мониторинга автоматически обнаруживает и блокирует подозрительные действия в вашем аккаунте. 
                  При обнаружении необычной активности мы немедленно уведомляем вас.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/30 rounded-lg p-6 border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start">
            <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-500 mr-3 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Будьте бдительны</h3>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Несмотря на все наши меры безопасности, всегда помните о базовых правилах защиты:
              </p>
              <ul className="list-disc pl-5 space-y-2 text-gray-700 dark:text-gray-300">
                <li>Никогда не сообщайте никому свои пароли и коды подтверждения</li>
                <li>Проверяйте URL сайта перед вводом данных (должен быть https://cryptoobmen.com)</li>
                <li>Используйте уникальные и сложные пароли</li>
                <li>Регулярно проверяйте историю входов в ваш аккаунт</li>
                <li>Немедленно сообщайте нам о любых подозрительных действиях</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

