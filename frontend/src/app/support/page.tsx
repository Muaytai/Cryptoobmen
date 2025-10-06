'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Link from 'next/link';

export default function SupportPage() {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Имитация отправки формы
    setTimeout(() => {
      setSubmitted(true);
      setIsSubmitting(false);
      // Очистка формы
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: ''
      });
    }, 1500);
  };
  
  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'} min-h-screen`}>
      <div className="max-w-5xl mx-auto px-4 py-12">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          Центр <span className={`${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>поддержки</span>
        </h1>
        
        <div className="mb-12">
          <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
            <h2 className="text-xl font-semibold mb-4">Часто задаваемые вопросы</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Как долго обрабатывается заявка на обмен?</h3>
                <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Большинство заявок обрабатываются автоматически в течение 5-15 минут. В редких случаях, 
                  при необходимости дополнительной проверки, время может увеличиться до 1-2 часов.
                </p>
              </div>
              <div>
                <h3 className="font-medium mb-2">Какие комиссии берет платформа?</h3>
                <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Комиссия уже включена в курс обмена. Дополнительно взимается только комиссия сети 
                  при отправке транзакции. Вы всегда видите итоговую сумму к получению до подтверждения обмена.
                </p>
              </div>
              <div>
                <h3 className="font-medium mb-2">Что делать, если транзакция не прошла?</h3>
                <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Обратитесь в службу поддержки, указав ID транзакции и подробно описав проблему. 
                  Наши специалисты рассмотрят ваш запрос в течение 24 часов.
                </p>
              </div>
              <div>
                <Link 
                  href="/faq" 
                  className={`inline-flex items-center mt-2 font-medium ${isDarkMode ? 'text-violet-400 hover:text-violet-300' : 'text-violet-600 hover:text-violet-700'}`}
                >
                  Больше ответов в FAQ
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
        
        {submitted ? (
          <div className={`p-8 rounded-lg text-center ${isDarkMode ? 'bg-green-900/30 text-green-100' : 'bg-green-50 text-green-800'}`}>
            <svg className="w-16 h-16 mx-auto mb-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <h2 className="text-2xl font-bold mb-2">Запрос отправлен успешно!</h2>
            <p className="mb-4">Наши специалисты свяжутся с вами в ближайшее время.</p>
            <button 
              onClick={() => setSubmitted(false)}
              className={`px-4 py-2 rounded-md font-medium ${
                isDarkMode ? 'bg-violet-600 hover:bg-violet-700 text-white' : 'bg-violet-600 hover:bg-violet-700 text-white'
              }`}
            >
              Отправить еще запрос
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="col-span-1">
              <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
                <h2 className="text-xl font-semibold mb-4">Контактная информация</h2>
                <div className="space-y-4">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 mt-0.5 mr-3 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                    <div>
                      <div className="font-medium">Email:</div>
                      <a href="mailto:support@ctokenx.com" className={`${isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}>
                        support@ctokenx.com
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
                        Telegram: <a href="https://t.me/ctokenx" className="hover:underline">@ctokenx</a>
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
                        24/7 - автоматические операции<br />
                        9:00 - 21:00 МСК - служба поддержки
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-2">
              <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}>
                <h2 className="text-xl font-semibold mb-4">Написать в поддержку</h2>
                <form onSubmit={handleSubmit}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block mb-1">Ваше имя*</label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className={`w-full px-4 py-2 rounded-md ${
                          isDarkMode 
                            ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                            : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                        } border focus:ring-1 focus:ring-violet-500 focus:outline-none`}
                      />
                    </div>
                    <div>
                      <label className="block mb-1">Email*</label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        className={`w-full px-4 py-2 rounded-md ${
                          isDarkMode 
                            ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                            : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                        } border focus:ring-1 focus:ring-violet-500 focus:outline-none`}
                      />
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block mb-1">Тема обращения*</label>
                    <select
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      className={`w-full px-4 py-2 rounded-md ${
                        isDarkMode 
                          ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                          : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                      } border focus:ring-1 focus:ring-violet-500 focus:outline-none`}
                    >
                      <option value="">Выберите тему</option>
                      <option value="problem">Проблема с транзакцией</option>
                      <option value="question">Вопрос о работе сервиса</option>
                      <option value="suggestion">Предложение по улучшению</option>
                      <option value="other">Другое</option>
                    </select>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block mb-1">Сообщение*</label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      rows={5}
                      className={`w-full px-4 py-2 rounded-md ${
                        isDarkMode 
                          ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                          : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                      } border focus:ring-1 focus:ring-violet-500 focus:outline-none`}
                    ></textarea>
                  </div>
                  
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className={`w-full flex justify-center items-center px-6 py-3 rounded-md font-medium ${
                      isDarkMode ? 'bg-violet-600 hover:bg-violet-700 text-white' : 'bg-violet-600 hover:bg-violet-700 text-white'
                    } transition-colors ${isSubmitting ? 'opacity-70 cursor-not-allowed' : ''}`}
                  >
                    {isSubmitting ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Отправка...
                      </>
                    ) : (
                      'Отправить сообщение'
                    )}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 