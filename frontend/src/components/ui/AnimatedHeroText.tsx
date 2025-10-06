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
  "Инвестируй с умом",
  "Получай от 10% годовых в USDT",
  "Твоя стратегия - стабильный доход",
  "Партия начинается здесь"
  ];

  // Разбиваем финальную фразу на слова для анимации
  const finalPhraseWords = ["Партия", "начинается", "здесь"];


  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];
    
    // Фаза 1: Появление всех строк, кроме финальной
    const nonFinalCount = lines.length - 1;
    lines.slice(0, nonFinalCount).forEach((_, index) => {
      const timeout = setTimeout(() => {
        setVisibleLines(prev => [...prev, index]);
      }, index * 1200); // 1200ms задержка между строками

      timeouts.push(timeout);
    });

    // Фаза 2: Появление финальной строки (без исчезновения предыдущих)
    const finalTimeout = setTimeout(() => {
      setAnimationPhase('final');
      setVisibleLines(prev => [...prev, lines.length - 1]); // Добавляем финальную строку

      // Анимация слов в финальной фразе
      finalPhraseWords.forEach((_, wordIndex) => {
        const wordTimeout = setTimeout(() => {
          setVisibleWords(prev => [...prev, wordIndex]);
        }, wordIndex * 800); // 800ms задержка между словами

        timeouts.push(wordTimeout);
      });
    }, (nonFinalCount) * 1200 + 1200); // После появления первых строк + пауза
    
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
      // Индивидуальные отступы между строками
      marginBottom: (() => {
        if (isFinalPhrase) return 0;
        // после второй строки увеличиваем отступ ещё сильнее, после третьей — уменьшаем
        if (index === 1) return isMobile ? 34 : 46;
        if (index === 2) return isMobile ? 10 : 14;
        return isMobile ? 22 : 26;
      })(),
      lineHeight: 1.2,
      fontWeight: isFinalPhrase ? 700 : 600,
      whiteSpace: 'nowrap' as const, // Всегда в одну строку на всех устройствах
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
      // Малые поддерживающие строки (оба одинаковые)
      fontSize = isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 20 : 22;
    } else if (index === 0 || index === 1) {
      // Первые две строки — одинаковая крупность, немного уменьшена, чтобы помещалась в одну строку
      fontSize = isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 30 : 36;
    } else {
      fontSize = isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 20 : 22;
    }

    // Цвета из существующей палитры проекта
    const color = isFinalPhrase 
      ? '#8b21fe' // Акцент для финальной строки
      : isDarkMode 
        ? '#e5e5e5'
        : '#333333';

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
          marginTop: isMobile ? '-6px' : '-6px',
        }),
      }),
      // Дополнительные эффекты для финальной строки (прозрачный как стекло с переливами и 3D)
      ...(isFinalPhrase && {
        letterSpacing: '0.5px',
        background: 'linear-gradient(135deg, #e5e7eb 0%, #cfd2da 50%, #eef0f5 100%)',
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
                marginTop: isMobile ? '28px' : '36px', // Блок поддержки опущен ниже
                marginBottom: isMobile ? '20px' : '30px', // Отступ снизу
      }),
      // Чёткий стеклянный эффект для первой строки (без размытого свечения)
      ...(index === 0 && {
        background: 'linear-gradient(180deg, #ffffff 0%, #e6e6f1 40%, #a259ff 100%)',
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        WebkitTextStroke: isDarkMode ? '0.4px rgba(255,255,255,0.35)' : '0.4px rgba(0,0,0,0.25)',
        textShadow: '0 1px 0 rgba(255,255,255,0.25), 0 0 0 rgba(0,0,0,0)'
      }),
      // Чуть усилим вторую строку, чтобы визуально рифмовалась с первой
      ...(index === 1 && {
        color: isDarkMode ? '#f3f4f6' : '#222222'
      })
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
      // Первая строка: акцент на слове "ход"
      if (index === 0) {
        // Явно выводим полный текст: "Инвестируй с умом"
        const first = 'Инвестируй';
        const second = 'с умом';
        return (
          <>
            <span style={{ color: 'hsl(var(--primary))' }}>{first}</span>{' '}
            <span style={{
              background: 'linear-gradient(135deg, #e5e7eb 0%, #d1d5db 25%, #9ca3af 50%, #d1d5db 75%, #e5e7eb 100%)',
              backgroundSize: '200% 200%',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'pearlShimmer 3s ease-in-out infinite',
              fontSize: '0.9em',
              opacity: 0.95
            }}>{second}</span>
          </>
        );
      }

      // Вторая строка: выделяем "10%" и "USDT"
      if (index === 1) {
        const withTokens = line.replace('10%', '__TEN__').replace('USDT', '__USDT__');
        const tokens = withTokens.split(' ');
        return (
          <>
            {tokens.map((t, i) => {
              if (t.includes('__TEN__')) {
                return (
                  <span key={i} style={{
                    color: 'hsl(var(--primary))',
                    textShadow: '0 0 10px rgba(162,89,255,0.55)'
                  }}>10%</span>
                );
              }
              if (t.includes('__USDT__')) {
                return (
                  <span key={i} style={{
                    padding: '2px 8px',
                    marginLeft: '6px',
                    borderRadius: '999px',
                    background: isDarkMode ? 'rgba(162,89,255,0.12)' : 'rgba(162,89,255,0.12)',
                    border: '1px solid rgba(162,89,255,0.35)'
                  }}>USDT</span>
                );
              }
              return <span key={i} style={{ marginRight: '6px' }}>{t}</span>;
            })}
          </>
        );
      }

      // Дефолтный рендер для прочих строк
      return <span>{line}</span>;
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
                position: 'relative',
                marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '90px' : '120px',
                marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '30px' : '60px',
              }}>
        {/* Слой глубины позади текста: мягкая подсветка + тонкая сетка */}
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          backgroundImage: `
            radial-gradient(800px 260px at 0% 40%, rgba(162,89,255,0.18), rgba(162,89,255,0) 60%),
            linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)
          `,
          backgroundSize: 'auto, 28px 28px, 28px 28px',
          backgroundPosition: 'left center, left top, left top',
          opacity: isDarkMode ? 1 : 0.6,
          maskImage: 'linear-gradient(90deg, rgba(0,0,0,1) 0%, rgba(0,0,0,0.9) 75%, rgba(0,0,0,0.65) 100%)',
          WebkitMaskImage: 'linear-gradient(90deg, rgba(0,0,0,1) 0%, rgba(0,0,0,0.9) 75%, rgba(0,0,0,0.65) 100%)'
        }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
        {lines.map((line, index) => (
          <div
            key={index}
            style={getLineStyles(index)}
          >
            {renderLine(line, index)}
          </div>
        ))}
        </div>
      </div>
    </>
  );
};
