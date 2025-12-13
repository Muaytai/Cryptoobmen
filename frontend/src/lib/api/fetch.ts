// Базовый URL API, устанавливаемый из переменных окружения
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
console.log('Базовый URL API:', API_BASE_URL);

// Функция для получения понятного сообщения об ошибке по статус коду
const getErrorMessageByStatus = (status: number): string => {
  switch (status) {
    case 400:
      return 'Некорректный запрос. Проверьте введенные данные.';
    case 401:
      return 'Необходима авторизация.';
    case 403:
      return 'Доступ запрещен.';
    case 404:
      return 'Ресурс не найден.';
    case 500:
      return 'Внутренняя ошибка сервера. Попробуйте позже.';
    case 502:
      return 'Сервер временно недоступен. Попробуйте позже.';
    case 503:
      return 'Сервис временно недоступен. Попробуйте позже.';
    default:
      return `Ошибка сервера. Код: ${status}`;
  }
};

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
      let errorData: any;
      try {
        errorData = await response.json();
      } catch (_err) {
        // Если не удалось распарсить JSON, возвращаем базовое сообщение
        throw new Error(`Ошибка сервера. Код: ${response.status}`);
      }
      
      // Формируем детальное сообщение об ошибке
      let errorMessage = '';
      
      // Если есть общее сообщение об ошибке
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      } else if (errorData.non_field_errors && Array.isArray(errorData.non_field_errors)) {
        // Ошибки, не привязанные к конкретным полям
        errorMessage = errorData.non_field_errors.join('. ');
      } else {
        // Обрабатываем ошибки для конкретных полей (email, username, password и т.д.)
        const fieldErrors: string[] = [];
        for (const [field, errors] of Object.entries(errorData)) {
          if (Array.isArray(errors)) {
            fieldErrors.push(`${field}: ${errors.join(', ')}`);
          } else if (typeof errors === 'string') {
            fieldErrors.push(`${field}: ${errors}`);
          }
        }
        
        if (fieldErrors.length > 0) {
          errorMessage = fieldErrors.join('. ');
        } else {
          // Если ничего не найдено, используем статус код
          errorMessage = getErrorMessageByStatus(response.status);
        }
      }
      
      const error = new Error(errorMessage);
      (error as any).status = response.status;
      (error as any).data = errorData;
      throw error;
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