'use client';

import Image from 'next/image';
import { SocialButtons } from '@/components/ui/SocialButtons';
import chessImage from '../../public/images/chess.png';

export default function HomePage() {
  return (
    <div style={{position: 'relative', minHeight: '100vh', background: '#111014'}}>
      <main style={{padding: '64px 0 0 0', maxWidth: 1400, margin: '0 auto'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 0}}>
          {/* Левая колонка */}
          <div style={{maxWidth: 600, zIndex: 2, position: 'relative'}}>
            <h1 style={{fontSize: 56, fontWeight: 700, color: '#fff', marginBottom: 20, lineHeight: 1.2}}>
              <span style={{whiteSpace: 'nowrap'}}>Инвестируй и получай</span>{' '}
              <span style={{color: '#b48afd', whiteSpace: 'nowrap'}}>от 10% годовых в USDT</span>
            </h1>
            <div style={{color: '#bdbdbd', fontSize: 22, marginBottom: 40}}>
              Думай на шаг вперёд. Инвестируй с умом.<br />Твоя партия начинается здесь
            </div>
            <div style={{display: 'flex', gap: 16}}>
              <button style={{background: '#a259ff', color: '#fff', border: 'none', borderRadius: 12, padding: '14px 32px', fontWeight: 500, fontSize: 18, cursor: 'pointer', transition: 'background 0.2s'}} onMouseOver={e => e.currentTarget.style.background='#8f3fff'} onMouseOut={e => e.currentTarget.style.background='#a259ff'}>
                Попробовать бесплатно
              </button>
              <button style={{border: '1px solid #a259ff', color: '#fff', borderRadius: 12, padding: '14px 32px', fontWeight: 500, fontSize: 18, background: 'none', cursor: 'pointer', transition: 'background 0.2s'}} onMouseOver={e => e.currentTarget.style.background='#2a1a3a'} onMouseOut={e => e.currentTarget.style.background='none'}>
                Узнать подробнее
              </button>
            </div>
          </div>
          {/* Правая колонка */}
          <div style={{position: 'relative', width: 650, height: 650, marginRight: -50, marginLeft: -350, marginTop: 140}}>
            <Image
              src={chessImage}
              alt="Chess Strategy"
              fill
              style={{ 
                objectFit: 'contain', 
                borderRadius: 24,
                transform: 'scale(1.8) translateX(-110px) translateY(60px)'
              }}
              priority
            />
          </div>
        </div>
        {/* Крипто-иконки снизу */}
        <div style={{display: 'flex', justifyContent: 'center', gap: 32, marginTop: 70}}>
          <Image
            src="/images/crypt-ico.png"
            alt="Cryptocurrency Icons"
            width={850}
            height={100}
            style={{ objectFit: 'contain' }}
          />
        </div>
        {/* Соц. кнопки справа */}
        <SocialButtons />
      </main>
    </div>
  );
}
