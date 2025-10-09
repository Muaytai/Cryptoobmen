'use client';

import { useEffect, useState } from 'react';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextV4Props {
  deviceType: string;
}

export const AnimatedHeroTextV4 = ({ deviceType }: AnimatedHeroTextV4Props) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const [visiblePhrases, setVisiblePhrases] = useState<number[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const phrases = [
    "Инвестируй с умом",
    "Получай от 10% годовых в USDT",
    "Лучшая стратегия – стабильный доход.",
    "Сделай верный ход."
  ];

  // Последовательное появление фраз
  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];
    
    phrases.forEach((_, index) => {
      const timeout = setTimeout(() => {
        setVisiblePhrases(prev => [...prev, index]);
      }, index * 800 + 500); // Задержка между фразами
      timeouts.push(timeout);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
  const isSmallMobile = deviceType === 'mobile-small';
  const isTablet = deviceType === 'tablet';

  const getPhraseStyles = (index: number) => {
    const isVisible = visiblePhrases.includes(index);
    const isLeft = index % 2 === 0; // Четные индексы слева, нечетные справа
    
    return {
      opacity: isVisible ? 1 : 0,
      transform: isVisible 
        ? 'translateX(0) translateY(0)' 
        : isLeft 
          ? 'translateX(-20px) translateY(20px)'
          : 'translateX(80px) translateY(20px)',
      transition: 'all 0.7s ease-out',
      fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 20 : 22,
      fontWeight: index === 0 ? 800 : index === 1 ? 700 : 600,
      lineHeight: 1.3,
      textAlign: 'left' as const,
      color: isDarkMode ? '#FFFFFF' : '#000000',
      marginBottom: isMobile ? 8 : 12,
      padding: '4px 0',
      position: 'relative' as const,
      textShadow: isDarkMode 
        ? '0 2px 4px rgba(0,0,0,0.5)'
        : '0 2px 4px rgba(255,255,255,0.5)'
    };
  };

  const renderPhrase = (phrase: string, index: number) => {
    // Убираем точки из фраз
    const cleanPhrase = phrase.replace(/\.$/, '');
    const words = cleanPhrase.split(' ');
    const isVisible = visiblePhrases.includes(index);
    
    return (
      <div key={index} style={getPhraseStyles(index)}>
        {words.map((word, wordIndex) => {
          const isKeyWord = ['Инвестируй', 'Получай', '10%', 'USDT', 'Сделай'].includes(word);
          const isThirdPhrase = index === 2; // "Лучшая стратегия – стабильный доход"
          const wordDelay = wordIndex * 100;
          
          return (
            <span
              key={wordIndex}
              style={{
                display: 'inline-block',
                marginRight: '6px',
                color: isKeyWord 
                  ? (index === 0 ? '#7C3AED' : index === 1 ? '#A855F7' : index === 3 ? '#7C3AED' : '#8B5CF6')
                  : isThirdPhrase 
                    ? (isDarkMode ? '#FFFFFF' : '#000000') // Третья фраза полностью белая
                    : (isDarkMode ? '#FFFFFF' : '#000000'),
                fontWeight: isKeyWord ? 800 : (index === 0 ? 800 : index === 1 ? 700 : 600),
                transform: isVisible 
                  ? 'translateY(0) scale(1)'
                  : 'translateY(10px) scale(0.95)',
                transition: `all 0.5s ease-out ${wordDelay}ms`,
                opacity: isVisible ? 1 : 0.7
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div style={{
      position: 'relative',
      width: isMobile ? '100%' : isTablet ? '70%' : '60%',
      maxWidth: isMobile ? 'none' : isTablet ? '500px' : '600px',
      margin: '0 auto',
      padding: '15px 12px',
      minHeight: isMobile ? 120 : 140,
      marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '80px' : '100px',
      marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '20px' : '40px',
      background: isDarkMode 
        ? 'rgba(17, 16, 20, 0.1)'
        : 'rgba(255, 255, 255, 0.1)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderRadius: '12px',
      border: 'none',
      border: isDarkMode 
        ? '1px solid rgba(124, 58, 237, 0.2)'
        : '1px solid rgba(124, 58, 237, 0.15)',
      boxShadow: isDarkMode 
        ? '0 8px 32px rgba(0, 0, 0, 0.3), 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        : '0 8px 32px rgba(0, 0, 0, 0.15), 0 2px 8px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
      contain: 'layout style',
      willChange: 'auto'
    }}>
      
      {/* Контейнер для фраз */}
      <div style={{ 
        position: 'relative',
        zIndex: 2,
        minHeight: isMobile ? 80 : 100,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        {phrases.map((phrase, index) => renderPhrase(phrase, index))}
      </div>
      
    </div>
  );
};
