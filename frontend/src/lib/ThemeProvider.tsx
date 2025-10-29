'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextProps {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextProps | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Устанавливаем темную тему по умолчанию
  const [theme, setTheme] = useState<Theme>('dark');
  const [isInitialized, setIsInitialized] = useState(false);

  // Функция для переключения темы - только через кнопку переключения
  const toggleTheme = () => {
    setTheme((prevTheme) => {
      const newTheme = prevTheme === 'light' ? 'dark' : 'light';
      // Сохраняем выбор пользователя в localStorage
      localStorage.setItem('theme', newTheme);
      return newTheme;
    });
  };

  // Применяем класс темы к HTML элементу
  useEffect(() => {
    // Применяем тему только после инициализации, чтобы избежать мерцания
    if (!isInitialized) return;
    
    const html = document.documentElement;
    
    if (theme === 'dark') {
      html.classList.add('dark');
      html.classList.remove('light');
    } else {
      html.classList.add('light');
      html.classList.remove('dark');
    }

    // Устанавливаем атрибут data-theme для возможности CSS-селекторов
    html.setAttribute('data-theme', theme);
    
    // Также обновляем классы для body для совместимости
    document.body.className = document.body.className
      .replace(/\b(light|dark)\b/g, '')
      .trim() + ` ${theme}`;
  }, [theme, isInitialized]);

  // Загружаем сохраненную тему только один раз при инициализации
  useEffect(() => {
    if (typeof window !== 'undefined' && !isInitialized) {
      // Загружаем тему из localStorage, или используем темную по умолчанию
      const savedTheme = localStorage.getItem('theme') as Theme | null;
      
      if (savedTheme) {
        setTheme(savedTheme);
      } else {
        // Если нет сохраненной темы, устанавливаем темную по умолчанию
        localStorage.setItem('theme', 'dark');
      }
      
      // Обозначаем, что инициализация завершена
      setIsInitialized(true);
    }
  }, [isInitialized]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Хук для использования темы в компонентах
export function useTheme() {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
} 