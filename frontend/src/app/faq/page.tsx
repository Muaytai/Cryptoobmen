'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';

interface FAQItem {
  question: string;
  answer: string;
}

export default function FAQPage() {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);

  // Массив вопросов и ответов из дизайна Figma
  const faqItems: FAQItem[] = [
    {
      question: "Что такое CTokenX?",
      answer: "CTokenX — это платформа, на которой вы можете зарабатывать токены, участвовать в реферальной программе, получать бонусы и управлять цифровыми активами через удобный личный кабинет."
    },
    {
      question: "Как зарегистрироваться на платформе СTokenX?",
      answer: "Чтобы зарегистрироваться, нажмите кнопку «Войти» на главной странице. В появившемся окне выберите вкладку «Регистрация», затем укажите свой почтовый адрес или телефон, придумайте пароль – либо воспользуйтесь входом через Google или Apple. После этого вы получите доступ к полному функционалу платформы."
    },
    {
      question: "В чём разница между личными и партнёрскими счётами?",
      answer: "• Личный счёт – ваш стандартный счёт для проведения операций с токенами.\n• Партнерский счёт – счёт, на который начисляется бонус с реферальной программы (при привлечении пользователей и проценты от их активности)."
    },
    {
      question: "Как пополнить счёт?",
      answer: "Зайдите в личный кабинет, нажмите «Пополнить» рядом с нужным счётом. В появившемся окне отобразится адрес криптокошелька и QR-код для перевода. Используйте его для пополнения."
    },
    {
      question: "Как вывести средства?",
      answer: "Зайдите в личный кабинет, нажмите «Вывести» напротив нужного счёта. В появившемся окне укажите адрес криптокошелька, сумму и подтвердите операцию."
    },
    {
      question: "Есть ли комиссия на вывод средств?",
      answer: "Да, на платформе CTokenX действует комиссия сервиса на вывод средств. Размер комиссии составляет 1% от суммы вывода."
    },
    {
      question: "Как проверить статус операции?",
      answer: "В настройках профиля отображаются все транзакции: пополнения, выводы, бонусы и т.п. Там указан текущий статус каждой операции."
    },
    {
      question: "Как работает реферальная программа?",
      answer: "Вы получаете бонус за каждого приглашённого друга и процент с его комиссий. В личном кабинете вы найдёте реферальную ссылку, а также всю статистику по рефералам."
    },
    {
      question: "Насколько безопасна платформа CTokenX?",
      answer: "Мы используем современные данные, двухфакторную аутентификацию и современные методы защиты аккаунтов. Рекомендуем активировать все доступные средства безопасности в настройках профиля."
    },
    {
      question: "Как связаться с поддержкой?",
      answer: "Вы можете написать в поддержку через форму обратной связи, указанную на сайте или по email: support@ctokenx.io"
    }
  ];

  const toggleQuestion = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'} min-h-screen`}>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-10 text-center">
          Часто задаваемые вопросы (FAQ)
        </h1>
        
        <div className="mt-8 space-y-3">
          {faqItems.map((item, index) => (
            <div 
              key={index} 
              className={`overflow-hidden border border-transparent rounded-lg ${
                isDarkMode 
                  ? 'bg-[#1A1A1A] hover:bg-[#222222]' 
                  : 'bg-gray-50 hover:bg-gray-100'
              } transition-all duration-200`}
            >
              <button
                onClick={() => toggleQuestion(index)}
                className={`flex justify-between items-center w-full p-5 text-left ${
                  openIndex === index 
                    ? (isDarkMode ? 'text-[#b48afd]' : 'text-[#7C3AED]') 
                    : ''
                }`}
                aria-expanded={openIndex === index}
              >
                <span className="font-medium">{item.question}</span>
                <span className="ml-6 flex-shrink-0 text-xl">
                  {openIndex === index ? <FiChevronUp /> : <FiChevronDown />}
                </span>
              </button>
              
              {openIndex === index && (
                <div className={`px-5 pb-5 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  <p className="whitespace-pre-line">{item.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 