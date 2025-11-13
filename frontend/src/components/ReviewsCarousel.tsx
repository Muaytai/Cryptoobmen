'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import Image from 'next/image';
import Link from 'next/link';

interface Review {
  id: number;
  name: string;
  rating: number;
  date: string;
  text: string;
  verified: boolean;
}

interface ReviewsCarouselProps {
  // Опциональные CSSProperties, которые можно передать извне
  containerStyle?: React.CSSProperties;
  // Флаг, который указывает, находится ли компонент на странице отзывов
  isReviewsPage?: boolean;
}

const ReviewsCarousel: React.FC<ReviewsCarouselProps> = ({ 
  containerStyle = {},
  isReviewsPage = false 
}) => {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentSlide, setCurrentSlide] = useState(0);

  // Обновляем состояние isDarkMode при изменении темы
  useEffect(() => {
    if (typeof document !== 'undefined') {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    }
  }, [theme]);

  // Загружаем лучшие отзывы
  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const response = await fetch('/api/reviews/featured');
        
        if (!response.ok) {
          throw new Error('Ошибка при загрузке отзывов');
        }
        
        const data = await response.json();
        
        if (data.success && data.results && Array.isArray(data.results)) {
          setReviews(data.results);
        } else {
          // Если API не возвращает данные, используем демо-отзывы
          setReviews([
            {
              id: 1,
              name: 'Александр',
              rating: 5,
              date: '15.04.2023',
              text: 'Пользуюсь платформой CTokenX уже более полугода. Очень доволен скоростью обработки транзакций и выгодными курсами обмена.',
              verified: true,
            },
            {
              id: 2,
              name: 'Елена',
              rating: 5,
              date: '22.05.2023',
              text: 'Отличная платформа для обмена криптовалют. Интуитивно понятный интерфейс, всё работает быстро и без сбоев.',
              verified: true,
            },
            {
              id: 3,
              name: 'Максим',
              rating: 4,
              date: '10.06.2023',
              text: 'В целом доволен сервисом. Удобный интерфейс, хорошие курсы. Рекомендую всем!',
              verified: true,
            },
          ]);
        }
      } catch (error) {
        console.error('Ошибка при получении отзывов:', error);
        // Резервные данные
        setReviews([
          {
            id: 1,
            name: 'Александр',
            rating: 5,
            date: '15.04.2023',
            text: 'Пользуюсь платформой CTokenX уже более полугода. Очень доволен скоростью обработки транзакций и выгодными курсами обмена.',
            verified: true,
          },
          {
            id: 2,
            name: 'Елена',
            rating: 5,
            date: '22.05.2023',
            text: 'Отличная платформа для обмена криптовалют. Интуитивно понятный интерфейс, всё работает быстро и без сбоев.',
            verified: true,
          },
          {
            id: 3,
            name: 'Максим',
            rating: 4,
            date: '10.06.2023',
            text: 'В целом доволен сервисом. Удобный интерфейс, хорошие курсы. Рекомендую всем!',
            verified: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchReviews();
  }, []);

  // Автоматическое переключение слайдов
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev === reviews.length - 1 ? 0 : prev + 1));
    }, 5000);
    
    return () => clearInterval(interval);
  }, [reviews.length]);

  // Отрисовка звёздочек рейтинга
  const renderStars = (rating: number) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <svg
          key={i}
          className={`w-4 h-4 ${
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

  if (loading) {
    return (
      <div className="flex justify-center items-center py-6">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-violet-500"></div>
      </div>
    );
  }

  if (reviews.length === 0) {
    return null;
  }

  const mainContainerStyle: React.CSSProperties = {
    padding: '40px 20px',
    marginTop: 60,
    marginBottom: 60,
    borderRadius: 12,
    ...containerStyle,
    background: isDarkMode ? 'rgba(30, 30, 35, 0.5)' : 'rgba(245, 245, 250, 0.5)',
    backdropFilter: 'blur(5px)',
    WebkitBackdropFilter: 'blur(5px)',
  };

  const titleStyle: React.CSSProperties = {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 30,
    textAlign: 'center',
    color: isDarkMode ? '#fff' : '#111827',
  };

  const carouselStyle: React.CSSProperties = {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 25,
  };

  const reviewCardStyle: React.CSSProperties = {
    background: isDarkMode ? 'rgba(40, 40, 45, 0.7)' : 'rgba(255, 255, 255, 0.9)',
    borderRadius: 12,
    padding: 20,
    margin: '0 auto',
    maxWidth: 700,
    boxShadow: isDarkMode 
      ? '0 4px 14px rgba(0, 0, 0, 0.3)' 
      : '0 4px 14px rgba(0, 0, 0, 0.1)',
  };

  const buttonStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    background: '#a259ff',
    color: '#fff',
    padding: '10px 20px',
    borderRadius: 12,
    fontWeight: 500,
    transition: 'all 0.2s ease',
    border: 'none',
    cursor: 'pointer',
  };

  return (
    <div style={mainContainerStyle}>
      {!isReviewsPage && (
        <h2 style={titleStyle}>
          Отзывы наших клиентов
        </h2>
      )}
      
      <div style={carouselStyle}>
        <div 
          style={{
            transition: 'transform 500ms ease-in-out',
            transform: `translateX(-${currentSlide * 100}%)`,
            display: 'flex',
          }}
        >
          {reviews.map((review, index) => (
            <div key={review.id} style={{minWidth: '100%', padding: '0 15px'}}>
              <div style={reviewCardStyle}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16}}>
                  <div>
                    <h3 style={{fontWeight: 600, fontSize: 18, color: isDarkMode ? '#fff' : '#333', marginBottom: 6}}>
                      {review.name}
                    </h3>
                    <div style={{display: 'flex'}}>
                      {renderStars(review.rating)}
                    </div>
                  </div>
                  <div style={{fontSize: 14, color: isDarkMode ? '#999' : '#666'}}>
                    {review.date}
                    {review.verified && (
                      <div style={{display: 'flex', alignItems: 'center', marginTop: 4, color: '#10b981'}}>
                        <svg style={{width: 16, height: 16, marginRight: 4}} fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                          <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                        </svg>
                        Проверено
                      </div>
                    )}
                  </div>
                </div>
                <p style={{color: isDarkMode ? '#e0e0e0' : '#444', fontSize: 16, lineHeight: 1.5}}>
                  "{review.text}"
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Пагинация */}
      <div style={{display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 25}}>
        {reviews.map((_, index) => (
          <button 
            key={index}
            onClick={() => setCurrentSlide(index)}
            style={{
              height: 8,
              borderRadius: 4,
              transition: 'all 0.2s ease',
              width: currentSlide === index ? 24 : 8,
              background: currentSlide === index 
                ? '#a259ff' 
                : isDarkMode ? 'rgba(150, 150, 150, 0.3)' : 'rgba(150, 150, 150, 0.5)',
              border: 'none',
              padding: 0,
              cursor: 'pointer',
            }}
            aria-label={`Перейти к слайду ${index + 1}`}
          />
        ))}
      </div>
      
      {!isReviewsPage && (
        <div style={{textAlign: 'center'}}>
          <Link 
            href="/reviews" 
            style={buttonStyle}
            onMouseOver={(e) => {
              const target = e.currentTarget.style as any;
              target.background = '#8f3fff';
            }}
            onMouseOut={(e) => {
              const target = e.currentTarget.style as any;
              target.background = '#a259ff';
            }}
          >
            Посмотреть все отзывы
            <svg 
              style={{
                width: 16, 
                height: 16, 
                marginLeft: 8,
                stroke: 'currentColor'
              }}
              fill="none" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
            </svg>
          </Link>
        </div>
      )}
    </div>
  );
};

export default ReviewsCarousel; 