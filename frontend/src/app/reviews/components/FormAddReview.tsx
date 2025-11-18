import React, { useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface FormAddReviewProps {
  onReviewAdded: () => void;
}

const FormAddReview: React.FC<FormAddReviewProps> = ({ onReviewAdded }) => {
  const { theme } = useTheme();
  const isDarkMode = typeof document !== 'undefined' ? document.documentElement.classList.contains('dark') : false;

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    rating: 5,
    text: ''
  });

  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rating' ? parseInt(value) : value
    }));
    
    // Очищаем ошибку при изменении поля
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors: {[key: string]: string} = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Имя обязательно';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email обязателен';
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = 'Некорректный email';
      }
    }
    
    if (!formData.text.trim()) {
      newErrors.text = 'Текст отзыва обязателен';
    } else if (formData.text.length < 10) {
      newErrors.text = 'Отзыв слишком короткий (минимум 10 символов)';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    setMessage(null);
    
    try {
      const response = await fetch('/api/reviews', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setMessage({
          text: data.message || 'Отзыв успешно отправлен!',
          type: 'success'
        });
        setFormData({
          name: '',
          email: '',
          rating: 5,
          text: ''
        });
        onReviewAdded();
      } else {
        setMessage({
          text: data.message || 'Ошибка при отправке отзыва.',
          type: 'error'
        });
        if (data.errors) {
          setErrors(data.errors);
        }
      }
    } catch (error) {
      setMessage({
        text: 'Произошла ошибка при отправке отзыва. Пожалуйста, попробуйте позже.',
        type: 'error'
      });
      console.error('Ошибка при отправке отзыва:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Отрисовка звёздочек для рейтинга
  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <label key={i} className="cursor-pointer">
          <input
            type="radio"
            name="rating"
            value={i}
            checked={formData.rating === i}
            onChange={handleChange}
            className="sr-only"
          />
          <svg
            className={`w-8 h-8 ${
              i <= formData.rating 
                ? isDarkMode ? 'text-yellow-400' : 'text-yellow-500'
                : isDarkMode ? 'text-gray-600' : 'text-gray-300'
            } cursor-pointer`}
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </label>
      );
    }
    return stars;
  };

  return (
    <div className={`w-full max-w-2xl mx-auto my-10 p-6 rounded-lg ${isDarkMode ? 'bg-gray-800' : 'bg-white shadow-md'}`}>
      <h2 className={`text-2xl font-bold mb-6 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
        Оставить отзыв
      </h2>
      
      {message && (
        <div className={`mb-6 p-4 rounded-md ${
          message.type === 'success' 
            ? isDarkMode ? 'bg-green-800 text-green-200' : 'bg-green-100 text-green-800'
            : isDarkMode ? 'bg-red-800 text-red-200' : 'bg-red-100 text-red-800'
        }`}>
          {message.text}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="name" className={`block mb-2 font-medium ${isDarkMode ? 'text-white' : 'text-gray-700'}`}>
            Имя*
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={`w-full px-4 py-2 rounded-md ${
              isDarkMode 
                ? 'bg-gray-700 text-white border-gray-600 focus:border-violet-500' 
                : 'bg-white text-gray-900 border-gray-300 focus:border-violet-500'
            } border focus:outline-none focus:ring-1 focus:ring-violet-500`}
            placeholder="Ваше имя"
          />
          {errors.name && (
            <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-500'}`}>{errors.name}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label htmlFor="email" className={`block mb-2 font-medium ${isDarkMode ? 'text-white' : 'text-gray-700'}`}>
            Email*
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={`w-full px-4 py-2 rounded-md ${
              isDarkMode 
                ? 'bg-gray-700 text-white border-gray-600 focus:border-violet-500' 
                : 'bg-white text-gray-900 border-gray-300 focus:border-violet-500'
            } border focus:outline-none focus:ring-1 focus:ring-violet-500`}
            placeholder="ваш@email.com"
          />
          {errors.email && (
            <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-500'}`}>{errors.email}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label className={`block mb-2 font-medium ${isDarkMode ? 'text-white' : 'text-gray-700'}`}>
            Рейтинг*
          </label>
          <div className="flex space-x-1">
            {renderStars()}
          </div>
        </div>
        
        <div className="mb-6">
          <label htmlFor="text" className={`block mb-2 font-medium ${isDarkMode ? 'text-white' : 'text-gray-700'}`}>
            Текст отзыва*
          </label>
          <textarea
            id="text"
            name="text"
            value={formData.text}
            onChange={handleChange}
            rows={4}
            className={`w-full px-4 py-2 rounded-md ${
              isDarkMode 
                ? 'bg-gray-700 text-white border-gray-600 focus:border-violet-500' 
                : 'bg-white text-gray-900 border-gray-300 focus:border-violet-500'
            } border focus:outline-none focus:ring-1 focus:ring-violet-500`}
            placeholder="Поделитесь своими впечатлениями..."
          ></textarea>
          {errors.text && (
            <p className={`mt-1 text-sm ${isDarkMode ? 'text-red-400' : 'text-red-500'}`}>{errors.text}</p>
          )}
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-2 px-4 text-white font-medium rounded-md ${
            isSubmitting 
              ? isDarkMode ? 'bg-violet-700 cursor-not-allowed' : 'bg-violet-400 cursor-not-allowed'
              : isDarkMode ? 'bg-violet-600 hover:bg-violet-700' : 'bg-violet-600 hover:bg-violet-700'
          } transition-colors`}
        >
          {isSubmitting ? 'Отправка...' : 'Отправить отзыв'}
        </button>
      </form>
    </div>
  );
};

export default FormAddReview; 