'use client';

import Image from 'next/image';
import chessImage from '../../public/images/chess.png';
import { useEffect, useState, CSSProperties, Suspense } from 'react';
import { useTheme } from '@/lib/ThemeProvider';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { AnimatedHeroText } from '@/components/ui/AnimatedHeroText';

// Простое модальное окно (вам нужно будет стилизовать его)
const EmailConfirmedModal = ({ onClose }: { onClose: () => void }) => {
  const { user } = useAuthStore();
  const router = useRouter();

  const handleGoToLogin = () => {
    onClose();
    router.push('/login?redirect=profile');
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', 
      alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: '#2d2c3a',
        color: 'white', 
        padding: '30px', borderRadius: '12px', textAlign: 'center', 
        maxWidth: '400px', width: '100%'
      }}>
        <h2 style={{ fontSize: '24px', marginBottom: '15px' }}>Регистрация успешна!</h2>
        <p style={{ marginBottom: '10px' }}>
          {user?.username || 'Ваш email'}, ваш адрес электронной почты был успешно подтвержден.
        </p>
        <p style={{ marginBottom: '25px' }}>Добро пожаловать на платформу!</p>
        <button 
          onClick={handleGoToLogin} 
          style={{
            background: '#A259FF', color: '#fff', padding: '10px 20px', 
            border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '16px'
          }}
        >
          Войти
        </button>
      </div>
    </div>
  );
};

