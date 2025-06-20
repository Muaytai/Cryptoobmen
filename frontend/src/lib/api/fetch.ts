import { getCookie } from '../cookies';

interface Tokens {
  access: string;
  refresh: string;
}

// Базовый URL API, устанавливаемый из переменных окружения
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
console.log('Базовый URL API:', API_BASE_URL);

interface ApiResponse<T = any> {
  data: T;
  error?: string;
}

// Функция для получения заголовков с авторизацией
const getAuthHeaders = () => {
  const token = getCookie('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

// Основная функция для выполнения запросов к API
const fetcher = async (url: string, options: RequestInit = {}) => {
  try {
    // Формируем полный URL для запроса
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    // Объединяем заголовки по умолчанию и переданные пользователем
    const headers = {
      ...getAuthHeaders(),
      ...(options.headers || {})
    };

    // Выполняем запрос с учетом всех параметров
    const response = await fetch(fullUrl, {
      ...options,
      headers,
      credentials: 'include'
    });

    // Если ответ не успешный, выбрасываем ошибку
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      throw new Error(errorData.detail || errorData.message || `HTTP error! Status: ${response.status}`);
    }

    // Проверяем content-type для определения формата ответа
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
  } catch (error) {
    console.error('Ошибка API запроса:', error);
    throw error;
  }
};

// API клиент с методами для разных типов запросов
const api = {
  get: async (url: string, options: RequestInit = {}) => {
    return fetcher(url, { ...options, method: 'GET' });
  },
  
  post: async (url: string, data: any, options: RequestInit = {}) => {
    return fetcher(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  put: async (url: string, data: any, options: RequestInit = {}) => {
    return fetcher(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  patch: async (url: string, data: any, options: RequestInit = {}) => {
    return fetcher(url, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  delete: async (url: string, options: RequestInit = {}) => {
    return fetcher(url, { ...options, method: 'DELETE' });
  }
};

export default api; 