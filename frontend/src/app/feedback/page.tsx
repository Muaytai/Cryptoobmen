'use client';

import { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// Типы для формы и ошибок
interface FormData {
  name: string;
  email: string;
  rating: number;
  text: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  text?: string;
  submit?: string;
}

export default function FeedbackPage() {
  const router = useRouter();
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Состояние формы
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    rating: 5,
    text: ''
  });
  
  // Состояние ошибок и отправки
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);

  // Обработка изменений в полях формы
  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Очищаем ошибку при изменении поля
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  // Установка рейтинга
  const handleRatingChange = (rating: number) => {
    setFormData(prev => ({
      ...prev,
      rating
    }));
  };

  // Валидация формы
  const validateForm = () => {
    const newErrors: FormErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Пожалуйста, введите ваше имя';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Пожалуйста, введите ваш email';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Пожалуйста, введите корректный email';
    }
    
    if (!formData.text.trim()) {
      newErrors.text = 'Пожалуйста, напишите ваш отзыв';
    } else if (formData.text.length < 10) {
      newErrors.text = 'Отзыв должен содержать не менее 10 символов';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Отправка формы
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Отправляем данные на DRF бэкенд
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/reviews/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Если у вас есть аутентификация, здесь нужно добавить токен
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          rating: formData.rating,
          text: formData.text,
          // Дополнительные поля, которые могут потребоваться для вашего API
          client_ip: '', // Обычно определяется на сервере
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        // Обработка ошибок валидации с Django Rest Framework
        if (response.status === 400 && result.errors) {
          const validationErrors: FormErrors = {};
          
          // Преобразуем ошибки из формата DRF в наш формат
          Object.entries(result.errors).forEach(([field, messages]) => {
            if (Array.isArray(messages) && messages.length > 0) {
              validationErrors[field as keyof FormErrors] = messages[0] as string;
            }
          });
          
          setErrors(validationErrors);
          throw new Error('Пожалуйста, исправьте ошибки в форме');
        }
        
        throw new Error(result.detail || result.message || 'Что-то пошло не так');
      }
      
      setSubmitSuccess(true);
      
      // Перенаправляем пользователя на страницу отзывов через 2 секунды
      setTimeout(() => {
        router.push('/reviews');
      }, 2000);
      
    } catch (error: any) {
      console.error('Ошибка при отправке отзыва:', error);
      
      // Если ошибка не связана с валидацией (уже обработана выше)
      if (!errors.name && !errors.email && !errors.text) {
        setErrors(prev => ({
          ...prev,
          submit: error.message || 'Произошла ошибка при отправке отзыва. Пожалуйста, попробуйте позже.'
        }));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Генерация звезд для рейтинга
  const renderRatingStars = () => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <button
          key={i}
          type="button"
          onClick={() => handleRatingChange(i)}
          className="focus:outline-none"
          aria-label={`Оценка ${i} из 5`}
          title={`Оценка ${i} из 5`}
        >
          <svg
            className={`w-8 h-8 ${
              i <= formData.rating 
                ? isDarkMode ? 'text-yellow-400' : 'text-yellow-500' 
                : isDarkMode ? 'text-gray-600' : 'text-gray-300'
            } cursor-pointer hover:scale-110 transition-transform`}
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      );
    }
    return stars;
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'}`}>
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8 text-center">
          {submitSuccess ? 
            <span>Спасибо за ваш отзыв!</span> : 
            <span>Оставить отзыв о <span className={`${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>CTokenX</span></span>
          }
        </h1>
        
        {submitSuccess ? (
          <div className="text-center">
            <div className={`mb-6 ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-lg mb-4">
              Ваш отзыв успешно отправлен и будет опубликован после модерации.
            </p>
            <p className="mb-8">
              Вы будете перенаправлены на страницу отзывов.
            </p>
            <Link 
              href="/reviews" 
              className={`inline-block px-6 py-3 rounded-lg font-medium ${
                isDarkMode 
                  ? 'bg-violet-600 hover:bg-violet-700 text-white' 
                  : 'bg-violet-600 hover:bg-violet-700 text-white'
              }`}
            >
              Вернуться к отзывам
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={`rounded-lg p-6 ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
            {errors.submit && (
              <div className="mb-6 p-4 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                {errors.submit}
              </div>
            )}
            
            <div className="mb-6">
              <label htmlFor="name" className="block mb-2 font-medium">
                Ваше имя
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`w-full px-4 py-2 rounded-lg border ${
                  isDarkMode 
                    ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                    : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                } focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
                placeholder="Введите ваше имя"
              />
              {errors.name && (
                <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                  {errors.name}
                </p>
              )}
            </div>
            
            <div className="mb-6">
              <label htmlFor="email" className="block mb-2 font-medium">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-2 rounded-lg border ${
                  isDarkMode 
                    ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                    : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                } focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
                placeholder="Введите ваш email"
              />
              {errors.email && (
                <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                  {errors.email}
                </p>
              )}
            </div>
            
            <div className="mb-6">
              <label className="block mb-2 font-medium">
                Ваша оценка
              </label>
              <div className="flex space-x-1">
                {renderRatingStars()}
              </div>
            </div>
            
            <div className="mb-6">
              <label htmlFor="text" className="block mb-2 font-medium">
                Ваш отзыв
              </label>
              <textarea
                id="text"
                name="text"
                value={formData.text}
                onChange={handleChange}
                rows={5}
                className={`w-full px-4 py-2 rounded-lg border ${
                  isDarkMode 
                    ? 'bg-gray-700 border-gray-600 text-white focus:border-violet-500' 
                    : 'bg-white border-gray-300 text-gray-900 focus:border-violet-500'
                } focus:outline-none focus:ring-2 focus:ring-violet-500/50`}
                placeholder="Расскажите о вашем опыте использования нашего сервиса"
              ></textarea>
              {errors.text && (
                <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                  {errors.text}
                </p>
              )}
            </div>
            
            <div className="flex justify-between items-center">
              <Link 
                href="/reviews" 
                className={`px-6 py-2 rounded-lg font-medium ${
                  isDarkMode 
                    ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
                }`}
              >
                Назад
              </Link>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className={`px-6 py-2 rounded-lg font-medium ${
                  isDarkMode 
                    ? 'bg-violet-600 hover:bg-violet-700 text-white' 
                    : 'bg-violet-600 hover:bg-violet-700 text-white'
                } ${isSubmitting ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {isSubmitting ? 'Отправка...' : 'Отправить отзыв'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
} 