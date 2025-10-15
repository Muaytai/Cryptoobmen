'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextProps {
  deviceType: string;
}

export const AnimatedHeroText = ({ deviceType }: AnimatedHeroTextProps) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const [visibleLines, setVisibleLines] = useState<number[]>([0, 1]); // Только первые две строки видны
  const [animationPhase, setAnimationPhase] = useState<'building' | 'disappearing' | 'final'>('building');
  const [visibleWords, setVisibleWords] = useState<number[]>([]);
  const [animatedLines, setAnimatedLines] = useState<number[]>([0, 1]); // Только первые две строки анимированы
  
  const lines = [
  "Инвестируй как гроссмейстер",
  "Получай от 10% годовых в USDT",
  "Твоя стратегия - твоя прибыль.",
  "Партия начинается здесь."
  ];

  // Разбиваем финальную фразу на слова для анимации
  const finalPhraseWords = ["Партия", "начинается", "здесь"];


  // Анимация появления строк
  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];
    
    // Третья строка появляется справа через 1500ms
    const thirdTimeout = setTimeout(() => {
      setVisibleLines(prev => [...prev, 2]);
      setAnimatedLines(prev => [...prev, 2]);
    }, 1500);
    timeouts.push(thirdTimeout);

    // Четвертая строка появляется в той же строке через 2500ms
    const fourthTimeout = setTimeout(() => {
      setAnimationPhase('final');
      setVisibleLines(prev => [...prev, 3]);
      setAnimatedLines(prev => [...prev, 3]);
    }, 2500);
    timeouts.push(fourthTimeout);

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  const getLineStyles = (index: number) => {
    const isVisible = visibleLines.includes(index);
    const isAnimated = animatedLines.includes(index);
    const isLastLine = index === lines.length - 1;
    const isFinalPhrase = isLastLine;
    const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
    const isSmallMobile = deviceType === 'mobile-small';
    const isTablet = deviceType === 'tablet';

    // Стили с анимацией
    const baseStyles = {
      opacity: isVisible ? 1 : 0,
      transform: isVisible 
        ? (index === 2 ? 'translateX(0)' : 'translateX(0) scale(1)')
        : (index === 2 ? 'translateX(100px)' : 'translateX(0) scale(0.95)'),
      transition: isVisible 
        ? 'opacity 0.6s ease-out, transform 0.6s ease-out'
        : 'opacity 0.3s ease-in, transform 0.3s ease-in',
      marginBottom: (() => {
        if (isFinalPhrase) return 0;
        if (index === 1) return isMobile ? 50 : 60; // Увеличиваем отступ после второй строки
        if (index === 2) return isMobile ? 8 : 12; // Увеличиваем отступ после третьей строки
        return isMobile ? 24 : 30;
      })(),
      lineHeight: 1.1,
      fontWeight: isFinalPhrase ? 600 : index === 0 ? 700 : 500,
      whiteSpace: 'nowrap' as const,
      // Простые тени для читаемости
      textShadow: isFinalPhrase
        ? isDarkMode 
          ? '0 2px 4px rgba(0,0,0,0.8), 0 0 10px rgba(124, 58, 237, 0.5)'
          : '0 2px 4px rgba(255,255,255,0.8), 0 0 10px rgba(124, 58, 237, 0.6)'
        : isDarkMode 
          ? '0 1px 2px rgba(0,0,0,0.5)'
          : '0 1px 2px rgba(255,255,255,0.5)',
    };

    // Размеры шрифта - возвращаем к предыдущему варианту
    let fontSize: number;
    if (isFinalPhrase) {
      fontSize = isSmallMobile ? 14 : isMobile ? 16 : isTablet ? 18 : 20;
    } else if (index === 0) {
      // Главный заголовок - самый крупный
      fontSize = isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 30 : 36;
    } else if (index === 1) {
      // Вторая строка - крупная, но меньше первой
      fontSize = isSmallMobile ? 18 : isMobile ? 20 : isTablet ? 24 : 28;
    } else {
      fontSize = isSmallMobile ? 12 : isMobile ? 14 : isTablet ? 16 : 18;
    }

    // Простые, четкие цвета для максимальной читаемости
    const color = isDarkMode 
      ? '#FFFFFF' // Чистый белый для темной темы
      : '#000000'; // Чистый черный для светлой темы

    return {
      ...baseStyles,
      fontSize,
      color,
      textAlign: 'left' as const,
      // Специальное позиционирование для первых трех фраз
      ...(!isFinalPhrase && {
        marginLeft: 0,
        width: 'auto',
        maxWidth: 'none',
        display: 'block' as const,
        ...(index === 0 && {
          marginTop: isMobile ? '-8px' : '-8px',
        }),
      }),
      // Простые эффекты для финальной строки
      ...(isFinalPhrase && {
        letterSpacing: '0.5px',
        color: isDarkMode ? '#FFFFFF' : '#FFFFFF', // Белый цвет
        marginLeft: 0,
        width: '100%',
        maxWidth: 'none',
        display: 'block' as const,
        marginTop: isMobile ? '32px' : '40px',
        marginBottom: isMobile ? '24px' : '32px',
        fontWeight: 600
      }),
      // Простой стиль для первой строки - без переходов
      ...(index === 0 && {
        color: isDarkMode ? '#FFFFFF' : '#000000',
        fontWeight: 700,
        transition: 'none' // Убираем переходы для предотвращения мигания
      }),
      // Простой стиль для второй строки - без переходов
      ...(index === 1 && {
        color: isDarkMode ? '#FFFFFF' : '#000000',
        fontWeight: 500,
        transition: 'none' // Убираем переходы для предотвращения мигания
      })
    };
  };

  const renderLine = (line: string, index: number) => {
    const isLastLine = index === lines.length - 1;
    const isFinalPhrase = isLastLine;

    if (isFinalPhrase) {
      // Финальная строка - рендерим полностью без анимации слов
      return <span>{line}</span>;
    } else {
      // Первая строка: акцент на слове "гроссмейстер"
      if (index === 0) {
        const first = 'Инвестируй как';
        const second = 'гроссмейстер';
        return (
          <>
            <span style={{ 
              color: isDarkMode ? '#FFFFFF' : '#000000',
              fontWeight: 600
            }}>{first}</span>{' '}
            <span style={{
              color: '#7C3AED',
              fontWeight: 700
            }}>{second}</span>
          </>
        );
      }

      // Вторая строка: выделяем "10%" и "USDT" крупнее
      if (index === 1) {
        const withTokens = line.replace('10%', '__TEN__').replace('USDT', '__USDT__');
        const tokens = withTokens.split(' ');
        return (
          <>
            {tokens.map((t, i) => {
              if (t.includes('__TEN__')) {
                return (
                  <span key={i} style={{
                    color: '#7C3AED',
                    fontWeight: 700,
                    fontSize: '1.1em'
                  }}>10%</span>
                );
              }
              if (t.includes('__USDT__')) {
                return (
                  <span key={i} style={{
                    padding: '2px 8px',
                    marginLeft: '6px',
                    borderRadius: '12px',
                    background: isDarkMode ? 'rgba(124, 58, 237, 0.2)' : 'rgba(124, 58, 237, 0.1)',
                    border: '1px solid #7C3AED',
                    color: '#7C3AED',
                    fontWeight: 600,
                    fontSize: '1.1em'
                  }}>USDT</span>
                );
              }
              return <span key={i} style={{ marginRight: '6px' }}>{t}</span>;
            })}
          </>
        );
      }

      // Третья строка: выделяем "ТВОЯ" и "ТВОЙ" большим шрифтом
      if (index === 2) {
        const parts = line.split(' - ');
        const firstPart = parts[0]; // "Твоя стратегия"
        const secondPart = parts[1]; // "твоя прибыль"
        
        return (
          <>
            <span style={{ 
              color: isDarkMode ? '#FFFFFF' : '#000000', // Правильный цвет для светлой темы
              fontWeight: 500,
              transition: 'none'
            }}>
              <span style={{ fontSize: '1.2em', fontWeight: 700, color: '#7C3AED' }}>ТВОЯ</span> стратегия
            </span>
            <span style={{ 
              color: isDarkMode ? '#FFFFFF' : '#000000', // Правильный цвет для светлой темы
              margin: '0 8px',
              transition: 'none'
            }}>-</span>
            <span style={{
              color: isDarkMode ? '#FFFFFF' : '#000000', // Правильный цвет для светлой темы
              fontWeight: 600,
              transition: 'none'
            }}>
              <span style={{ fontSize: '1.2em', fontWeight: 700, color: '#7C3AED' }}>ТВОЯ</span> прибыль.
            </span>
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
                minHeight: '200px', // Еще больше уменьшаем высоту рамки
                position: 'relative',
                marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '110px' : '140px', // Смещаем ниже
                marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '30px' : '60px',
                // Предотвращаем скачки при загрузке
                contain: 'layout style',
                willChange: 'auto'
              }}>
        {/* Многослойный фон с глубиной */}
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: isDarkMode 
            ? `
              radial-gradient(ellipse 1000px 500px at 0% 50%, rgba(124,58,237,0.12) 0%, transparent 70%),
              radial-gradient(ellipse 600px 300px at 20% 30%, rgba(168,85,247,0.06) 0%, transparent 60%),
              linear-gradient(135deg, rgba(124,58,237,0.04) 0%, transparent 50%)
            `
            : `
              radial-gradient(ellipse 1000px 500px at 0% 50%, rgba(124,58,237,0.08) 0%, transparent 70%),
              radial-gradient(ellipse 600px 300px at 20% 30%, rgba(168,85,247,0.04) 0%, transparent 60%),
              linear-gradient(135deg, rgba(124,58,237,0.03) 0%, transparent 50%)
            `,
          opacity: 1
        }} />
        
        {/* Дополнительный слой глубины */}
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: isDarkMode 
            ? `
              linear-gradient(180deg, rgba(0,0,0,0.02) 0%, transparent 30%),
              linear-gradient(90deg, rgba(124,58,237,0.01) 0%, transparent 100%)
            `
            : `
              linear-gradient(180deg, rgba(255,255,255,0.02) 0%, transparent 30%),
              linear-gradient(90deg, rgba(124,58,237,0.01) 0%, transparent 100%)
            `,
          opacity: 0.8
        }} />
        
        {/* Тонкие рамки слева и сверху - менее яркие */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: isDarkMode 
            ? 'linear-gradient(90deg, rgba(124,58,237,0.15) 0%, transparent 100%)'
            : 'linear-gradient(90deg, rgba(124,58,237,0.1) 0%, transparent 100%)',
          zIndex: 1
        }} />
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '1px',
          background: isDarkMode 
            ? 'linear-gradient(180deg, rgba(124,58,237,0.15) 0%, transparent 100%)'
            : 'linear-gradient(180deg, rgba(124,58,237,0.1) 0%, transparent 100%)',
          zIndex: 1
        }} />
        <div style={{ 
          position: 'relative', 
          zIndex: 1,
          // Фиксированная высота для предотвращения скачков
          minHeight: '180px', // Еще больше уменьшаем высоту внутреннего контейнера
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
          paddingTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? 8 : 12
        }}>
        {lines.map((line, index) => {
          if (index === 3) {
            // Четвертую строку рендерим внутри третьей — тут пропускаем
            return null;
          }
          if (index === 2) {
            // Комбинированная строка: третья + четвертая в одну линию
            const baseStyle = getLineStyles(index);
            return (
              <div key={index} style={{ ...baseStyle, whiteSpace: 'nowrap' }}>
                {renderLine(line, index)}
                <span
                  style={{
                    // Анимация справа налево для четвертой части
                    display: 'inline-block',
                    marginLeft: 18,
                    color: isDarkMode ? '#FFFFFF' : '#000000', // Правильный цвет для светлой темы
                    fontWeight: 600,
                    fontSize: '0.95em',
                    opacity: visibleLines.includes(3) ? 1 : 0,
                    transform: visibleLines.includes(3) ? 'translateX(0)' : 'translateX(50px)',
                    transition: 'opacity 0.6s ease-out, transform 0.6s ease-out'
                  }}
                >
                  {lines[3]}
                </span>
              </div>
            );
          }
          return (
            <div key={index} style={getLineStyles(index)}>
              {renderLine(line, index)}
            </div>
          );
        })}
        </div>
      </div>
    </>
  );
};
