'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextV3Props {
  deviceType: string;
}

export const AnimatedHeroTextV3 = ({ deviceType }: AnimatedHeroTextV3Props) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const [currentPhrase, setCurrentPhrase] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);
  
  const phrases = [
    "Инвестируй с умом",
    "Получай от 10% годовых в USDT",
    "Лучшая стратегия – стабильный доход.",
    "Сделай верный ход."
  ];

  // Анимация появления фраз одна за другой
  useEffect(() => {
    if (!isLoaded) return;
    
    const interval = setInterval(() => {
      setCurrentPhrase(prev => (prev + 1) % phrases.length);
    }, 2500);

    return () => clearInterval(interval);
  }, [isLoaded, phrases.length]);

  // Показываем компонент после загрузки
  useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 300);
    return () => clearTimeout(timer);
  }, []);

  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
  const isSmallMobile = deviceType === 'mobile-small';
  const isTablet = deviceType === 'tablet';

  const getPhraseStyles = (index: number) => {
    const isActive = currentPhrase === index;
    const isVisible = isLoaded && isActive;
    
    return {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      opacity: isVisible ? 1 : 0,
      transform: isVisible 
        ? 'translateY(0) scale(1)' 
        : 'translateY(30px) scale(0.95)',
      transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
      fontSize: isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 28 : 32,
      fontWeight: 700,
      lineHeight: 1.1,
      textAlign: 'left' as const,
      color: isDarkMode ? '#FFFFFF' : '#000000',
      whiteSpace: 'nowrap' as const,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      padding: '0 20px',
      marginBottom: isMobile ? 25 : 35,
      minHeight: isSmallMobile ? 25 : isMobile ? 30 : isTablet ? 35 : 40,
      display: 'flex',
      alignItems: 'center',
      textShadow: isDarkMode 
        ? '0 3px 6px rgba(0,0,0,0.8), 0 0 12px rgba(255,255,255,0.2)'
        : '0 3px 6px rgba(255,255,255,0.8), 0 0 12px rgba(0,0,0,0.2)',
      filter: isVisible ? 'blur(0px)' : 'blur(2px)',
      zIndex: isVisible ? 10 : 1
    };
  };

  const renderPhrase = (phrase: string, index: number) => {
    const words = phrase.split(' ');
    const isActive = currentPhrase === index;
    
    return (
      <div key={index} style={getPhraseStyles(index)}>
        {words.map((word, wordIndex) => {
          const isKeyWord = ['Инвестируй', 'Получай', '10%', 'USDT', 'стратегия', 'доход', 'ход'].includes(word);
          const delay = wordIndex * 100; // Задержка для каждого слова
          
          return (
            <span
              key={wordIndex}
              style={{
                display: 'inline-block',
                marginRight: '8px',
                color: isKeyWord 
                  ? '#7C3AED'
                  : (isDarkMode ? '#FFFFFF' : '#000000'),
                fontWeight: isKeyWord ? 800 : 700,
                textShadow: isKeyWord 
                  ? '0 0 15px rgba(124, 58, 237, 0.6)'
                  : (isDarkMode 
                    ? '0 3px 6px rgba(0,0,0,0.8), 0 0 12px rgba(255,255,255,0.2)'
                    : '0 3px 6px rgba(255,255,255,0.8), 0 0 12px rgba(0,0,0,0.2)'),
                transform: isActive 
                  ? `translateY(0) scale(1)`
                  : `translateY(20px) scale(0.9)`,
                transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${delay}ms`,
                opacity: isActive ? 1 : 0.3
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    );
  };

  if (!isLoaded) return null;

  return (
    <>
      <style jsx>{`
        @keyframes depthPulse {
          0%, 100% { 
            transform: scale(1);
            filter: brightness(1);
          }
          50% { 
            transform: scale(1.02);
            filter: brightness(1.1);
          }
        }
        
        @keyframes floating {
          0%, 100% { 
            transform: translateY(0px);
          }
          50% { 
            transform: translateY(-5px);
          }
        }
        
        @keyframes glow {
          0%, 100% { 
            box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
          }
          50% { 
            box-shadow: 0 0 40px rgba(124, 58, 237, 0.6);
          }
        }
        
        .depth-container {
          animation: depthPulse 4s ease-in-out infinite;
        }
        
        .floating-bg {
          animation: floating 6s ease-in-out infinite;
        }
        
        .glow-border {
          animation: glow 3s ease-in-out infinite;
        }
      `}</style>
      
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: 'none',
        minWidth: isMobile ? '100%' : isTablet ? '85%' : '75%',
        margin: '0 auto',
        padding: '0 20px',
        minHeight: isMobile ? 180 : 220,
        marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '90px' : '120px',
        marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '30px' : '60px',
        contain: 'layout style',
        willChange: 'auto'
      }}>
        {/* Многослойный фон с глубиной */}
        <div className="depth-container" style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: isDarkMode 
            ? `
              radial-gradient(ellipse 1200px 600px at 30% 40%, rgba(124,58,237,0.2) 0%, transparent 60%),
              radial-gradient(ellipse 800px 400px at 70% 60%, rgba(168,85,247,0.15) 0%, transparent 50%),
              radial-gradient(ellipse 600px 300px at 50% 20%, rgba(139,92,246,0.1) 0%, transparent 40%),
              linear-gradient(135deg, rgba(124,58,237,0.08) 0%, transparent 50%),
              linear-gradient(45deg, rgba(0,0,0,0.4) 0%, transparent 30%)
            `
            : `
              radial-gradient(ellipse 1200px 600px at 30% 40%, rgba(124,58,237,0.15) 0%, transparent 60%),
              radial-gradient(ellipse 800px 400px at 70% 60%, rgba(168,85,247,0.1) 0%, transparent 50%),
              radial-gradient(ellipse 600px 300px at 50% 20%, rgba(139,92,246,0.08) 0%, transparent 40%),
              linear-gradient(135deg, rgba(124,58,237,0.05) 0%, transparent 50%),
              linear-gradient(45deg, rgba(255,255,255,0.3) 0%, transparent 30%)
            `,
          opacity: 1,
          borderRadius: '20px'
        }} />
        
        {/* Плавающий слой */}
        <div className="floating-bg" style={{
          position: 'absolute',
          inset: '10px',
          zIndex: 1,
          pointerEvents: 'none',
          background: isDarkMode 
            ? `
              linear-gradient(180deg, rgba(0,0,0,0.1) 0%, transparent 50%),
              linear-gradient(90deg, rgba(124,58,237,0.05) 0%, transparent 100%)
            `
            : `
              linear-gradient(180deg, rgba(255,255,255,0.1) 0%, transparent 50%),
              linear-gradient(90deg, rgba(124,58,237,0.03) 0%, transparent 100%)
            `,
          borderRadius: '15px',
          opacity: 0.8
        }} />
        
        {/* Светящиеся рамки */}
        <div className="glow-border" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: isDarkMode 
            ? 'linear-gradient(90deg, rgba(124,58,237,0.6) 0%, rgba(168,85,247,0.4) 50%, transparent 100%)'
            : 'linear-gradient(90deg, rgba(124,58,237,0.4) 0%, rgba(168,85,247,0.3) 50%, transparent 100%)',
          zIndex: 2,
          borderRadius: '1px'
        }} />
        <div className="glow-border" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '2px',
          background: isDarkMode 
            ? 'linear-gradient(180deg, rgba(124,58,237,0.6) 0%, rgba(168,85,247,0.4) 50%, transparent 100%)'
            : 'linear-gradient(180deg, rgba(124,58,237,0.4) 0%, rgba(168,85,247,0.3) 50%, transparent 100%)',
          zIndex: 2,
          borderRadius: '1px'
        }} />
        
        {/* Контейнер для фраз */}
        <div style={{ 
          position: 'relative', 
          zIndex: 3,
          minHeight: isMobile ? 160 : 200,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          paddingTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? 10 : 15
        }}>
          {phrases.map((phrase, index) => renderPhrase(phrase, index))}
        </div>
        
        {/* Индикатор прогресса */}
        <div style={{
          position: 'absolute',
          bottom: 15,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 10,
          zIndex: 4
        }}>
          {phrases.map((_, index) => (
            <div
              key={index}
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: currentPhrase === index 
                  ? '#7C3AED' 
                  : (isDarkMode ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)'),
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                boxShadow: currentPhrase === index 
                  ? '0 0 10px rgba(124, 58, 237, 0.5)'
                  : 'none'
              }}
              onClick={() => setCurrentPhrase(index)}
            />
          ))}
        </div>
      </div>
    </>
  );
};
