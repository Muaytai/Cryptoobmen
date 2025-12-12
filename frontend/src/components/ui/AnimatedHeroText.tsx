'use client';

import { CSSProperties, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/lib/ThemeProvider';

interface AnimatedHeroTextProps {
  deviceType: 'mobile-small' | 'mobile' | 'tablet' | 'desktop';
}

// Вариант A — «Кинетическая доска»
export const AnimatedHeroText = ({ deviceType }: AnimatedHeroTextProps) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const router = useRouter();

  const isSmallMobile = deviceType === 'mobile-small';
  const isMobile = deviceType === 'mobile' || isSmallMobile;
  const isTablet = deviceType === 'tablet';

  // Тайминги анимации строк (каскад с лёгким overshoot)
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const colors = useMemo(() => ({
    fg: isDark ? '#FFFFFF' : '#0A0A0A',
    muted: isDark ? 'rgba(255,255,255,0.72)' : '#4B5563',
    accent: '#7C3AED',
    accentHover: '#9333EA',
    bgA: isDark
      ? 'linear-gradient(135deg, rgba(17,16,20,0.08) 0%, rgba(30,27,35,0.04) 100%)'
      : 'linear-gradient(135deg, rgba(255,255,255,0.005) 0%, rgba(248,250,252,0.002) 100%)',
    depthRadialSoft: isDark
      ? 'radial-gradient(ellipse at center, rgba(124,58,237,0.06) 0%, transparent 70%)'
      : 'radial-gradient(ellipse at center, rgba(124,58,237,0.02) 0%, transparent 70%)',
  }), [isDark]);

  const container: CSSProperties = {
    position: 'relative',
    width: isMobile ? '100%' : isTablet ? '75%' : '65%',
    maxWidth: isMobile ? 'none' : isTablet ? 660 : 760,
    margin: '0 auto',
    // Сместим заметно правее
    marginLeft: isMobile ? '4px' : isTablet ? '12px' : '20px',
    marginTop: isMobile ? '20px' : isTablet ? '30px' : '40px',
    padding: isMobile ? '8px 12px' : '16px 16px',
    background: 'transparent',
    contain: 'layout style',
    willChange: 'auto',
  };

  const phraseBase: CSSProperties = {
    color: colors.fg,
    textAlign: 'left',
    lineHeight: 1.18,
    letterSpacing: '0.01em',
    marginBottom: isMobile ? 6 : 10,
    transform: mounted ? 'translateY(0px)' : 'translateY(10px)',
    opacity: mounted ? 1 : 0,
    transition: 'opacity 1000ms ease, transform 1000ms cubic-bezier(.2,.9,.2,1.2)',
    textShadow: isDark ? '0 2px 8px rgba(0,0,0,0.55)' : '0 2px 8px rgba(255,255,255,0.6)',
  };

  const phrase1: CSSProperties = {
    ...phraseBase,
    fontWeight: 700,
    fontSize: isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 32 : 42,
    transitionDelay: '0ms',
  };
  const phrase2: CSSProperties = {
    ...phraseBase,
    fontWeight: 700,
    fontSize: isSmallMobile ? 20 : isMobile ? 24 : isTablet ? 32 : 42,
    transitionDelay: '200ms',
  };
  const phrase3: CSSProperties = {
    ...phraseBase,
    fontWeight: 400,
    fontSize: isSmallMobile ? 18 : isMobile ? 20 : isTablet ? 26 : 32,
    transitionDelay: '400ms',
    whiteSpace: isMobile ? 'normal' : 'nowrap',
  };
  const strongAccent: CSSProperties = { color: colors.accent };
  // Третья строка — немного мельче
  const phrase3Title: CSSProperties = {
    ...phraseBase,
    fontWeight: 600,
    fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 26,
    transitionDelay: '400ms',
  };
  const phrase4: CSSProperties = {
    ...phraseBase,
    fontWeight: 400,
    fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 24,
    transitionDelay: '800ms',
  };
  // Пятая и шестая строки — отделяем увеличенным промежутком и паузой
  const phrase5: CSSProperties = {
    ...phraseBase,
    fontWeight: 400,
    fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 24,
    color: colors.muted,
    marginTop: isMobile ? 16 : 22,
    transitionDelay: '1200ms',
  };
  const phrase6: CSSProperties = {
    ...phraseBase,
    fontWeight: 400,
    fontSize: isSmallMobile ? 16 : isMobile ? 18 : isTablet ? 22 : 24,
    transitionDelay: '1500ms',
  };

  const btnRow: CSSProperties = {
    display: 'flex',
    gap: isMobile ? 10 : 14,
    marginTop: isSmallMobile ? 60 : isMobile ? 64 : isTablet ? 72 : 80,
    flexWrap: 'nowrap',
    // Появление кнопок после текста
    opacity: mounted ? 1 : 0,
    transform: mounted ? 'translateY(0)' : 'translateY(8px)',
    transition: 'opacity 600ms ease 900ms, transform 600ms ease 900ms',
  };

  const btnBase: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: isMobile ? '10px 18px' : '12px 26px',
    borderRadius: 9999,
    fontWeight: 600,
    fontSize: isMobile ? 14 : 16,
    cursor: 'pointer',
    transition: 'all .25s ease',
    border: `1px solid ${colors.accent}`,
    background: 'transparent',
    color: colors.accent,
    boxShadow: isDark ? 'inset 0 0 0 0 rgba(124,58,237,0.2)' : 'inset 0 0 0 0 rgba(124,58,237,0.12)',
    whiteSpace: 'nowrap',
  };
  const btnPrimary: CSSProperties = {
    ...btnBase,
    background: 'rgba(124,58,237,0.14)',
  };

  const handleRegister = () => router.push('/register');
  const handleAbout = () => router.push('/about');

  // Лёгкая интерактивность слов при наведении без сдвигов макета
  const renderInteractiveLine = (
    text: string,
    lineStyle: CSSProperties,
    highlightWords: string[] = []
  ) => {
    const words = text.split(' ');
    return (
      <div style={lineStyle}>
        {words.map((word, idx) => {
          const isHighlight = highlightWords.includes(word);
          const base: CSSProperties = {
            display: 'inline-block',
            marginRight: idx === words.length - 1 ? 0 : 6,
            transition: 'transform 220ms ease, text-shadow 220ms ease, color 220ms ease',
            transform: 'scale(1)',
            transformOrigin: 'left bottom',
            color: isHighlight ? colors.accent : undefined,
            textShadow: 'none',
            willChange: 'transform, text-shadow, color',
          };
          return (
            <span
              key={`${word}-${idx}`}
              style={base}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.04)';
                e.currentTarget.style.textShadow = isDark
                  ? '0 0 10px rgba(124,58,237,0.35)'
                  : '0 0 10px rgba(124,58,237,0.25)';
                if (isHighlight) e.currentTarget.style.color = colors.accentHover;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.textShadow = 'none';
                if (isHighlight) e.currentTarget.style.color = colors.accent;
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
    <div style={container}>
      {/* Глубина: мягкие объединяющие слои, без видимых краёв */}
      <div style={{
        position: 'absolute', inset: 0,
        background: colors.bgA,
        backdropFilter: 'blur(50px)', WebkitBackdropFilter: 'blur(50px)',
        zIndex: -1,
      }} />
      <div style={{
        position: 'absolute',
        top: -40, left: -40, right: -20, bottom: -40,
        background: colors.depthRadialSoft,
        zIndex: -2,
        pointerEvents: 'none',
      }} />

      {/* Текстовые строки */}
      {renderInteractiveLine('Инвестируй и получай', phrase1)}
      {renderInteractiveLine('доход в USDT просто!', phrase2, ['доход', 'в', 'USDT'])}
      {renderInteractiveLine('Комиссия только при выводе', phrase3)}

      {/* Кнопки */}
      <div style={btnRow}>
        <button
          type="button"
          onClick={handleRegister}
          aria-label="Сделай первый ход"
          style={btnPrimary}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(124,58,237,0.22)';
            e.currentTarget.style.boxShadow = 'inset 0 0 0 1px rgba(124,58,237,0.35)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(124,58,237,0.14)';
            e.currentTarget.style.boxShadow = 'inset 0 0 0 0 rgba(124,58,237,0.2)';
          }}
        >
          Сделай первый ход
        </button>
        <button
          type="button"
          onClick={handleAbout}
          aria-label="Правила игры"
          style={btnBase}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(124,58,237,0.08)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          Правила игры
        </button>
      </div>
    </div>
  );
};