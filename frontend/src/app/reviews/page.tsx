'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Image from 'next/image';
import Link from 'next/link';
import FormAddReview from './components/FormAddReview';
import ReviewsCarousel from '@/components/ReviewsCarousel';

// Типы для отзывов
interface Review {
  id: number;
  name: string;
  rating: number;
  date: string;
  text: string;
  verified: boolean;
}

interface PaginationData {
  total: number;
  pages: number;
  currentPage: number;
  limit: number;
}

export default function ReviewsPage() {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [filter, setFilter] = useState('all'); // all, positive, negative
  const [reviews, setReviews] = useState<Review[]>([]);
  const [staticReviews, setStaticReviews] = useState<Review[]>([]); // Резервные демо-отзывы
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAllReviews, setShowAllReviews] = useState(false);
  const [pagination, setPagination] = useState<PaginationData>({
    total: 0,
    pages: 1,
    currentPage: 1,
    limit: 10
  });

  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);
  
  // Загрузка отзывов
  const fetchReviews = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reviews?filter=${filter}&page=${pagination.currentPage}&limit=${pagination.limit}`);
      
      if (!response.ok) {
        throw new Error('Ошибка при загрузке отзывов');
      }
      
      const data = await response.json();
      
      if (data.success && data.results && Array.isArray(data.results)) {
        setReviews(data.results);
        setPagination({
          total: data.count || 0,
          pages: Math.ceil((data.count || 0) / pagination.limit),
          currentPage: pagination.currentPage,
          limit: pagination.limit
        });
      } else {
        // Если API не возвращает данные или структура другая, используем демо-отзывы
        setReviews(staticReviews);
      }
    } catch (error) {
      console.error('Ошибка при получении отзывов:', error);
      setError('Не удалось загрузить отзывы. Отображаем демо-данные.');
      setReviews(staticReviews);
    } finally {
      setLoading(false);
    }
  };
  
  // Загружаем отзывы при изменении фильтра или страницы
  useEffect(() => {
    fetchReviews();
  }, [filter, pagination.currentPage]);

  // Демо-отзывы для отображения, когда API недоступен
  useEffect(() => {
    setStaticReviews([
      {
        id: 1,
        name: 'Александр',
        rating: 5,
        date: '15.04.2023',
        text: 'Пользуюсь платформой CTokenX уже более полугода. Очень доволен скоростью обработки транзакций и выгодными курсами обмена. Поддержка отвечает быстро и всегда помогает решить любые вопросы.',
        verified: true,
      },
      {
        id: 2,
        name: 'Елена',
        rating: 5,
        date: '22.05.2023',
        text: 'Отличная платформа для обмена криптовалют. Интуитивно понятный интерфейс, всё работает быстро и без сбоев. Особенно нравится возможность отслеживать статус транзакций в реальном времени.',
        verified: true,
      },
      {
        id: 3,
        name: 'Максим',
        rating: 4,
        date: '10.06.2023',
        text: 'В целом доволен сервисом. Удобный интерфейс, хорошие курсы. Из минусов - иногда бывают задержки при больших суммах, но это, наверное, связано с проверками безопасности.',
        verified: true,
      },
      {
        id: 4,
        name: 'Ирина',
        rating: 5,
        date: '28.07.2023',
        text: 'Самая удобная платформа для обмена, которой я пользовалась. Верификация прошла быстро, комиссии низкие, операции выполняются практически мгновенно. Рекомендую всем!',
        verified: true,
      },
      {
        id: 5,
        name: 'Дмитрий',
        rating: 4,
        date: '15.08.2023',
        text: 'Хороший сервис с понятным интерфейсом. Правда, один раз была задержка с выводом средств, но служба поддержки быстро решила проблему. В целом рекомендую.',
        verified: true,
      },
      {
        id: 6,
        name: 'Анна',
        rating: 5,
        date: '09.09.2023',
        text: 'Пользуюсь CTokenX уже год, ни разу не было проблем. Радует, что постоянно добавляются новые криптовалюты и улучшается функционал платформы. Отдельное спасибо за круглосуточную поддержку!',
        verified: true,
      },
      {
        id: 7,
        name: 'Сергей',
        rating: 3,
        date: '12.10.2023',
        text: 'Сервис неплохой, но хотелось бы больше аналитических инструментов. Транзакции проходят быстро, но интерфейс мог бы быть более современным.',
        verified: true,
      },
      {
        id: 8,
        name: 'Ольга',
        rating: 5,
        date: '26.11.2023',
        text: 'Очень благодарна команде CTokenX за отличный сервис. Всё работает как часы, верификация проходит быстро, а курсы действительно выгодные. Буду рекомендовать вас друзьям!',
        verified: true,
      },
    ]);
  }, []);
  
  // Фильтрация отзывов
  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
    setPagination(prev => ({...prev, currentPage: 1})); // Сброс на первую страницу при изменении фильтра
  };

  // Пагинация
  const handlePageChange = (page: number) => {
    setPagination(prev => ({...prev, currentPage: page}));
  };

  // Обработчик добавления нового отзыва
  const handleReviewAdded = () => {
    // Обновляем список отзывов после добавления нового
    fetchReviews();
  };

  // Отрисовка звёздочек рейтинга
  const renderStars = (rating: number) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <svg
          key={i}
          className={`w-5 h-5 ${
            i <= rating 
              ? isDarkMode ? 'text-yellow-400' : 'text-yellow-500' 
              : isDarkMode ? 'text-gray-600' : 'text-gray-300'
          }`}
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      );
    }
    return stars;
  };

  // Отрисовка пагинации
  const renderPagination = () => {
    if (pagination.pages <= 1) return null;
    
    const pages = [];
    for (let i = 1; i <= pagination.pages; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`px-3 py-1 rounded-md ${
            pagination.currentPage === i
              ? isDarkMode ? 'bg-violet-600 text-white' : 'bg-violet-600 text-white'
              : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
          }`}
        >
          {i}
        </button>
      );
    }
    
    return (
      <div className="flex justify-center space-x-2 mt-8">
        <button
          onClick={() => handlePageChange(Math.max(1, pagination.currentPage - 1))}
          disabled={pagination.currentPage === 1}
          className={`px-3 py-1 rounded-md ${
            pagination.currentPage === 1
              ? isDarkMode ? 'bg-gray-800 text-gray-500' : 'bg-gray-100 text-gray-400'
              : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
          }`}
        >
          &laquo;
        </button>
        {pages}
        <button
          onClick={() => handlePageChange(Math.min(pagination.pages, pagination.currentPage + 1))}
          disabled={pagination.currentPage === pagination.pages}
          className={`px-3 py-1 rounded-md ${
            pagination.currentPage === pagination.pages
              ? isDarkMode ? 'bg-gray-800 text-gray-500' : 'bg-gray-100 text-gray-400'
              : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
          }`}
        >
          &raquo;
        </button>
      </div>
    );
  };

  // Показываем только первые 3 отзыва, если не включен режим "показать все"
  const visibleReviews = showAllReviews ? reviews : reviews.slice(0, 3);

  // Обработчик нажатия кнопки "Показать все отзывы"
  const toggleShowAllReviews = () => {
    setShowAllReviews(!showAllReviews);
  };

  return (
    <div className={`${isDarkMode ? 'bg-[#111014] text-white' : 'bg-white text-gray-900'}`}>
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          Отзывы о <span className={`${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>CTokenX</span>
        </h1>
        
        {/* Карусель избранных отзывов */}
        <div className="mb-10">
          <ReviewsCarousel 
            isReviewsPage={true}
            containerStyle={{
              maxWidth: 1100,
              margin: '0 auto',
              padding: '30px 15px',
              borderRadius: 12,
              background: isDarkMode ? 'rgba(30, 30, 35, 0.5)' : 'rgba(245, 245, 250, 0.5)',
            }}
          />
        </div>
        
        {/* Статистика отзывов */}
        <div className="mb-12">
          <div className={`max-w-4xl mx-auto p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
            <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16">
              <div className="text-center">
                <div className={`text-4xl font-bold ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
                  {pagination.total || reviews.length}
                </div>
                <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Всего отзывов
                </div>
              </div>
              
              <div className="text-center">
                <div className="flex justify-center">
                  {[1, 2, 3, 4, 5].map(i => (
                    <svg
                      key={i}
                      className={`w-6 h-6 ${isDarkMode ? 'text-yellow-400' : 'text-yellow-500'}`}
                      fill="currentColor"
                      viewBox="0 0 20 20"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Средний рейтинг 4.8
                </div>
              </div>
              
              <div className="text-center">
                <div className={`text-4xl font-bold ${isDarkMode ? 'text-violet-400' : 'text-violet-600'}`}>
                  98%
                </div>
                <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Положительных отзывов
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Фильтры отзывов */}
        <div className="flex justify-center flex-wrap gap-2 mt-10 mb-8">
          <button 
            onClick={() => handleFilterChange('all')} 
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              filter === 'all' 
                ? isDarkMode ? 'bg-violet-600 text-white' : 'bg-violet-600 text-white'
                : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Все отзывы
          </button>
          <button 
            onClick={() => handleFilterChange('positive')} 
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              filter === 'positive' 
                ? isDarkMode ? 'bg-violet-600 text-white' : 'bg-violet-600 text-white'
                : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Положительные
          </button>
          <button 
            onClick={() => handleFilterChange('negative')} 
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              filter === 'negative' 
                ? isDarkMode ? 'bg-violet-600 text-white' : 'bg-violet-600 text-white'
                : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Критические
          </button>
        </div>
        
        {/* Отображение ошибки */}
        {error && (
          <div className={`p-4 mb-6 rounded-md ${isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800'}`}>
            {error}
          </div>
        )}
        
        {/* Список отзывов */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-violet-500"></div>
          </div>
        ) : error ? (
          <div className={`text-center py-6 rounded-lg ${isDarkMode ? 'bg-red-900/20 text-red-200' : 'bg-red-100 text-red-700'}`}>
            {error}
          </div>
        ) : visibleReviews.length > 0 ? (
          <div className="space-y-6">
            {visibleReviews.map((review) => (
              <div 
                key={review.id} 
                className={`p-6 rounded-lg ${isDarkMode ? 'bg-gray-800/70' : 'bg-gray-50'}`}
              >
                <div className="flex flex-wrap items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold mb-1">{review.name}</h3>
                  <div className="flex mb-2">
                    {renderStars(review.rating)}
                  </div>
                </div>
                <div className="mb-2">
                  <div className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {review.date}
                    {review.verified && (
                      <div className="flex items-center mt-1 text-green-500">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                          <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                        </svg>
                        Проверено
                      </div>
                    )}
                  </div>
                </div>
                <p className={`${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  {review.text}
                </p>
              </div>
            ))}
            
            {/* Кнопка "Показать все / Свернуть" */}
            {reviews.length > 3 && (
              <div className="flex justify-center mt-8">
                <button
                  onClick={toggleShowAllReviews}
                  className={`flex items-center px-5 py-2.5 rounded-lg transition-all ${
                    isDarkMode ? 'bg-violet-600 hover:bg-violet-700 text-white' : 'bg-violet-600 hover:bg-violet-700 text-white'
                  }`}
                >
                  {showAllReviews ? (
                    <>
                      <span>Свернуть</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7"></path>
                      </svg>
                    </>
                  ) : (
                    <>
                      <span>Показать все отзывы ({reviews.length})</span>
                      <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                      </svg>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className={`text-center py-12 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Отзывов пока нет. Будьте первым, кто оставит отзыв!
          </div>
        )}
        
        {/* Пагинация показываем только если включен режим "показать все" и есть несколько страниц */}
        {showAllReviews && renderPagination()}
        
        {/* Форма добавления отзыва */}
        <div className="mt-16">
          <FormAddReview onReviewAdded={handleReviewAdded} />
        </div>
      </div>
    </div>
  );
} 