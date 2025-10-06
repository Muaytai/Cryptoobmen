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
const getAuthHeaders = (isFormData = false, customHeaders: Record<string, string> = {}) => {
  // Для HttpOnly куки не нужно устанавливать Authorization заголовок вручную
  // Браузер автоматически отправляет HttpOnly куки с credentials: 'include'
  const baseHeaders = {
    // Для FormData не устанавливаем Content-Type, браузер сам установит правильную границу
    ...(isFormData ? {} : { 'Content-Type': 'application/json' })
  };
  
  // Объединяем базовые заголовки с пользовательскими
  return {
    ...baseHeaders,
    ...customHeaders
  };
};

// Основная функция для выполнения запросов к API
const fetcher = async (url: string, options: RequestInit = {}) => {
  try {
    // Формируем полный URL для запроса
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    // Определяем, является ли тело запроса FormData
    const isFormData = options.body instanceof FormData;
    
    // Получаем пользовательские заголовки из options
    const customHeaders = (options.headers as Record<string, string>) || {};
    
    // Объединяем заголовки по умолчанию и переданные пользователем
    const headers = {
      ...getAuthHeaders(isFormData, customHeaders),
      ...(options.headers || {})
    };
    
    // Логируем заголовки для отладки
    console.log('[fetch.ts] Заголовки запроса:', headers);
    console.log('[fetch.ts] URL:', fullUrl);
    console.log('[fetch.ts] Метод:', options.method || 'GET');

    // Выполняем запрос с учетом всех параметров
    const response = await fetch(fullUrl, {
      ...options,
      headers,
      credentials: 'include'
    });

    // Если ответ не успешный, выбрасываем ошибку
    if (!response.ok) {
      let errorData: any;
      try {
        errorData = await response.json();
      } catch (e) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      // Специальная обработка для ошибок rate limiting
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        const retrySeconds = retryAfter ? parseInt(retryAfter) : 60;
        throw new Error(`Too Many Requests. Please try again in ${retrySeconds} seconds.`);
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
    // Для FormData не сериализуем в JSON
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return fetcher(url, {
      ...options,
      method: 'PATCH',
      body
    });
  },
  
  delete: async (url: string, options: RequestInit = {}) => {
    return fetcher(url, { ...options, method: 'DELETE' });
  }
};

export default api; 