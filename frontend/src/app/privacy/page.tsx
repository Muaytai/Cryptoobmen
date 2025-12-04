'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

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
            Последнее обновление: 09 августа 2025 г.
          </span>
        </div>

        <div className="space-y-6">
          <p className="mb-4">
            CTokenX уважает ваше право на конфиденциальность и обязуется защищать персональную информацию пользователей. 
            Настоящая Политика конфиденциальности объясняет, какие данные мы собираем, как мы их используем, храним и защищаем, 
            а также ваши права в отношении этих данных. Используя наш сервис, вы подтверждаете, что ознакомлены с этой политикой 
            и даёте согласие на обработку ваших персональных данных в соответствии с ней.
          </p>

          {/* Раздел 1 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              1. Сбор информации
            </h2>
            <p className="mb-2">
              Мы можем собирать следующие категории данных:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li><span className="font-medium">Персональные данные</span>: имя, адрес электронной почты, номер телефона (при регистрации);</li>
              <li><span className="font-medium">Данные для аутентификации</span>: логин, пароль, двухфакторная аутентификация (2FA), биометрические данные (если используются);</li>
              <li><span className="font-medium">Данные KYC/AML</span>: копии паспорта, водительских прав, подтверждение адреса (при верификации);</li>
              <li><span className="font-medium">Техническая информация</span>: IP-адрес, тип устройства, операционная система, браузер, данные о сессии;</li>
              <li><span className="font-medium">Данные транзакций</span>: история обменов, пополнений, выводов, суммы, даты, криптокошельки;</li>
              <li><span className="font-medium">Cookies и аналитика</span>: данные о поведении на сайте, предпочтениях, маркетинговой активности.</li>
            </ul>
          </section>

          {/* Раздел 2 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              2. Цели обработки данных
            </h2>
            <p className="mb-2">
              Мы используем ваши данные для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Создания, управления и защиты вашего аккаунта;</li>
              <li>Обработки транзакций (обмен, вывод, пополнение);</li>
              <li>Проведения верификации личности (KYC) и проверки на отмывание денег (AML);</li>
              <li>Предоставления технической поддержки и уведомлений;</li>
              <li>Обеспечения безопасности платформы и предотвращения мошенничества;</li>
              <li>Анализа и улучшения сервиса, пользовательского интерфейса и функционала;</li>
              <li>Соблюдения юридических, налоговых и регуляторных обязательств;</li>
              <li>Отправки информационных и маркетинговых сообщений (только при наличии согласия).</li>
            </ul>
          </section>

          {/* Раздел 3 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              3. Хранение и защита данных
            </h2>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Все персональные и финансовые данные хранятся с использованием современного шифрования (TLS, AES-256);</li>
              <li>Серверы защищены многоуровневыми системами безопасности, включая фаерволы, DDoS-защиту и мониторинг;</li>
              <li>Доступ к данным ограничен и предоставляется только уполномоченным сотрудникам и системам;</li>
              <li>Мы применяем двухфакторную аутентификацию (2FA), защиту от несанкционированного доступа и регулярные аудиты безопасности.</li>
            </ul>
          </section>

          {/* Раздел 4 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              4. Передача данных третьим сторонам
            </h2>
            <p className="mb-2">
              Мы не продаём и не передаём ваши данные третьим лицам без вашего согласия, за исключением:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Поставщиков услуг KYC/AML (например, Sumsub, Jumio) для верификации личности;</li>
              <li>Платежных и ликвидностных провайдеров, необходимых для обработки транзакций;</li>
              <li>Юридических, аудиторских и IT-консультантов, действующих на условиях конфиденциальности;</li>
              <li>Государственных органов, если этого требует закон (например, по запросу правоохранительных органов);</li>
              <li>Партнёров, участвующих в улучшении сервиса, при условии, что они не получают доступ к идентифицируемым данным.</li>
            </ul>
          </section>

          {/* Раздел 5 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              5. Cookie-файлы и трекинг
            </h2>
            <p className="mb-2">
              Мы используем cookie-файлы и аналогичные технологии для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Автоматического входа и запоминания ваших настроек;</li>
              <li>Анализа трафика и поведения пользователей;</li>
              <li>Улучшения производительности и удобства платформы;</li>
              <li>Показа персонализированной рекламы (если вы дали согласие).</li>
            </ul>
            <p className="mt-2">
              Вы можете отключить cookies через настройки браузера, но это может ограничить функциональность платформы.
            </p>
          </section>

          {/* Раздел 6 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              6. Ваши права
            </h2>
            <p className="mb-2">
              В зависимости от вашей юрисдикции (включая GDPR), вы имеете право:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Запрашивать доступ к своим персональным данным;</li>
              <li>Требовать исправления неточностей;</li>
              <li>Запрашивать удаление данных («право на забвение»);</li>
              <li>Ограничить или возразить против обработки;</li>
              <li>Получить копию ваших данных в структурированном формате (переносимость);</li>
              <li>Отозвать согласие в любое время;</li>
              <li>Подать жалобу в орган по защите персональных данных (например, в вашей стране).</li>
            </ul>
            <p className="mt-2">
              Для реализации своих прав свяжитесь с нами по адресу: <a href="mailto:support@ctokenx.io" className={`${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-800'}`}>support@ctokenx.io</a>.
            </p>
          </section>

          {/* Раздел 7 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              7. Срок хранения данных
            </h2>
            <p className="mb-2">
              Мы храним ваши данные только в течение времени, необходимого для:
            </p>
            <ul className={`list-disc pl-8 space-y-1 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              <li>Выполнения обязательств перед вами;</li>
              <li>Соблюдения юридических требований (например, AML — до 5 лет);</li>
              <li>Расследования споров или подозрительной активности;</li>
              <li>До тех пор, пока вы не запросите удаление аккаунта.</li>
            </ul>
          </section>

          {/* Раздел 8 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              8. Изменения в политике
            </h2>
            <p className="mb-2">
              Мы оставляем за собой право вносить изменения в настоящую Политику конфиденциальности. 
              Обновлённая версия будет опубликована на этой странице с новой датой. 
              При существенных изменениях мы уведомим вас по электронной почте или через интерфейс платформы.
            </p>
          </section>

          {/* Раздел 9 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              9. Контактная информация
            </h2>
            <p className="mb-2">
              Если у вас есть вопросы, претензии или запросы, связанные с обработкой персональных данных, 
              свяжитесь с нами:
            </p>
            <p>
              По электронной почте: <a href="mailto:support@ctokenx.io" className={`${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-800'}`}>
                support@ctokenx.io
              </a>
            </p>
          </section>

          {/* Раздел 10 */}
          <section>
            <h2 className={`text-xl font-semibold mb-3 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              10. Применимое право и разрешение споров
            </h2>
            <p className="mb-2">
              Настоящая Политика регулируется законодательством [укажите юрисдикцию, например: Республики Кипр, Сингапура или оффшорной зоны]. 
              Все споры, связанные с обработкой персональных данных, подлежат разрешению в соответствии с действующим законодательством. 
              Пользователи из ЕС также могут обращаться в национальные органы по защите данных.
            </p>
          </section>

          <p className={`text-sm mt-8 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            <strong>Внимание:</strong> Использование платформы CTokenX доступно только пользователям, достигшим 18 лет и соответствующим требованиям законодательства своей страны.
          </p>
        </div>
      </div>
    </div>
  );
}