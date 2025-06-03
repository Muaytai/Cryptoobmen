interface Tokens {
  access: string;
  refresh: string;
}

// Используем базовый URL без /api, так как он уже содержится в NEXT_PUBLIC_API_URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'; // Возвращаем /api сюда, если это стандарт
console.log('Базовый URL API:', API_URL);

interface ApiResponse<T = any> {
  data: T;
  error?: string;
}

// Базовые настройки для fetch запросов
const fetchConfig: RequestInit = {
  credentials: 'include', // Важно для работы с куками
  headers: {
    'Content-Type': 'application/json',
  },
};

// Функция для обработки ответа
const handleResponse = async (response: Response): Promise<ApiResponse> => {
  const contentType = response.headers.get('content-type');
  let data;

  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    if (response.status === 500) {
      throw new Error('Внутренняя ошибка сервера. Попробуйте позже или свяжитесь с поддержкой.');
    }
    if (data && typeof data === 'object' && data.detail) {
      throw new Error(data.detail);
    }
    if (data && typeof data === 'object') {
      const errorMessages = Object.values(data)
        .flat()
        .join(' ');
      throw new Error(errorMessages || 'Произошла ошибка при выполнении запроса');
    }
    throw new Error(data || 'Произошла ошибка при выполнении запроса');
  }
  return { data };
};

// API функции
export const api = {
  // Аутентификация
  auth: {
    async login(email: string, password: string): Promise<ApiResponse> {
      const response = await fetch(`${API_URL}/auth/login/`, {
        ...fetchConfig,
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      return handleResponse(response);
    },

    async getToken(credentials: { email: string, password: string }): Promise<ApiResponse<Tokens>> {
      const response = await fetch(`${API_URL}/token/`, {
        ...fetchConfig,
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Ошибка получения токена, не удалось прочитать ответ сервера' }));
        throw new Error(errorData.detail || JSON.stringify(errorData));
      }
      const tokens = await response.json();
      return { data: tokens };
    },

    async logout(): Promise<ApiResponse> {
      const response = await fetch(`${API_URL}/auth/logout/`, {
        ...fetchConfig,
        method: 'POST',
      });
      return handleResponse(response);
    },

    async getUser(): Promise<ApiResponse> {
      const response = await fetch(`${API_URL}/auth/user/`, {
        ...fetchConfig,
        method: 'GET',
      });
      return handleResponse(response);
    },
  },

  // Общие методы для работы с API
  async get(endpoint: string): Promise<ApiResponse> {
    const currentConfig = { ...fetchConfig, method: 'GET' };
    const response = await fetch(`${API_URL}${endpoint}`, currentConfig);
    return handleResponse(response);
  },

  async post(endpoint: string, data: any): Promise<ApiResponse> {
    const currentConfig = { ...fetchConfig, method: 'POST', body: JSON.stringify(data) };
    const response = await fetch(`${API_URL}${endpoint}`, currentConfig);
    return handleResponse(response);
  },

  async put(endpoint: string, data: any): Promise<ApiResponse> {
    const currentConfig = { ...fetchConfig, method: 'PUT', body: JSON.stringify(data) };
    const response = await fetch(`${API_URL}${endpoint}`, currentConfig);
    return handleResponse(response);
  },

  async delete(endpoint: string): Promise<ApiResponse> {
    const currentConfig = { ...fetchConfig, method: 'DELETE' };
    const response = await fetch(`${API_URL}${endpoint}`, currentConfig);
    return handleResponse(response);
  },
};

export default api; 