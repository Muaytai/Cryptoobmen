'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Link from 'next/link';

export default function PrivacyPage() {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);

  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'}`}>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8 text-center sm:text-left">
          Политика конфиденциальности платформы CTokenX
        </h1>
        
        <div className="text-sm mb-6">
          <span className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Последнее обновление: 29 апреля 2025 г.
          </span>
        </div>
        
        <div className="space-y-6">
          <p className="mb-4">
            CTokenX уважает ваше право на конфиденциальность и обязуется защищать персональную информацию пользователей. Настоящая Политика конфиденциальности объясняет, какие данные мы собираем, как мы их используем, храним и защищаем, а также ваши права на них.
          </p>
          
          {/* Раздел 1 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              1. Сбор информации
            </h2>
            <p className="mb-2">
              Мы можем собирать следующие данные при использовании вами платформы:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li><span className="font-medium">Персональная информация</span>: имя, email, номер телефона (если предоставлены);</li>
              <li><span className="font-medium">Данные для входа</span>: ID, логин и пароль, биометрические данные (если используются);</li>
              <li><span className="font-medium">Технические данные</span>: IP-адрес, тип устройства, данные о браузере, журналы посещений;</li>
              <li><span className="font-medium">Факты сессии</span>: данные о действиях на сайте для улучшения пользовательского опыта.</li>
            </ul>
          </section>
          
          {/* Раздел 2 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              2. Использование информации
            </h2>
            <p className="mb-2">
              Собранная информация используется для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>обеспечения работы и развития платформы;</li>
              <li>создания и управления аккаунтом;</li>
              <li>предоставления поддержки пользователям;</li>
              <li>аналитики и улучшения сервиса;</li>
              <li>изучения поведения пользователей и улучшения функционала;</li>
              <li>соблюдения юридических и нормативных требований.</li>
            </ul>
          </section>
          
          {/* Раздел 3 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              3. Хранение и защита данных
            </h2>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Ваша персональная информация хранится в зашифрованном виде на защищенных серверах;</li>
              <li>Мы используем современные протоколы шифрования и защитные механизмы для ограничения доступа по ролям;</li>
              <li>Доступ не предоставляется третьим лицам, за исключением случаев, предусмотренных законом или с согласия пользователя.</li>
            </ul>
          </section>
          
          {/* Раздел 4 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              4. Передача данных третьим сторонам
            </h2>
            <p className="mb-2">
              Ваши персональные и платежные данные никогда не передаются третьим лицам, за исключением:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>случаев, предусмотренных законодательством;</li>
              <li>партнёров и подрядчиков, работающих с нами на условиях конфиденциальности;</li>
              <li>случаев (например, случаи не являются исчерпывающими), не имеющих доступа к идентифицирующим данным.</li>
            </ul>
          </section>
          
          {/* Раздел 5 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              5. Cookie-файлы
            </h2>
            <p className="mb-2">
              Мы используем cookie-файлы для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>запоминания пользовательских предпочтений;</li>
              <li>отслеживания активности на сайте;</li>
              <li>анализа работы и улучшения проекта;</li>
            </ul>
            <p className="mt-2">
              Вы можете отключить cookie в настройках браузера, но это может повлиять на доступность работы сайта.
            </p>
          </section>
          
          {/* Раздел 6 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              6. Права пользователей
            </h2>
            <p className="mb-2">
              Вы имеете право:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>запрашивать доступ к своим данным;</li>
              <li>требовать их корректировки или удаления;</li>
              <li>ограничить обработку ваших данных;</li>
              <li>подать жалобу в надзорный орган по защите персональных данных.</li>
            </ul>
          </section>
          
          {/* Раздел 7 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              7. Хранение данных
            </h2>
            <p className="mb-2">
              Мы храним ваши персональные данные только на необходимый срок:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>для целей, описанных в данной политике;</li>
              <li>требуемый законодательством период;</li>
              <li>до удаления аккаунта по вашему запросу.</li>
            </ul>
          </section>
          
          {/* Раздел 8 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              8. Изменения в политике
            </h2>
            <p className="mb-2">
              Мы можем вносить изменения в Политику конфиденциальности. Обновленная версия вступает в силу с момента публикации. Пользователи будут уведомлены о существенных изменениях по email или через интерфейс системы.
            </p>
          </section>
          
          {/* Раздел 9 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              9. Контакты
            </h2>
            <p className="mb-2">
              Если у вас возникнут вопросы по поводу конфиденциальности данных, свяжитесь с нами:{' '}
              <a href="mailto:support@ctokenx.io" className={`${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-800'}`}>
                support@ctokenx.io
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
} 