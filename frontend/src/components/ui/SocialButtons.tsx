import React from 'react';

export const SocialButtons = () => (
  <div style={{
    position: 'fixed',
    top: '40%',
    right: 32,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    zIndex: 10
  }}>
    <a
      href="https://t.me/your_channel"
      target="_blank"
      rel="noopener noreferrer"
      style={{
        background: '#262626',
        borderRadius: 12,
        padding: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'background 0.2s'
      }}
      onMouseOver={e => e.currentTarget.style.background = '#b48afd'}
      onMouseOut={e => e.currentTarget.style.background = '#262626'}
      title="Telegram"
    >
      <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
        <path fill="#b48afd" d="M21.5 4.5 18.2 19.1c-.2.8-.7 1-1.4.6l-3.8-2.8-1.8 1.7c-.2.2-.4.3-.7.3l.2-2.2 8-7.2c.3-.3-.1-.4-.5-.2l-9.9 6.2-2.1-.7c-.8-.3-.8-.8.2-1.2l16.3-6.3c.7-.3 1.3.2 1.1 1.1Z"/>
      </svg>
    </a>
    <a
      href="https://instagram.com/your_profile"
      target="_blank"
      rel="noopener noreferrer"
      style={{
        background: '#262626',
        borderRadius: 12,
        padding: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'background 0.2s'
      }}
      onMouseOver={e => e.currentTarget.style.background = '#b48afd'}
      onMouseOut={e => e.currentTarget.style.background = '#262626'}
      title="Instagram"
    >
      <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
        <rect width="18" height="18" x="3" y="3" rx="5" fill="#b48afd"/>
        <circle cx="12" cy="12" r="4" fill="#111014"/>
        <circle cx="17" cy="7" r="1" fill="#111014"/>
      </svg>
    </a>
  </div>
); 