'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextProps {
  deviceType: string;
}

export const AnimatedHeroText = ({ deviceType }: AnimatedHeroTextProps) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const [visibleLines, setVisibleLines] = useState<number[]>([]);
  const [animationPhase, setAnimationPhase] = useState<'building' | 'disappearing' | 'final'>('building');
  const [visibleWords, setVisibleWords] = useState<number[]>([]);
  
  const lines = [
    "Твоя стратегия",
    "Твой ход",
    "Твоя прибыль", 
    "Партия начинается здесь"
  ];

  // Разбиваем четвертую фразу на слова для анимации
  const finalPhraseWords = ["Партия", "начинается", "здесь"];


  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];
    
    // Фаза 1: Появление первых трех строк (собираются вместе)
    lines.slice(0, 3).forEach((_, index) => {
      const timeout = setTimeout(() => {
        setVisibleLines(prev => [...prev, index]);
      }, index * 1200); // 1200ms задержка между строками

      timeouts.push(timeout);
    });

    // Фаза 2: Появление финальной строки (без исчезновения первых трех)
    const finalTimeout = setTimeout(() => {
      setAnimationPhase('final');
      setVisibleLines(prev => [...prev, 3]); // Добавляем четвертую строку к существующим

      // Анимация слов в финальной фразе
      finalPhraseWords.forEach((_, wordIndex) => {
        const wordTimeout = setTimeout(() => {
          setVisibleWords(prev => [...prev, wordIndex]);
        }, wordIndex * 800); // 800ms задержка между словами

        timeouts.push(wordTimeout);
      });
    }, 3 * 1200 + 2000); // После появления всех трех + 2 секунды показа
    
    timeouts.push(finalTimeout);

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  const getLineStyles = (index: number) => {
    const isVisible = visibleLines.includes(index);
    const isLastLine = index === lines.length - 1;
    const isFinalPhrase = isLastLine;
    const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
    const isSmallMobile = deviceType === 'mobile-small';
    const isTablet = deviceType === 'tablet';

    // Определяем видимость в зависимости от фазы анимации
    let shouldShow = false;
    if (animationPhase === 'building') {
      shouldShow = isVisible && !isFinalPhrase; // Показываем только первые три
    } else if (animationPhase === 'final') {
      shouldShow = isVisible; // Показываем все видимые строки
    }
    
    // Дополнительная проверка: финальные строки должны быть скрыты в начальных фазах
    if (isFinalPhrase && animationPhase !== 'final') {
      shouldShow = false;
    }
    
    // Принудительно скрываем финальные строки если они не должны быть видны
    if (isFinalPhrase && !isVisible) {
      shouldShow = false;
    }

    // Базовые стили для анимации в шахматном порядке (строго по горизонтали) с 3D эффектами
    const baseStyles = {
      opacity: shouldShow ? 1 : 0,
      transform: shouldShow
        ? 'translateX(0) scale(1)'
        : index % 2 === 0 
          ? 'translateX(-50px) scale(0.95)' // Четные индексы (0,2) - "Твоя стратегия", "Твоя прибыль" - слева направо
          : 'translateX(50px) scale(0.95)', // Нечетные индексы (1) - "Твой ход" - справа налево
      transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)', // Более плавный переход
      marginBottom: isFinalPhrase ? 0 : (isMobile ? 25 : 30), // Расстояние между первыми тремя строками
      lineHeight: 1.2,
      fontWeight: isFinalPhrase ? 700 : 500,
      whiteSpace: 'nowrap' as const, // Все фразы в одну строку
      // Простые тени для объемного эффекта
      textShadow: isFinalPhrase
        ? '2px 2px 4px rgba(0,0,0,0.3), 4px 4px 8px rgba(0,0,0,0.2), 6px 6px 12px rgba(0,0,0,0.1), 0 0 20px rgba(139, 33, 254, 0.3)'
        : '1px 1px 2px rgba(0,0,0,0.2), 2px 2px 4px rgba(0,0,0,0.1), 3px 3px 6px rgba(0,0,0,0.05)',
      // Полностью скрываем финальные строки в начальных фазах
      ...(isFinalPhrase && animationPhase !== 'final' && { 
        display: 'none',
        opacity: 0,
        visibility: 'hidden' as const
      }),
    };

    // Размеры шрифта в зависимости от устройства и позиции (увеличенные размеры)
    let fontSize: number;
    if (isFinalPhrase) {
      // Финальная строка - немного уменьшенный размер для баланса
      fontSize = isSmallMobile ? 20 : isMobile ? 25 : isTablet ? 32 : 40;
    } else {
      // Первые три строки - немного меньше финальной
      fontSize = isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 30 : 38;
    }

    // Цвета из существующей палитры проекта
    const color = isFinalPhrase 
      ? '#8b21fe' // Фиолетовый акцент (как в оригинале)
      : isDarkMode 
        ? '#bdbdbd' // Серый для темной темы (как в оригинале)
        : '#666666'; // Серый для светлой темы (как в оригинале)

    return {
      ...baseStyles,
      fontSize,
      color,
      textAlign: 'left' as const, // Все фразы выровнены по левому краю
              // Специальное позиционирование для первых трех фраз - все выровнены по левому краю
              ...(!isFinalPhrase && {
                marginLeft: 0, // Все фразы выровнены по одной точке от левого края
        width: 'auto', // Автоматическая ширина
        maxWidth: 'none', // Убираем ограничение ширины
        display: 'block' as const, // Блочный элемент
        // Первая строка выше остальных
        ...(index === 0 && {
          marginTop: isMobile ? '-20px' : '-30px', // Поднимаем первую строку выше
        }),
      }),
      // Дополнительные эффекты для финальной строки (прозрачный как стекло с переливами и 3D)
      ...(isFinalPhrase && {
        letterSpacing: '0.5px',
        background: 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--secondary)) 25%, hsl(var(--accent)) 50%, hsl(var(--secondary)) 75%, hsl(var(--primary)) 100%)',
        backgroundSize: '200% 200%',
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        animation: 'gradientShift 4s ease-in-out infinite',
        opacity: 0.9,
        // Дополнительные эффекты для финальной фразы
                marginLeft: 0, // Финальная фраза тоже выровнена по левому краю
        width: '100%', // Полная ширина для использования всего доступного пространства
        maxWidth: 'none', // Убираем ограничение ширины
        display: 'block' as const, // Блочный элемент
                marginTop: isMobile ? '60px' : '80px', // Отступ сверху между 3-й и 4-й фразой
                marginBottom: isMobile ? '20px' : '30px', // Отступ снизу
      }),
    };
  };

  const renderLine = (line: string, index: number) => {
    const isLastLine = index === lines.length - 1;
    const isFinalPhrase = isLastLine;

    if (isFinalPhrase) {
      // Финальная строка - рендерим слова по отдельности с анимацией
      return (
        <>
          {finalPhraseWords.map((word, wordIndex) => {
            const isWordVisible = visibleWords.includes(wordIndex);
            return (
              <span
                key={wordIndex}
                style={{
                  opacity: isWordVisible ? 1 : 0,
                  transform: isWordVisible 
                    ? 'translateX(0) scale(1)' 
                    : 'translateX(20px) scale(0.9)',
                  transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                  display: 'inline-block',
                  marginRight: '8px'
                }}
              >
                {word}
              </span>
            );
          })}
        </>
      );
    } else {
      // Для первых трех строк выделяем "Твоя/Твой" фиолетовым, остальные слова - жемчужно-серым с градиентом
      const parts = line.split(' ');
      const firstWord = parts[0]; // "Твоя" или "Твой"
      const restWords = parts.slice(1).join(' ');

      return (
        <>
          <span style={{ color: 'hsl(var(--primary))' }}>{firstWord}</span>
          <span style={{
            background: 'linear-gradient(135deg, #e5e7eb 0%, #d1d5db 25%, #9ca3af 50%, #d1d5db 75%, #e5e7eb 100%)',
            backgroundSize: '200% 200%',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            animation: 'pearlShimmer 3s ease-in-out infinite'
          }}> {restWords}</span>
        </>
      );
    }
  };

  return (
    <>
      {/* CSS анимация для плавного переливания градиента */}
      <style jsx>{`
        @keyframes gradientShift {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
        
        @keyframes pearlShimmer {
          0% {
            background-position: 0% 50%;
            filter: brightness(1);
          }
          50% {
            background-position: 100% 50%;
            filter: brightness(1.2);
          }
          100% {
            background-position: 0% 50%;
            filter: brightness(1);
          }
        }
        
        
      `}</style>
      
      
              <div style={{
                display: 'block',
                width: '100%',
                maxWidth: 'none',
                margin: '0 auto',
                padding: '0 10px',
                minHeight: '300px',
                marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '90px' : '130px',
                marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '30px' : '60px',
              }}>
        {lines.map((line, index) => (
          <div
            key={index}
            style={getLineStyles(index)}
          >
            {renderLine(line, index)}
          </div>
        ))}
      </div>
    </>
  );
};
