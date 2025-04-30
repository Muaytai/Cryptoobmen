'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Link from 'next/link';

export default function AMLPage() {
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
          Политика AML платформы CTokenX
        </h1>
        
        <div className="text-sm mb-6">
          <span className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Последнее обновление: 29 апреля 2025 г.
          </span>
        </div>
        
        <div className="space-y-6">
          <p className="mb-4">
            CTokenX придерживается строгих стандартов AML (Anti-Money Laundering) и KYC (Know Your Customer) для предотвращения использования нашей платформы в незаконных целях. Настоящая политика устанавливает принципы и процедуры, которым мы следуем для соблюдения международного и национального законодательства.
          </p>
          
          {/* Раздел 1 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              1. Основные принципы
            </h2>
            <p className="mb-2">
              Наша политика AML основана на следующих принципах:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Проверка личности всех пользователей платформы;</li>
              <li>Мониторинг транзакций на предмет подозрительной активности;</li>
              <li>Соответствие требованиям законодательства в области противодействия отмыванию денег;</li>
              <li>Хранение и защита данных в соответствии с международными стандартами безопасности;</li>
              <li>Обучение сотрудников для своевременного выявления подозрительных операций.</li>
            </ul>
          </section>
          
          {/* Раздел 2 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              2. Процедуры KYC
            </h2>
            <p className="mb-2">
              Для соблюдения требований KYC, мы проводим следующие процедуры:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li><span className="font-medium">Базовая верификация</span>: Имя, фамилия, дата рождения, адрес электронной почты;</li>
              <li><span className="font-medium">Расширенная верификация</span>: Документы, удостоверяющие личность (паспорт, водительское удостоверение), фотография с документом;</li>
              <li><span className="font-medium">Проверка адреса</span>: Подтверждение места жительства через счета за коммунальные услуги или банковские выписки;</li>
              <li><span className="font-medium">Непрерывная верификация</span>: Обновление информации не реже одного раза в год или при изменении обстоятельств.</li>
            </ul>
          </section>
          
          {/* Раздел 3 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              3. Мониторинг транзакций
            </h2>
            <p className="mb-2">
              Мы осуществляем постоянный мониторинг транзакций для выявления подозрительной активности:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Автоматическая система обнаружения необычных или крупных операций;</li>
              <li>Проверка транзакций на соответствие установленным лимитам;</li>
              <li>Отслеживание операций со странами высокого риска;</li>
              <li>Анализ схем транзакций для выявления потенциального структурирования операций.</li>
            </ul>
          </section>
          
          {/* Раздел 4 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              4. Оценка рисков
            </h2>
            <p className="mb-2">
              Мы применяем риск-ориентированный подход к оценке клиентов и транзакций:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li><span className="font-medium">Низкий риск</span>: Базовая верификация, стандартные лимиты операций;</li>
              <li><span className="font-medium">Средний риск</span>: Расширенная верификация, усиленный мониторинг операций;</li>
              <li><span className="font-medium">Высокий риск</span>: Полная комплексная проверка, строгие ограничения по операциям, регулярный пересмотр профиля.</li>
            </ul>
          </section>
          
          {/* Раздел 5 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              5. Обязательства по уведомлению
            </h2>
            <p className="mb-2">
              В случае выявления подозрительных транзакций:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Мы обязуемся уведомлять соответствующие регулирующие органы в соответствии с требованиями законодательства;</li>
              <li>Сохраняем всю информацию о подозрительных транзакциях для внутреннего учета и предоставления по запросу уполномоченных органов;</li>
              <li>Сотрудничаем с правоохранительными органами при проведении расследований.</li>
            </ul>
          </section>
          
          {/* Раздел 6 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              6. Обучение персонала
            </h2>
            <p className="mb-2">
              Для эффективного выполнения AML политики:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Все сотрудники проходят регулярное обучение по вопросам AML/KYC;</li>
              <li>Проводятся тренинги для повышения осведомленности о новых методах отмывания денег и финансирования терроризма;</li>
              <li>Сотрудники обучаются выявлению и правильному реагированию на подозрительную активность.</li>
            </ul>
          </section>
          
          {/* Раздел 7 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              7. Отказ в обслуживании
            </h2>
            <p className="mb-2">
              CTokenX оставляет за собой право:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Отказать в регистрации или проведении транзакций пользователям, не прошедшим процедуры KYC;</li>
              <li>Приостановить или закрыть аккаунты, связанные с подозрительной деятельностью;</li>
              <li>Блокировать операции, которые могут быть связаны с незаконной деятельностью.</li>
            </ul>
          </section>
          
          {/* Раздел 8 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              8. Изменения в политике
            </h2>
            <p className="mb-2">
              Мы можем периодически обновлять нашу Политику AML для соответствия изменяющимся требованиям законодательства и стандартам индустрии. Актуальная версия всегда доступна на нашем сайте. Продолжение использования платформы после внесения изменений означает автоматическое согласие с обновленными условиями.
            </p>
          </section>
          
          {/* Раздел 9 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              9. Контакты
            </h2>
            <p className="mb-2">
              Если у вас есть вопросы относительно нашей Политики AML или процедур соответствия, пожалуйста, свяжитесь с нами по адресу:{' '}
              <a href="mailto:compliance@ctokenx.io" className={`${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-800'}`}>
                compliance@ctokenx.io
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
} 