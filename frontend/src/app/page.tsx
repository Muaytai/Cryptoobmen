'use client';

import Image from 'next/image';
import { Header } from '@/components/layout/Header';

export default function HomePage() {
  return (
    <div className="container">
      <Header />

      {/* Main Content */}
      <main className="main">
        <div className="grid">
          {/* Left Column - Text Content */}
          <div className="hero-content">
            <h1 className="hero-title">
              Инвестируй и получай{' '}
              <span className="hero-highlight">
                от 10% годовых в USDT
              </span>
            </h1>
            
            <div className="button-group">
              <button className="button button-primary">
                Попробовать бесплатно
              </button>
              <button className="button button-outline">
                Узнать подробнее
              </button>
            </div>
          </div>

          {/* Right Column - Chess Image */}
          <div className="image-container">
            <div className="image-overlay" />
            <Image
              src="/images/chess.png"
              alt="Chess Strategy"
              fill
              style={{ objectFit: 'contain' }}
              priority
              className="chess-image"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