// Компонент с использованием useSearchParams
const HomePageContent = () => {
  const searchParams = useSearchParams();
  const showEmailConfirmedModal = useAuthStore((state) => state.showEmailConfirmedModal);
  const setShowEmailConfirmedModal = useAuthStore((state) => state.setShowEmailConfirmedModal);
  const checkAuthStatus = useAuthStore((state) => state.checkAuthStatus);

  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';

  const buildStyles = (
    device: 'mobile-small' | 'mobile' | 'tablet' | 'desktop',
    isDark: boolean
  ): Record<string, CSSProperties> => {
    const isMobile = device === 'mobile' || device === 'mobile-small';
    const isSmallMobile = device === 'mobile-small';
    const isTablet = device === 'tablet';
    const isFirefox = typeof navigator !== 'undefined' && /firefox/i.test(navigator.userAgent);

    return {
      contentContainer: {
        display: 'flex',
        flexDirection: isMobile ? 'column' as const : 'row' as const,
        justifyContent: 'flex-start',
        alignItems: isMobile ? 'center' : 'flex-start',
        gap: isMobile ? 20 : 40,
        marginBottom: isMobile ? 15 : 20,
        minHeight: isMobile ? 'auto' : isTablet ? 400 : 500,
        height: isMobile ? 'auto' : isTablet ? 400 : 500,
        width: '100%',
        position: 'relative' as const,
        padding: isMobile ? '0 16px' : 0
      } as CSSProperties,

      textContainer: {
        maxWidth: '100%',
        zIndex: 2,
        position: 'relative' as const,
        textAlign: isMobile ? 'center' as const : 'left' as const,
        marginBottom: isMobile ? '20px' : 0,
        marginLeft: 0,
        padding: isMobile ? '0' : '0 20px',
        width: isMobile ? '100%' : isTablet ? '55%' : '50%',
        overflowWrap: 'break-word' as const,
        wordWrap: 'break-word' as const,
        minHeight: isMobile ? 'auto' : isTablet ? 240 : 300
      } as CSSProperties,

      imageContainer: {
        position: 'relative' as const,
        width: isMobile ? '100%' : isTablet ? '45%' : '50%',
        height: isSmallMobile ? 200 : isMobile ? 250 : isTablet ? 350 : 450,
        marginRight: isMobile ? 0 : isTablet ? 10 : 24,
        marginLeft: isMobile ? 0 : isTablet ? -20 : -28,
        marginTop: isMobile ? 0 : isTablet ? -10 : 30,
        alignSelf: isMobile ? 'center' : 'flex-end' as const,
        minHeight: isSmallMobile ? 200 : isMobile ? 250 : isTablet ? 350 : 450,
        maxWidth: isMobile ? '100%' : 'none'
      } as CSSProperties,

      image: {
        objectFit: 'contain' as const,
        borderRadius: 24,
        transform: isMobile
          ? 'scale(1)'
          : isTablet
            ? 'scale(1.1) translateX(-20px) translateY(10px)'
            : 'scale(1.2) translateX(-40px) translateY(20px)'
      } as CSSProperties,

      spacer: {
        flex: 0,
        height: isMobile ? '20px' : isTablet ? '60px' : 'clamp(200px, 40vh, 400px)'
      } as CSSProperties,

      cryptoIconsContainer: {
        display: 'flex',
        justifyContent: 'center',
        padding: '0 15px',
        marginTop: isMobile ? 20 : 40,
        marginBottom: isFirefox ? 100 : 80,
        overflow: 'hidden',
        minHeight: isMobile ? 50 : 70,
        height: isMobile ? 50 : 70,
        width: '100%',
        position: 'relative' as const,
        contain: 'layout paint size' as any
      } as CSSProperties,

      cryptoIcons: {
        objectFit: 'contain' as const,
        maxWidth: '100%',
        height: 'auto',
        width: isMobile ? '100%' : 'auto'
      } as CSSProperties,

      bottomSpacer: {
        width: '100%',
        minHeight: isFirefox
          ? (isSmallMobile ? 60 : isMobile ? 80 : isTablet ? 120 : 160)
          : (isSmallMobile ? 30 : isMobile ? 50 : isTablet ? 80 : 100)
      } as CSSProperties,

      socialButtonsContainer: {
        position: 'fixed' as const,
        right: isMobile ? 8 : isTablet ? 10 : 12,
        top: isMobile ? 200 : isTablet ? 200 : 220,
        transform: 'none' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        gap: 12,
        zIndex: 100,
        width: isMobile ? 40 : 48,
        height: 'auto'
      } as CSSProperties,

      socialButton: {
        width: isMobile ? 40 : 48,
        height: isMobile ? 40 : 48,
        borderRadius: 10,
        background: isDark ? 'rgba(38, 38, 38, 0.6)' : 'rgba(230, 230, 230, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        backdropFilter: 'blur(5px)' as const,
        WebkitBackdropFilter: 'blur(5px)' as const
      } as CSSProperties,

      socialButtonImage: { 
        width: isMobile ? 20 : 24, 
        height: isMobile ? 20 : 24 
      } as CSSProperties
    };
  };

  const [deviceType, setDeviceType] = useState<'mobile-small' | 'mobile' | 'tablet' | 'desktop'>(() => {
    if (typeof window === 'undefined') return 'desktop';
    const w = window.innerWidth;
    if (w < 480) return 'mobile-small';
    if (w < 768) return 'mobile';
    if (w < 1024) return 'tablet';
    return 'desktop';
  });
  const [isHydrated, setIsHydrated] = useState(false);
  const [styles, setStyles] = useState<Record<string, CSSProperties>>(() => {
    const w = typeof window === 'undefined' ? 1200 : window.innerWidth;
    const initialDevice = w < 480 ? 'mobile-small' : w < 768 ? 'mobile' : w < 1024 ? 'tablet' : 'desktop';
    return buildStyles(initialDevice, isDarkMode);
  });

  useEffect(() => {
    checkAuthStatus();

    const emailConfirmed = searchParams.get('email_confirmed');
    if (emailConfirmed === 'true') {
      setShowEmailConfirmedModal(true);
    }
  }, [searchParams, setShowEmailConfirmedModal, checkAuthStatus]);

  useEffect(() => {
    setIsHydrated(true);
    
    const preventJumpCSS = `
      html { 
        overflow-y: scroll !important; 
        scrollbar-gutter: stable both-edges !important; 
        height: 100% !important;
      }
      body { 
        height: 100vh !important; 
        min-height: 100vh !important; 
        overflow-y: auto !important;
        margin: 0 !important;
        padding: 0 !important;
      }
    `;
    
    const style = document.createElement('style');
    style.textContent = preventJumpCSS;
    style.setAttribute('data-prevent-jump', 'true');
    document.head.appendChild(style);
    
    return () => {
      const existingStyle = document.querySelector('style[data-prevent-jump="true"]');
      if (existingStyle) {
        existingStyle.remove();
      }
    };
  }, []);

  useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      let nextDevice: 'mobile-small' | 'mobile' | 'tablet' | 'desktop';
      if (width < 480) nextDevice = 'mobile-small';
      else if (width < 768) nextDevice = 'mobile';
      else if (width < 1024) nextDevice = 'tablet';
      else nextDevice = 'desktop';

      setDeviceType(nextDevice);
      setStyles(buildStyles(nextDevice, isDarkMode));
    };
    
    checkDevice();
    window.addEventListener('resize', checkDevice);
    return () => window.removeEventListener('resize', checkDevice);
  }, [isDarkMode]);

  const currentStyles = styles;
  const isMobile = deviceType === 'mobile' || deviceType === 'mobile-small';

  return (
    <div 
      className={`relative min-h-screen prevent-layout-shift ${isDarkMode ? 'bg-[#111014]' : 'bg-white'}`} 
      style={{ 
        contain: 'layout style', 
        willChange: 'auto',
        position: 'relative',
        overflowX: 'hidden'
      }} 
      data-hydrated={isHydrated}
    >
      <main className="stable-container" style={{
        minHeight: '100vh',
        maxWidth: 1400, 
        margin: '0 auto',
        padding: isMobile ? '16px 0 60px 0' : '20px 32px 80px 0px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        backgroundColor: isDarkMode ? '#111014' : 'white',
        contain: 'layout style',
        color: isDarkMode ? 'white' : '#111827',
        position: 'relative',
        willChange: 'auto'
      } as CSSProperties}>
        {showEmailConfirmedModal && <EmailConfirmedModal onClose={() => setShowEmailConfirmedModal(false)} />}
        
        <div className="stable-container" style={currentStyles.contentContainer}>
          {/* Левая колонка - текст */}
          <div className="stable-container" style={currentStyles.textContainer}>
            <AnimatedHeroText deviceType={deviceType} />
          </div>
          
          {/* Правая колонка - изображение */}
          <div className="stable-container" style={currentStyles.imageContainer}>
            <Image
              src={chessImage}
              alt="Chess Strategy"
              fill
              style={currentStyles.image}
              priority
              sizes="(max-width: 480px) 100vw, (max-width: 768px) 100vw, (max-width: 1024px) 45vw, 50vw"
            />
          </div>
        </div>
        
        {/* Соц. кнопки */}
        <div style={currentStyles.socialButtonsContainer} data-fixed>
          <a 
            href="https://t.me/your_channel" 
            target="_blank" 
            rel="noopener noreferrer"
            style={currentStyles.socialButton}
            onMouseOver={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(180, 138, 253, 0.7)';
            }}
            onMouseOut={e => {
              const target = e.currentTarget.style as any;
              target.background = isDarkMode ? 'rgba(38, 38, 38, 0.6)' : 'rgba(230, 230, 230, 0.8)';
            }}
          >
            <Image
              src="/images/Телеграм.png"
              alt="Telegram"
              width={24}
              height={24}
              style={currentStyles.socialButtonImage}
            />
          </a>
          <a 
            href="https://instagram.com/your_profile" 
            target="_blank" 
            rel="noopener noreferrer"
            style={currentStyles.socialButton}
            onMouseOver={e => {
              const target = e.currentTarget.style as any;
              target.background = 'rgba(180, 138, 253, 0.7)';
            }}
            onMouseOut={e => {
              const target = e.currentTarget.style as any;
              target.background = isDarkMode ? 'rgba(38, 38, 38, 0.6)' : 'rgba(230, 230, 230, 0.8)';
            }}
          >
            <Image
              src="/images/Инста.png"
              alt="Instagram"
              width={24}
              height={24}
              style={currentStyles.socialButtonImage}
            />
          </a>
        </div>
        
        {/* Пустой блок для создания пространства */}
        <div style={currentStyles.spacer}></div>
        
        {/* Крипто-иконки снизу */}
        <div className="stable-container" style={currentStyles.cryptoIconsContainer}>
          <Image
            src="/images/crypt-ico.png"
            alt="Cryptocurrency Icons"
            width={850}
            height={70}
            style={currentStyles.cryptoIcons}
            sizes="(max-width: 768px) 100vw, 850px"
          />
        </div>
        
        {/* Дополнительный отступ перед футером */}
        <div style={currentStyles.bottomSpacer} />
      </main>
    </div>
  );
};

// Основной компонент
export default function HomePage() {
  return (
    <Suspense fallback={
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#111014',
        color: 'white'
      }}>
        Загрузка...
      </div>
    }>
      <HomePageContent />
    </Suspense>
  );
}
