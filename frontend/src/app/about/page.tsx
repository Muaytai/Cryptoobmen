'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Image from 'next/image';
import Link from 'next/link';

export default function AboutPage() {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark'; // Используем тему напрямую из ThemeProvider

  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'}`}>
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          О <span className={`${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>CTokenX</span>
        </h1>
        
        {/* История компании */}
        <section className="mb-16">
          <h2 className={`text-2xl font-semibold mb-6 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
            Наша история
          </h2>
          <div className="flex flex-col md:flex-row gap-8 items-center">
            <div className="md:w-1/2">
              <p className="mb-4">
                CTokenX была основана в 2021 году группой энтузиастов криптовалюты и блокчейн-технологий. 
                Мы поставили перед собой цель создать надежную и удобную платформу для обмена криптовалют, 
                которая будет доступна каждому, от опытных трейдеров до новичков в мире цифровых активов.
              </p>
              <p className="mb-4">
                С момента запуска нашей платформы мы постоянно развиваемся, совершенствуем наши услуги и 
                расширяем возможности для наших пользователей. Мы гордимся тем, что за короткий срок 
                смогли завоевать доверие тысяч клиентов по всему миру.
              </p>
            </div>
            <div className="md:w-1/2 relative h-64 w-full md:h-80">
              <div className={`absolute inset-0 rounded-lg ${isDarkMode ? 'bg-violet-900/20' : 'bg-violet-100'} flex items-center justify-center`}>
              <Image
                  src="/images/logo.png"
                  alt="CTokenX Logo"
                  width={300}
                  height={300}
                  className="object-contain"
                />
              </div>
            </div>
          </div>
        </section>
        
        {/* Миссия и ценности */}
        <section className="mb-16">
          <h2 className={`text-2xl font-semibold mb-6 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
            Миссия и ценности
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className="text-xl font-semibold mb-3">Наша миссия</h3>
              <p>
                Сделать криптовалюты доступными каждому, предоставляя безопасные и удобные 
                инструменты для обмена, хранения и использования цифровых активов.
              </p>
            </div>
            <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className="text-xl font-semibold mb-3">Наше видение</h3>
              <p>
                Стать ведущей платформой для обмена криптовалют, которая устанавливает 
                новые стандарты в области безопасности, прозрачности и удобства использования.
              </p>
            </div>
            <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <h3 className="text-xl font-semibold mb-3">Наши ценности</h3>
              <ul className="list-disc pl-5 space-y-1">
                <li>Безопасность пользователей</li>
                <li>Прозрачность операций</li>
                <li>Инновации и развитие</li>
                <li>Клиентоориентированность</li>
              </ul>
            </div>
          </div>
        </section>
        
        {/* Преимущества */}
        <section className="mb-16">
          <h2 className={`text-2xl font-semibold mb-6 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
            Почему выбирают нас
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex gap-4">
              <div className={`mt-1 flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full ${isDarkMode ? 'bg-violet-900/30 text-violet-400' : 'bg-violet-100 text-violet-600'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Безопасность</h3>
                <p>
                  Мы используем передовые технологии шифрования и многоуровневую защиту 
                  для обеспечения безопасности ваших средств и личных данных.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className={`mt-1 flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full ${isDarkMode ? 'bg-violet-900/30 text-violet-400' : 'bg-violet-100 text-violet-600'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Скорость</h3>
                <p>
                  Благодаря оптимизированной системе обмена, большинство операций выполняются 
                  в течение нескольких минут.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className={`mt-1 flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full ${isDarkMode ? 'bg-violet-900/30 text-violet-400' : 'bg-violet-100 text-violet-600'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Выгодные курсы</h3>
                <p>
                  Мы предлагаем конкурентные курсы обмена и минимальные комиссии для всех 
                  поддерживаемых криптовалют.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className={`mt-1 flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full ${isDarkMode ? 'bg-violet-900/30 text-violet-400' : 'bg-violet-100 text-violet-600'}`}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Поддержка 24/7</h3>
                <p>
                  Наша команда поддержки работает круглосуточно, чтобы помочь вам решить 
                  любые вопросы, связанные с использованием платформы.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Команда */}
        <section className="mb-16">
          <h2 className={`text-2xl font-semibold mb-6 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
            Наша команда
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className={`p-6 rounded-lg text-center ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-300 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-12 w-12 ${isDarkMode ? 'text-gray-600' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold">Алексей Иванов</h3>
              <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'} mb-2`}>Генеральный директор</p>
              <p className="text-sm">
                Опытный предприниматель с более чем 10-летним опытом в финансовой сфере и технологиях блокчейн.
              </p>
            </div>
            <div className={`p-6 rounded-lg text-center ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-300 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-12 w-12 ${isDarkMode ? 'text-gray-600' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold">Мария Петрова</h3>
              <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'} mb-2`}>CTO</p>
              <p className="text-sm">
                Опытный разработчик с глубокими знаниями в области блокчейн-технологий и криптографии.
              </p>
            </div>
            <div className={`p-6 rounded-lg text-center ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-300 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className={`h-12 w-12 ${isDarkMode ? 'text-gray-600' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold">Дмитрий Сидоров</h3>
              <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-500'} mb-2`}>Директор по безопасности</p>
              <p className="text-sm">
                Эксперт в области кибербезопасности с опытом работы в ведущих технологических компаниях.
              </p>
            </div>
          </div>
        </section>
        
        {/* Призыв к действию */}
        <section>
          <div className={`p-8 rounded-lg text-center ${isDarkMode ? 'bg-violet-900/20' : 'bg-violet-50'}`}>
            <h2 className={`text-2xl font-semibold mb-4 ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
              Присоединяйтесь к нам сегодня!
            </h2>
            <p className="mb-6 max-w-2xl mx-auto">
              Откройте для себя новые возможности в мире криптовалют с CTokenX. 
              Мы стремимся сделать обмен криптовалют максимально простым, безопасным и выгодным для вас.
            </p>
            <Link href="/login" className={`inline-block px-6 py-3 rounded-lg font-medium ${
              isDarkMode 
                ? 'bg-violet-600 hover:bg-violet-700 text-white' 
                : 'bg-violet-600 hover:bg-violet-700 text-white'
            }`}>
              Начать работу
            </Link>
          </div>
        </section>
      </div>
    </div>
  );

} 