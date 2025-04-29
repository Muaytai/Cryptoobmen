'use client';

import Image from 'next/image';
import { SocialButtons } from '@/components/ui/SocialButtons';
import chessImage from '../../public/images/chess.png';
import { useEffect, useState, CSSProperties } from 'react';

export default function HomePage() {
  const [deviceType, setDeviceType] = useState('desktop');
  const [styleLoaded, setStyleLoaded] = useState(false);

  // Определяем тип устройства с более точной градацией
  useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      if (width < 480) {
        setDeviceType('mobile-small');
      } else if (width < 768) {
        setDeviceType('mobile');
      } else if (width < 1024) {
        setDeviceType('tablet');
      } else {
        setDeviceType('desktop');
      }
    };
    
    // Проверяем при загрузке
    checkDevice();
    
    // Проверяем при изменении размера окна
    window.addEventListener('resize', checkDevice);
    
    // Очищаем обработчики событий
    return () => window.removeEventListener('resize', checkDevice);
  }, []);

  // Добавляем стили для мобильной адаптации
  useEffect(() => {
    // Создаем стиль только один раз
    if (!styleLoaded) {
      const style = document.createElement('style');
      style.innerHTML = `
        @media (max-width: 480px) {
          h1 {
            font-size: 24px !important;
            word-break: break-word !important;
            white-space: normal !important;
            max-width: 100% !important;
          }
          h1 span {
            font-size: 24px !important;
            white-space: normal !important;
            word-break: break-word !important;
            display: inline !important;
          }
        }
        @media (min-width: 481px) and (max-width: 767px) {
          h1 {
            font-size: 28px !important;
            word-break: break-word !important;
            white-space: normal !important;
          }
          h1 span {
            font-size: 28px !important;
            white-space: normal !important;
            word-break: break-word !important;
            display: inline !important;
          }
        }
      `;
      document.head.appendChild(style);
      setStyleLoaded(true);
    }
  }, [styleLoaded]);

  // Функция для определения стилей в зависимости от устройства
  const getResponsiveStyles = () => {
    const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';
    const isSmallMobile = deviceType === 'mobile-small';
    const isTablet = deviceType === 'tablet';
    
    return {
      // Контейнер с основным контентом
      contentContainer: {
        display: 'flex',
        flexDirection: isMobile ? 'column' as const : 'row' as const,
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: 0,
        marginBottom: isMobile ? 15 : 20
      } as CSSProperties,
      
      // Левая колонка с текстом
      textContainer: {
        maxWidth: isMobile ? '100%' : isTablet ? '55%' : 600,
        zIndex: 2,
        position: 'relative' as const,
        textAlign: isMobile ? 'center' as const : 'left' as const,
        marginBottom: isMobile ? '30px' : 0,
        padding: isMobile ? '0 15px' : 0,
        width: isMobile ? '100%' : 'auto',
        overflowWrap: 'break-word' as const,
        wordWrap: 'break-word' as const
      } as CSSProperties,
      
      // Заголовок
      heading: {
        fontSize: isSmallMobile ? 24 : isMobile ? 28 : isTablet ? 40 : 60,
        fontWeight: 700,
        color: '#fff',
        marginBottom: isMobile ? 16 : 24,
        lineHeight: isMobile ? 1.3 : 1.2,
        maxWidth: '100%',
        wordBreak: isMobile ? 'break-word' as const : 'normal' as const,
        overflow: 'hidden'
      } as CSSProperties,
      
      // Span в заголовке для nowrap
      headingSpan: {
        whiteSpace: 'normal' as const,
        display: 'inline' as const,
        fontSize: isSmallMobile ? 24 : isMobile ? 28 : isTablet ? 40 : 60,
        wordBreak: 'break-word' as const,
        hyphens: 'auto' as const
      } as CSSProperties,
      
      // Span с выделенным цветом в заголовке
      headingColoredSpan: {
        color: '#b48afd',
        whiteSpace: 'normal' as const,
        display: 'inline' as const,
        fontSize: isSmallMobile ? 24 : isMobile ? 28 : isTablet ? 40 : 60,
        wordBreak: 'break-word' as const,
        hyphens: 'auto' as const
      } as CSSProperties,
      
      // Подзаголовок
      subtitle: {
        color: '#bdbdbd',
        fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 20 : 24,
        marginBottom: isMobile ? 30 : 48
      } as CSSProperties,
      
      // Контейнер для кнопок
      buttonContainer: {
        display: 'flex',
        flexDirection: isMobile ? 'column' as const : 'row' as const,
        alignItems: isMobile ? 'center' as const : 'flex-start' as const,
        gap: isMobile ? 12 : 20,
        width: isMobile ? '100%' : 'auto'
      } as CSSProperties,
      
      // Кнопка основного действия
      primaryButton: {
        background: '#a259ff',
        color: '#fff',
        border: 'none',
        borderRadius: 12,
        padding: isSmallMobile ? '10px 20px' : isMobile ? '12px 24px' : '16px 36px',
        fontWeight: 500,
        fontSize: isSmallMobile ? 14 : isMobile ? 16 : 18,
        cursor: 'pointer',
        transition: 'background 0.2s',
        width: isMobile ? '100%' : 'auto',
        marginBottom: isMobile ? '12px' : 0
      } as CSSProperties,
      
      // Кнопка дополнительного действия
      secondaryButton: {
        border: '1px solid #a259ff',
        color: '#fff',
        borderRadius: 12,
        padding: isSmallMobile ? '10px 20px' : isMobile ? '12px 24px' : '16px 36px',
        fontWeight: 500,
        fontSize: isSmallMobile ? 14 : isMobile ? 16 : 18,
        background: 'none',
        cursor: 'pointer',
        transition: 'background 0.2s',
        width: isMobile ? '100%' : 'auto'
      } as CSSProperties,
      
      // Контейнер для изображения
      imageContainer: {
        position: 'relative' as const,
        width: isMobile ? '100%' : isTablet ? 400 : 520,
        height: isSmallMobile ? 250 : isMobile ? 300 : isTablet ? 400 : 520,
        marginRight: isMobile ? 0 : isTablet ? 0 : -25,
        marginLeft: isMobile ? 0 : isTablet ? -50 : -150,
        marginTop: isMobile ? -20 : isTablet ? -10 : 30,
        alignSelf: 'flex-end' as const
      } as CSSProperties,
      
      // Стили для изображения
      image: {
        objectFit: 'contain' as const,
        borderRadius: 24,
        transform: isMobile 
          ? 'scale(1.1) translateX(-10px) translateY(10px)' 
          : isTablet 
            ? 'scale(1.2) translateX(-50px) translateY(20px)' 
            : 'scale(1.4) translateX(-100px) translateY(20px)'
      } as CSSProperties,
      
      // Пустой блок для отступа
      spacer: {
        flex: 1,
        minHeight: isSmallMobile ? 20 : isMobile ? 40 : isTablet ? 80 : 120
      } as CSSProperties,
      
      // Контейнер для крипто-иконок
      cryptoIconsContainer: {
        display: 'flex',
        justifyContent: 'center',
        padding: '0 15px',
        marginBottom: 80,
        overflow: 'hidden'
      } as CSSProperties,
      
      // Стили для крипто-иконок
      cryptoIcons: {
        objectFit: 'contain' as const,
        maxWidth: '100%',
        height: 'auto'
      } as CSSProperties,

      // Стили для контейнера кнопок соцсетей
      socialButtonsContainer: {
        position: 'fixed' as const,
        right: 20,
        top: '50%',
        transform: 'translateY(-50%)' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 15,
        zIndex: 100
      } as CSSProperties,

      // Стили для кнопок соцсетей
      socialButton: {
        width: 48,
        height: 48,
        borderRadius: 12,
        background: 'rgba(38, 38, 38, 0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        backdropFilter: 'blur(5px)' as const,
        WebkitBackdropFilter: 'blur(5px)' as const,
      } as CSSProperties,

      // Стили для изображений внутри кнопок
      socialButtonImage: {
        width: 24,
        height: 24
      } as CSSProperties
    };
  };

  const styles = getResponsiveStyles();
  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';

  return (
    <div className="relative h-full bg-[#111014]">
      <main style={{
        height: '100%',
        maxWidth: 1400, 
        margin: '0 auto',
        padding: '20px 5px 80px 5px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start'
      } as CSSProperties}>
        <div style={styles.contentContainer}>
          {/* Левая колонка */}
          <div style={styles.textContainer}>
            <h1 style={styles.heading}>
              <span style={styles.headingSpan}>Инвестируй и получай</span>{' '}
              <span style={styles.headingColoredSpan}>от 10% годовых в USDT</span>
            </h1>
            <div style={styles.subtitle}>
              Думай на шаг вперёд. Инвестируй с умом.<br />Твоя партия начинается здесь
            </div>
            <div style={styles.buttonContainer}>
              <button style={styles.primaryButton} 
                onMouseOver={e => {
                  const target = e.currentTarget.style as any;
                  target.background = '#8f3fff';
                }} 
                onMouseOut={e => {
                  const target = e.currentTarget.style as any;
                  target.background = '#a259ff';
                }}
              >
                Попробовать бесплатно
              </button>
              <button style={styles.secondaryButton} 
                onMouseOver={e => {
                  const target = e.currentTarget.style as any;
                  target.background = '#2a1a3a';
                }} 
                onMouseOut={e => {
                  const target = e.currentTarget.style as any;
                  target.background = 'none';
                }}
              >
                Узнать подробнее
              </button>
            </div>
          </div>
          {/* Правая колонка */}
          <div style={styles.imageContainer}>
            <Image
              src={chessImage}
              alt="Chess Strategy"
              fill
              style={styles.image}
              priority
            />
          </div>
        </div>
        
        {/* Пустой блок для создания пространства */}
        <div style={styles.spacer}></div>
        
        {/* Крипто-иконки снизу */}
        <div style={styles.cryptoIconsContainer}>
          <Image
            src="/images/crypt-ico.png"
            alt="Cryptocurrency Icons"
            width={850}
            height={70}
            style={styles.cryptoIcons}
          />
        </div>
        
        {/* Соц. кнопки справа */}
        {/* Скрыли стандартные кнопки: {!isMobile && <SocialButtons />} */}
        
        {/* Альтернативные кнопки соцсетей справа */}
        <div style={styles.socialButtonsContainer}>
          <a 
            href="https://t.me/your_channel" 
            target="_blank" 
            rel="noopener noreferrer"
            style={styles.socialButton}
            onMouseOver={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(180, 138, 253, 0.7)';
            }}
            onMouseOut={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(38, 38, 38, 0.4)';
            }}
          >
            <Image
              src="/images/Телеграм.png"
              alt="Telegram"
              width={24}
              height={24}
              style={styles.socialButtonImage}
            />
          </a>
          <a 
            href="https://instagram.com/your_profile" 
            target="_blank" 
            rel="noopener noreferrer"
            style={styles.socialButton}
            onMouseOver={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(180, 138, 253, 0.7)';
            }}
            onMouseOut={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(38, 38, 38, 0.4)';
            }}
          >
            <Image
              src="/images/Инста.png"
              alt="Instagram"
              width={24}
              height={24}
              style={styles.socialButtonImage}
            />
          </a>
        </div>
      </main>
    </div>
  );
}
