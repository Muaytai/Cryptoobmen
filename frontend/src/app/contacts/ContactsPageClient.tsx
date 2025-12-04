"use client";

import { useTheme } from "@/lib/ThemeProvider";
import Link from "next/link";

const ContactsPageClient = () => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';

  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'} min-h-screen`}>
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          Наши <span className={`${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>контакты</span>
        </h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          <div>
            <div className={`p-6 rounded-lg mb-8 ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
              <h2 className="text-xl font-semibold mb-4">О компании</h2>
              <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-4`}>
                CTokenX - это современная платформа для обмена криптовалют, основанная в 2023 году. 
                Мы работаем с физическими и юридическими лицами по всему миру, предоставляя надежный 
                и безопасный сервис для всех видов криптовалютных операций.
              </p>
              <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'} mb-4`}>
                Наша миссия - сделать обмен криптовалюты максимально простым, быстрым и безопасным для каждого.
              </p>
              <div className="flex space-x-4 mt-4">
                <a 
                  href="https://twitter.com/ctokenx" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a 
                  href="https://t.me/ctokenx" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 0C5.373 0 0 5.373 0 12c0 6.628 5.373 12 12 12s12-5.373 12-12c0-6.628-5.373-12-12-12zm5.894 8.221L16.11 18.179c-.131.599-.721.808-1.176.408l-3.232-2.658-1.562 1.503c-.173.172-.314.314-.65.314-.336 0-.294-.128-.417-.45l-.932-3.248-3.079-1.021c-.628-.203-.635-.627.147-.923l12.125-4.668c.549-.203 1.086.126.89.786z" />
                  </svg>
                </a>
                <a 
                  href="https://github.com/ctokenx" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                </a>
                <a 
                  href="https://www.linkedin.com/company/ctokenx" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" d="M19 3a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h14m-.5 15.5v-5.3a3.26 3.26 0 00-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 011.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 001.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 00-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" clipRule="evenodd" />
                  </svg>
                </a>
              </div>
            </div>
            
            <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
              <h2 className="text-xl font-semibold mb-4">Контактная информация</h2>
              <div className="space-y-4">
                <div className="flex items-start">
                  <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                  </svg>
                  <div>
                    <div className="font-medium">Email:</div>
                    <a href="mailto:info@ctokenx.com" className={`${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}>
                      info@ctokenx.com
                    </a>
                  </div>
                </div>
                <div className="flex items-start">
                  <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                  </svg>
                  <div>
                    <div className="font-medium">Телефон:</div>
                    <a href="tel:+78001234567" className={`${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}>
                      +7 (800) 123-45-67
                    </a>
                  </div>
                </div>
                <div className="flex items-start">
                  <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path>
                  </svg>
                  <div>
                    <div className="font-medium">Мессенджеры:</div>
                    <div className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      Telegram: <a href="https://t.me/ctokenx" className="hover:underline">@ctokenx</a><br />
                      WhatsApp: <a href="https://wa.me/78001234567" className="hover:underline">+7 (800) 123-45-67</a>
                    </div>
                  </div>
                </div>
                <div className="flex items-start">
                  <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <div>
                    <div className="font-medium">Время работы:</div>
                    <div className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      24/7 - операции на платформе<br />
                      9:00 - 21:00 МСК - служба поддержки<br />
                      10:00 - 19:00 МСК - офис (Пн-Пт)
                    </div>
                  </div>
                </div>
                <div className="flex items-start">
                  <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                  <div>
                    <div className="font-medium">Адрес офиса:</div>
                    <address className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'} not-italic`}>
                      Россия, г. Москва, ул. Цифровая, д. 42, офис 301<br />
                      Метро: Цифровая<br />
                      <Link 
                        href="https://yandex.ru/maps/-/CDF7RNJ5" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className={`inline-flex items-center mt-1 ${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-700'}`}
                      >
                        Открыть на карте
                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                      </Link>
                    </address>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <div className="rounded-lg overflow-hidden shadow-lg mb-8 h-[400px] relative">
              <div className={`h-full w-full flex items-center justify-center ${isDarkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
                <div className="text-center p-8">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path>
                  </svg>
                  <p>Здесь будет интерактивная карта с расположением офиса</p>
                  <p className="mt-2 text-sm">
                    (Для интеграции реальной карты требуется API ключ Яндекс или Google Maps)
                  </p>
                </div>
              </div>
            </div>
            
            <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
              <h2 className="text-xl font-semibold mb-4">Часто задаваемые вопросы</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-1">Можно ли посетить ваш офис?</h3>
                  <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Да, наш офис открыт для посетителей в рабочие дни с 10:00 до 19:00. 
                    Рекомендуем предварительно записаться на встречу через форму обратной связи.
                  </p>
                </div>
                <div>
                  <h3 className="font-medium mb-1">Как быстро отвечает служба поддержки?</h3>
                  <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Среднее время ответа составляет 15-30 минут в рабочее время. 
                    Для срочных вопросов рекомендуем использовать чат на сайте или Telegram.
                  </p>
                </div>
                <div>
                  <h3 className="font-medium mb-1">Есть ли у вас вакансии?</h3>
                  <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    Актуальные вакансии публикуются в разделе &quot;Карьера&quot; на нашем сайте. 
                    Также вы можете отправить резюме на почту hr@ctokenx.com.
                  </p>
                </div>
                <div>
                  <Link 
                    href="/support" 
                    className={`inline-flex items-center mt-2 font-medium ${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-700'}`}
                  >
                    Перейти в центр поддержки
                    <svg 
                      className="w-4 h-4 ml-1" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24" 
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="text-center mb-10">
          <h2 className="text-2xl font-semibold mb-6">Свяжитесь с нами</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link 
              href="/support" 
              className={`px-6 py-3 rounded-md font-medium inline-flex items-center ${
                isDarkMode ? 'bg-violet-600 hover:bg-violet-700 text-white' : 'bg-violet-600 hover:bg-violet-700 text-white'
              }`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
              </svg>
              Написать в поддержку
            </Link>
            <a 
              href="mailto:info@ctokenx.com" 
              className={`px-6 py-3 rounded-md font-medium inline-flex items-center ${
                isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
              }`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
              Написать на email
            </a>
            <a 
              href="tel:+78001234567" 
              className={`px-6 py-3 rounded-md font-medium inline-flex items-center ${
                isDarkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
              }`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
              </svg>
              Позвонить
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactsPageClient;



