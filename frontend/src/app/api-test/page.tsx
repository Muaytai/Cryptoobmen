'use client';

import { useState, useEffect } from 'react';

export default function ApiTestPage() {
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Функция для выполнения простого тестового запроса
  const testApi = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/test');
      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
      console.error('Ошибка при тестировании API:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Функция для проверки прямого проксирования API
  const testDirectProxy = async () => {
    setLoading(true);
    setError(null);
    try {
      // Убедимся, что URL заканчивается на слэш
      const res = await fetch('/api/auth/registration/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'test@example.com',
          email: 'test@example.com',
          password: 'Test123!'
        }),
      });
      
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = { raw: text };
      }
      
      setResponse(JSON.stringify({
        status: res.status,
        statusText: res.statusText,
        data
      }, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
      console.error('Ошибка при тестировании прямого прокси:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Тестирование API</h1>
      
      <div style={{ marginBottom: '2rem' }}>
        <button 
          onClick={testApi} 
          disabled={loading}
          style={{ 
            padding: '0.5rem 1rem', 
            marginRight: '1rem',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Загрузка...' : 'Тест Next.js API'}
        </button>
        
        <button 
          onClick={testDirectProxy} 
          disabled={loading}
          style={{ 
            padding: '0.5rem 1rem', 
            backgroundColor: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Загрузка...' : 'Тест прямого прокси'}
        </button>
      </div>
      
      {error && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#FFEBEE', 
          color: '#D32F2F',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          <h3>Ошибка:</h3>
          <p>{error}</p>
        </div>
      )}
      
      {response && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#E8F5E9', 
          color: '#2E7D32',
          borderRadius: '4px'
        }}>
          <h3>Ответ:</h3>
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            wordBreak: 'break-word',
            backgroundColor: '#F5F5F5',
            padding: '1rem',
            borderRadius: '4px'
          }}>
            {response}
          </pre>
        </div>
      )}
    </div>
  );
} 