'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextProps {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextProps | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark'); // Темная тема по умолчанию

  // Функция для переключения темы
  const toggleTheme = () => {
    setTheme((prevTheme) => {
      const newTheme = prevTheme === 'light' ? 'dark' : 'light';
      // Сохраняем выбор пользователя в localStorage
      localStorage.setItem('theme', newTheme);
      console.log('Тема изменена на:', newTheme);
      return newTheme;
    });
  };

  // Применяем класс темы к HTML элементу
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
      document.body.classList.add('dark');
      document.body.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
      document.body.classList.add('light');
      document.body.classList.remove('dark');
    }
    console.log('Применен класс для темы:', theme);
  }, [theme]);

  // При загрузке компонента, проверяем сохраненную тему в localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme') as Theme | null;
      
      if (savedTheme) {
        console.log('Загружена сохраненная тема:', savedTheme);
        setTheme(savedTheme);
      } else {
        localStorage.setItem('theme', theme);
      }

      // Проверяем системные настройки, если нет сохраненной темы
      if (!savedTheme && window.matchMedia) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
          setTheme('dark');
        }
      }
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
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