"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from '@/lib/ThemeProvider';

export default function TermsPageClient() {
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
          Условия использования платформы СTоkеnX
        </h1>
        
        <div className="text-sm mb-4">
          <span className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Последнее обновление: 31 апреля 2023 г.
          </span>
        </div>
        
        <div className="space-y-8">
          {/* Раздел 1 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              1. Общие положения
            </h2>
            <p className="mb-2">
              Платформа СTоkеnX — специализированную для управления криптоактивами. Настоящие условия использования (далее – «Условия») регулируют отношения между нами (далее – «Пользователь») и администрацией СTоkеnX (далее – «Платформа», «мы», «нас»). Используя СTоkеnX, вы соглашаетесь с этими условиями и принимаете все связанные с этим риски, ответственность и юридические последствия.
            </p>
          </section>
          
          {/* Раздел 2 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              2. Регистрация и безопасность аккаунта
            </h2>
            <p className="mb-2">
              Для доступа к платформе необходимо создать личный аккаунт:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Вы должны предоставить точную и актуальную информацию;</li>
              <li>Вы несете полную ответственность за сохранность ваших данных авторизации (логин, пароль, коды двухфакторной аутентификации);</li>
              <li>При действиях, отличных от использования вашего аккаунта, сообщайте об этом в службу поддержки максимально оперативно;</li>
              <li>Мы оставляем за собой право ограничить доступ к аккаунту при подозрении на несанкционированный доступ.</li>
            </ul>
          </section>
          
          {/* Раздел 3 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              3. Описание сервиса
            </h2>
            <p className="mb-2">
              Платформа СTоkеnX предоставляет следующие возможности:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>создание и управление криптокошельками;</li>
              <li>обмен одной криптовалюты на другую;</li>
              <li>участие в инвестиционных программах;</li>
              <li>реферальная система привлечения вознаграждений;</li>
              <li>расширенные настройки безопасности аккаунта.</li>
            </ul>
            <p className="my-2">
              Мы стремимся обеспечивать бесперебойную работу сервиса и гарантируем его безопасность в случае нормальных условий, но признаем возможность форс-мажора.
            </p>
          </section>
          
          {/* Раздел 4 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              4. Финансовые операции и комиссии
            </h2>
            <p className="mb-2">
              Все операции на платформе осуществляются добровольно и по инициативе Пользователя.
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Комиссии и лимиты на операции (в том числе на вывод средств) отображаются в интерфейсе Платформы и могут быть изменены без предварительного уведомления;</li>
              <li>Платформа не несет ответственности за убытки, понесенные в результате торговли, курсовых колебаний или рыночных событий, например, при падении криптовалют или при выводе средств.</li>
            </ul>
          </section>
          
          {/* Раздел 5 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              5. Риски
            </h2>
            <p className="mb-2">
              Работа с криптовалютами сопряжена с высокой волатильностью, отсутствием централизованного регулирования и возможными внезапными обвалами капитала:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Инвестируйте только средства, которые готовы потерять;</li>
              <li>Проводите собственное исследование перед инвестиционными решениями.</li>
            </ul>
          </section>
          
          {/* Раздел 6 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              6. Ограничения и запреты
            </h2>
            <p className="mb-2">
              Запрещается использовать СTоkеnX для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>нарушения законов вашей страны;</li>
              <li>финансирования терроризма;</li>
              <li>отмывания денежных средств;</li>
              <li>обхода санкций;</li>
              <li>осуществления мошеннических действий;</li>
              <li>блокирования операций других пользователей и генерации средств без предварительного уведомления.</li>
            </ul>
          </section>
          
          {/* Раздел 7 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              7. Реферальная программа
            </h2>
            <p className="mb-2">
              Пользователь может участвовать в реферальной программе, получая вознаграждения за привлеченных участников согласно дистрибуции условиям. Платформа оставляет за собой право менять правила и условия начисления бонусов.
            </p>
          </section>
          
          {/* Раздел 8 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              8. Конфиденциальность и защита данных
            </h2>
            <p className="mb-2">
              Мы обрабатываем ваши данные в соответствии с ПОЛИТИКОЙ КОНФИДЕНЦИАЛЬНОСТИ:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Мы не передаем вашу информацию третьим лицам без законных оснований или вашего согласия;</li>
              <li>Система использует надежные меры для защиты данных, однако не может гарантировать абсолютную безопасность передачи информации через интернет.</li>
            </ul>
          </section>
          
          {/* Раздел 9 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              9. Изменения в условиях
            </h2>
            <p className="mb-2">
              Платформа оставляет за собой право вносить изменения в настоящие Условия. Актуальная версия всегда доступна на сайте. Продолжение использования платформы после внесения изменений означает автоматическое согласие с обновленными терминами.
            </p>
          </section>
          
          {/* Раздел 10 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              10. Контакты
            </h2>
            <p className="mb-2">
              По вопросам, связанным с условиями использования, вы можете обратиться в службу поддержки по адресу: 
              <a href="mailto:support@ctokenx.io" className={`${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-800'} ml-1`}>
                support@ctokenx.io
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}

