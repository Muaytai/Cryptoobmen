'use client';

import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextV5Props {
  deviceType: string;
}

export const AnimatedHeroTextV5 = ({ deviceType }: AnimatedHeroTextV5Props) => {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  
  const phrases = [
    "Инвестируй и выводи на счет",
    "Доход от 10% годовых в USDT",
    "Партия начинается здесь"
  ];

  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
  const isSmallMobile = deviceType === 'mobile-small';
  const isTablet = deviceType === 'tablet';

  const getPhraseStyles = (index: number) => {
    return {
      fontSize: index === 0 
        ? (isSmallMobile ? 18 : isMobile ? 20 : isTablet ? 24 : 28)
        : index === 1
        ? (isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 26)
        : (isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 26),
      fontWeight: isDarkMode ? 400 : 500,
      lineHeight: 1.2,
      textAlign: 'left' as const,
      color: isDarkMode ? '#FFFFFF' : '#666666',
      marginBottom: isMobile ? 8 : 12,
      padding: '8px 0',
      position: 'relative' as const,
      textShadow: isDarkMode 
        ? '0 2px 8px rgba(0,0,0,0.6)'
        : '0 2px 8px rgba(255,255,255,0.8)',
      letterSpacing: '0.02em'
    };
  };

  const renderPhrase = (phrase: string, index: number) => {
    return (
      <div key={index} style={getPhraseStyles(index)}>
        {phrase}
      </div>
    );
  };

  return (
    <div style={{
      position: 'relative',
      width: isMobile ? '100%' : isTablet ? '75%' : '65%',
      maxWidth: isMobile ? 'none' : isTablet ? '600px' : '700px',
      margin: '0 auto',
      padding: '20px 16px',
      minHeight: isMobile ? 140 : 160,
      marginTop: deviceType === 'mobile' || deviceType === 'mobile-small' ? '120px' : '140px',
      marginLeft: deviceType === 'mobile' || deviceType === 'mobile-small' ? '-5px' : '0px',
      background: 'transparent',
      borderRadius: '0',
      border: 'none',
      boxShadow: 'none',
      contain: 'layout style',
      willChange: 'auto'
    }}>
      
      {/* Фоновая глубина */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: isDarkMode 
          ? 'linear-gradient(135deg, rgba(17, 16, 20, 0.08) 0%, rgba(30, 27, 35, 0.04) 100%)'
          : 'linear-gradient(135deg, rgba(255, 255, 255, 0.005) 0%, rgba(248, 250, 252, 0.002) 100%)',
        borderRadius: '0',
        backdropFilter: 'blur(60px)',
        WebkitBackdropFilter: 'blur(60px)',
        zIndex: -1,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Дополнительная глубина */}
      <div style={{
        position: 'absolute',
        top: '-30px',
        left: '-30px',
        right: isMobile ? '-10px' : isTablet ? '-15px' : '-20px',
        bottom: '-30px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.06) 0%, transparent 70%)'
          : 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.003) 0%, transparent 70%)',
        borderRadius: '0',
        zIndex: -2,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Третья глубина */}
      <div style={{
        position: 'absolute',
        top: '-50px',
        left: '-50px',
        right: isMobile ? '-5px' : isTablet ? '-10px' : '-15px',
        bottom: '-50px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.1) 0%, transparent 80%)'
          : 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.003) 0%, transparent 80%)',
        borderRadius: '0',
        zIndex: -3,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Четвертая глубина - большой размытый ореол */}
      <div style={{
        position: 'absolute',
        top: '-80px',
        left: '-80px',
        right: isMobile ? '0px' : isTablet ? '-5px' : '-10px',
        bottom: '-80px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.08) 0%, transparent 90%)'
          : 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.003) 0%, transparent 90%)',
        borderRadius: '0',
        backdropFilter: 'blur(100px)',
        WebkitBackdropFilter: 'blur(100px)',
        zIndex: -4,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Пятая глубина - максимальный ореол */}
      <div style={{
        position: 'absolute',
        top: '-120px',
        left: '-120px',
        right: isMobile ? '0px' : isTablet ? '0px' : '-5px',
        bottom: '-120px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.15) 0%, transparent 95%)'
          : 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.003) 0%, transparent 95%)',
        borderRadius: '0',
        backdropFilter: 'blur(150px)',
        WebkitBackdropFilter: 'blur(150px)',
        zIndex: -5,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Шестая глубина - космическая бездна */}
      <div style={{
        position: 'absolute',
        top: '-180px',
        left: '-180px',
        right: isMobile ? '0px' : isTablet ? '0px' : '0px',
        bottom: '-180px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.12) 0%, transparent 98%)'
          : 'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.003) 0%, transparent 98%)',
        borderRadius: '0',
        backdropFilter: 'blur(200px)',
        WebkitBackdropFilter: 'blur(200px)',
        zIndex: -6,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Седьмая глубина - бесконечность */}
      <div style={{
        position: 'absolute',
        top: '-250px',
        left: '-250px',
        right: isMobile ? '0px' : isTablet ? '0px' : '0px',
        bottom: '-250px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.2) 0%, transparent 99%)'
          : 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.003) 0%, transparent 99%)',
        borderRadius: '0',
        backdropFilter: 'blur(300px)',
        WebkitBackdropFilter: 'blur(300px)',
        zIndex: -7,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Восьмая глубина - черная дыра */}
      <div style={{
        position: 'absolute',
        top: '-350px',
        left: '-350px',
        right: isMobile ? '0px' : isTablet ? '0px' : '0px',
        bottom: '-350px',
        background: isDarkMode 
          ? 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.25) 0%, transparent 99.5%)'
          : 'radial-gradient(ellipse at center, rgba(0, 0, 0, 0.003) 0%, transparent 99.5%)',
        borderRadius: '0',
        backdropFilter: 'blur(500px)',
        WebkitBackdropFilter: 'blur(500px)',
        zIndex: -8,
        transform: 'translateZ(0)',
        willChange: 'auto'
      }} />
      
      {/* Контейнер для фраз */}
      <div style={{ 
        position: 'relative',
        zIndex: 2,
        minHeight: isMobile ? 100 : 120,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        {phrases.map((phrase, index) => renderPhrase(phrase, index))}
      </div>
      
    </div>
  );
};
