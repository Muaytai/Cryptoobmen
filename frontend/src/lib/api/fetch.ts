// Используем базовый URL без /api, так как он уже содержится в NEXT_PUBLIC_API_URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://tkxn.org/api';
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
    throw new Error(data.detail || 'Произошла ошибка при выполнении запроса');
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
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...fetchConfig,
      method: 'GET',
    });
    return handleResponse(response);
  },

  async post(endpoint: string, data: any): Promise<ApiResponse> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...fetchConfig,
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  async put(endpoint: string, data: any): Promise<ApiResponse> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...fetchConfig,
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  async delete(endpoint: string): Promise<ApiResponse> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...fetchConfig,
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export default api; 