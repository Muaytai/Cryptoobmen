// Базовый URL API, устанавливаемый из переменных окружения
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
console.log('Базовый URL API:', API_BASE_URL);

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
const fetcher = async <T = unknown>(url: string, options: RequestInit = {}): Promise<T> => {
  try {
    // Формируем полный URL для запроса
    const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

    // Определяем, является ли тело запроса FormData
    const isFormData = options.body instanceof FormData;
    
    // Получаем пользовательские заголовки из options
    const customHeaders = options.headers as Record<string, string> || {};
    
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
      let errorData: { detail?: string; message?: string } | undefined;
      try {
        errorData = await response.json();
      } catch (_err) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      throw new Error(errorData.detail || errorData.message || `HTTP error! Status: ${response.status}`);
    }

    // Проверяем content-type для определения формата ответа
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    } else {
      return (await response.text()) as T;
    }
  } catch (error) {
    console.error('Ошибка API запроса:', error);
    throw error;
  }
};

// API клиент с методами для разных типов запросов
const api = {
  get: async <T = unknown>(url: string, options: RequestInit = {}): Promise<T> => {
    return fetcher<T>(url, { ...options, method: 'GET' });
  },
  
  post: async <TResponse = unknown, TBody = unknown>(url: string, data: TBody, options: RequestInit = {}): Promise<TResponse> => {
    return fetcher<TResponse>(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  put: async <TResponse = unknown, TBody = unknown>(url: string, data: TBody, options: RequestInit = {}): Promise<TResponse> => {
    return fetcher<TResponse>(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  patch: async <TResponse = unknown, TBody = unknown>(url: string, data: TBody, options: RequestInit = {}): Promise<TResponse> => {
    // Для FormData не сериализуем в JSON
    const body = data instanceof FormData ? data : JSON.stringify(data);
    return fetcher<TResponse>(url, {
      ...options,
      method: 'PATCH',
      body
    });
  },
  
  delete: async <TResponse = unknown>(url: string, options: RequestInit = {}): Promise<TResponse> => {
    return fetcher<TResponse>(url, { ...options, method: 'DELETE' });
  }
};

export default api; 