'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextV2Props {
  deviceType: string;
}

export const AnimatedHeroTextV2 = ({ deviceType }: AnimatedHeroTextV2Props) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const [activePhrase, setActivePhrase] = useState<number>(0);
  const [hoveredWord, setHoveredWord] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  
  const phrases = [
    "Инвестируй с умом",
    "Получай от 10% годовых в USDT",
    "Лучшая стратегия – стабильный доход.",
    "Сделай верный ход."
  ];

  // Автоматическое переключение фраз
  useEffect(() => {
    if (!isVisible) return;
    
    const interval = setInterval(() => {
      setActivePhrase(prev => (prev + 1) % phrases.length);
    }, 3000); // Меняем фразу каждые 3 секунды

    return () => clearInterval(interval);
  }, [isVisible, phrases.length]);

  // Показываем компонент после загрузки
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
  const isSmallMobile = deviceType === 'mobile-small';
  const isTablet = deviceType === 'tablet';

  const getPhraseStyles = (index: number) => {
    const isActive = activePhrase === index;
    const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
    const isSmallMobile = deviceType === 'mobile-small';
    const isTablet = deviceType === 'tablet';

    return {
      position: 'absolute' as const,
      top: 0,
      left: 0,
      right: 0,
      opacity: isActive ? 1 : 0,
      transform: isActive ? 'translateY(0)' : 'translateY(20px)',
      transition: 'opacity 0.6s ease-in-out, transform 0.6s ease-in-out',
      fontSize: isSmallMobile ? 24 : isMobile ? 28 : isTablet ? 32 : 36,
      fontWeight: 600,
      lineHeight: 1.2,
      textAlign: 'left' as const,
      color: isDarkMode ? '#FFFFFF' : '#000000',
      textShadow: isDarkMode 
        ? '0 2px 4px rgba(0,0,0,0.8), 0 0 8px rgba(255,255,255,0.3)'
        : '0 2px 4px rgba(255,255,255,0.8), 0 0 8px rgba(0,0,0,0.3)',
      whiteSpace: 'nowrap' as const,
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      padding: '0 10px',
      marginBottom: isMobile ? 30 : 40,
      minHeight: isSmallMobile ? 30 : isMobile ? 35 : isTablet ? 40 : 45,
      display: 'flex',
      alignItems: 'center'
    };
  };

  const getWordStyles = (word: string, phraseIndex: number) => {
    const isHovered = hoveredWord === word;
    const isKeyWord = ['Инвестируй', 'Получай', '10%', 'USDT', 'стратегия', 'доход', 'ход'].includes(word);
    
    return {
      display: 'inline-block',
      marginRight: '6px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      transform: isHovered ? 'scale(1.1)' : 'scale(1)',
      color: isKeyWord 
        ? (isHovered ? '#7C3AED' : '#A855F7')
        : (isDarkMode ? '#FFFFFF' : '#000000'),
      textShadow: isKeyWord 
        ? (isHovered ? '0 0 15px rgba(124, 58, 237, 0.8)' : '0 0 10px rgba(168, 85, 247, 0.6)')
        : (isDarkMode 
          ? '0 2px 4px rgba(0,0,0,0.8), 0 0 8px rgba(255,255,255,0.3)'
          : '0 2px 4px rgba(255,255,255,0.8), 0 0 8px rgba(0,0,0,0.3)'),
      fontWeight: isKeyWord ? 700 : 600,
      padding: isHovered ? '2px 4px' : '0',
      borderRadius: isHovered ? '4px' : '0',
      background: isHovered 
        ? (isDarkMode ? 'rgba(124, 58, 237, 0.1)' : 'rgba(124, 58, 237, 0.05)')
        : 'transparent'
    };
  };

  const renderPhrase = (phrase: string, index: number) => {
    const words = phrase.split(' ');
    
    return (
      <div key={index} style={getPhraseStyles(index)}>
        {words.map((word, wordIndex) => (
          <span
            key={wordIndex}
            style={getWordStyles(word, index)}
            onMouseEnter={() => setHoveredWord(word)}
            onMouseLeave={() => setHoveredWord(null)}
            onClick={() => {
              // Интерактивность: клик по слову может менять фразу
              if (word === 'ход' || word === 'стратегия') {
                setActivePhrase((index + 1) % phrases.length);
              }
            }}
          >
            {word}
          </span>
        ))}
      </div>
    );
  };

  if (!isVisible) return null;

  return (
    <>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        
        @keyframes glow {
          0%, 100% { 
            text-shadow: 0 0 5px rgba(124, 58, 237, 0.3);
          }
          50% { 
            text-shadow: 0 0 20px rgba(124, 58, 237, 0.6), 0 0 30px rgba(124, 58, 237, 0.4);
          }
        }
        
        .interactive-text {
          animation: pulse 2s ease-in-out infinite;
        }
        
        .key-word {
          animation: glow 3s ease-in-out infinite;
        }
      `}</style>
      
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: 'none',
        minWidth: isMobile ? '100%' : isTablet ? '80%' : '70%',
        margin: '0 auto',
        padding: '0 20px',
        minHeight: isMobile ? 200 : 250,
        position: 'relative',
        marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '90px' : '120px',
        marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '30px' : '60px',
        contain: 'layout style',
        willChange: 'auto'
      }}>
        {/* Интерактивный фон */}
        <div style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          pointerEvents: 'none',
          background: isDarkMode 
            ? `
              radial-gradient(ellipse 800px 400px at 50% 50%, rgba(124,58,237,0.15) 0%, transparent 70%),
              linear-gradient(135deg, rgba(124,58,237,0.08) 0%, transparent 50%),
              linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 30%)
            `
            : `
              radial-gradient(ellipse 800px 400px at 50% 50%, rgba(124,58,237,0.1) 0%, transparent 70%),
              linear-gradient(135deg, rgba(124,58,237,0.05) 0%, transparent 50%),
              linear-gradient(180deg, rgba(255,255,255,0.2) 0%, transparent 30%)
            `,
          opacity: hoveredWord ? 1 : 0.6,
          transition: 'opacity 0.3s ease'
        }} />
        
        {/* Тонкие рамки */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: isDarkMode 
            ? 'linear-gradient(90deg, rgba(124,58,237,0.4) 0%, transparent 100%)'
            : 'linear-gradient(90deg, rgba(124,58,237,0.3) 0%, transparent 100%)',
          zIndex: 1
        }} />
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '1px',
          background: isDarkMode 
            ? 'linear-gradient(180deg, rgba(124,58,237,0.4) 0%, transparent 100%)'
            : 'linear-gradient(180deg, rgba(124,58,237,0.3) 0%, transparent 100%)',
          zIndex: 1
        }} />
        
        {/* Контейнер для фраз */}
        <div style={{ 
          position: 'relative', 
          zIndex: 2,
          minHeight: isMobile ? 180 : 220,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          paddingTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? 8 : 12
        }}>
          {phrases.map((phrase, index) => renderPhrase(phrase, index))}
        </div>
        
        {/* Индикатор активной фразы */}
        <div style={{
          position: 'absolute',
          bottom: 10,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 8,
          zIndex: 3
        }}>
          {phrases.map((_, index) => (
            <div
              key={index}
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: activePhrase === index 
                  ? '#7C3AED' 
                  : (isDarkMode ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.3)'),
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onClick={() => setActivePhrase(index)}
            />
          ))}
        </div>
      </div>
    </>
  );
};
