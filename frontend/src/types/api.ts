// Пользовательские типы
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  is_verified: boolean;
  is_staff: boolean;
  created_at: string;
}

// Типы для аутентификации
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  password2: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// Типы для криптовалюты
export interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  logo_url: string;
  is_active: boolean;
  exchange_rate: number;
}

// Типы для транзакций
export interface Transaction {
  id: number;
  user: User;
  from_currency: Currency;
  to_currency: Currency;
  from_amount: number;
  to_amount: number;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  transaction_id: string;
}

// Типы для запросов и ответов
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
} 