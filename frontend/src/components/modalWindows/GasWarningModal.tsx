import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

interface GasWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  gasInfo: {
    estimated_gas_cost: string;
    currency_symbol: string;
    calculation_method: string;
  } | null;
  currencySymbol: string;
  network: string;
}

const GasWarningModal: React.FC<GasWarningModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  gasInfo,
  currencySymbol,
  network
}) => {
  useEffect(() => {
    if (isOpen) {
      // Блокируем скролл страницы
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
      document.body.style.height = '100%';
      document.body.style.top = '0';
      document.body.style.left = '0';
      // Дополнительно фиксируем html
      document.documentElement.style.overflow = 'hidden';
    } else {
      // Восстанавливаем скролл
      document.body.style.overflow = 'unset';
      document.body.style.position = 'unset';
      document.body.style.width = 'unset';
      document.body.style.height = 'unset';
      document.body.style.top = 'unset';
      document.body.style.left = 'unset';
      document.documentElement.style.overflow = 'unset';
    }

    // Очистка при размонтировании
    return () => {
      document.body.style.overflow = 'unset';
      document.body.style.position = 'unset';
      document.body.style.width = 'unset';
      document.body.style.height = 'unset';
      document.body.style.left = 'unset';
      document.documentElement.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modalContent = (
    <div 
      style={{
        position: 'fixed',
        top: '64px', // Отступ сверху для хедера
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh', // Полная высота экрана
        minHeight: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.99)', // Максимально непрозрачный фон
        backdropFilter: 'blur(2px)', // Дополнительное размытие фона
        zIndex: 999, // Ниже хедера
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        padding: '20px',
        boxSizing: 'border-box',
        margin: 0,
        border: 'none',
        outline: 'none',
        overflow: 'hidden',
        // Дополнительные стили для полного перекрытия
        pointerEvents: 'auto',
        isolation: 'isolate'
      }}
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: '#1a1a1a',
          border: '1px solid rgba(59, 130, 246, 0.4)',
          borderRadius: '15px',
          padding: '15px',
          marginTop: '40px',
          maxWidth: '450px',
          width: '90%',
          maxHeight: '80vh',
          overflowY: 'visible',
          position: 'relative',
          zIndex: 1000, // Ниже хедера
          margin: 0,
          boxSizing: 'border-box',
          boxShadow: '0 0 30px rgba(59, 130, 246, 0.3), 0 0 60px rgba(59, 130, 246, 0.2), 0 0 90px rgba(59, 130, 246, 0.1)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ textAlign: 'center', color: 'white' }}>
          {/* Иконка предупреждения */}
          <div style={{ marginBottom: '10px' }}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              style={{ width: '36px', height: '36px', margin: '0 auto', color: '#f59e0b' }}
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" 
              />
            </svg>
          </div>

          {/* Заголовок */}
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: 'white' }}>
            Важное предупреждение
          </h2>

          {/* Основное предупреждение */}
          <div style={{ 
            backgroundColor: 'rgba(245, 158, 11, 0.1)', 
            borderLeft: '4px solid #f59e0b', 
            padding: '12px', 
            borderRadius: '8px', 
            marginBottom: '12px',
            textAlign: 'left'
          }}>
            <h3 style={{ 
              fontWeight: 'bold', 
              color: '#f59e0b', 
              marginBottom: '8px', 
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center'
            }}>
              <svg xmlns="http://www.w3.org/2000/svg" style={{ width: '16px', height: '16px', marginRight: '6px' }} viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              Перевод через прокси кошелек
            </h3>
            <p style={{ color: '#fbbf24', marginBottom: '8px', lineHeight: '1.4', fontSize: '13px' }}>
              В целях безопасности ваш перевод будет осуществлен через прокси кошелек. 
              Это означает, что <strong>газ будет списан дважды</strong>:
            </p>
            <ul style={{ color: '#fbbf24', paddingLeft: '16px', lineHeight: '1.4', fontSize: '13px' }}>
              <li>Первый раз - при переводе с вашего кошелька на прокси</li>
              <li>Второй раз - при переводе с прокси на финальный адрес</li>
            </ul>
          </div>

          {/* Информация о газе */}
          {gasInfo && (
            <div style={{ 
              backgroundColor: 'rgba(59, 130, 246, 0.1)', 
              borderLeft: '4px solid #3b82f6', 
              padding: '12px', 
              borderRadius: '8px', 
              marginBottom: '12px',
              textAlign: 'left'
            }}>
              <h4 style={{ 
                fontWeight: 'bold', 
                color: '#60a5fa', 
                marginBottom: '8px', 
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" style={{ width: '16px', height: '16px', marginRight: '6px' }} viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Текущая стоимость газа
              </h4>
              <div style={{ color: '#93c5fd', lineHeight: '1.4', fontSize: '13px' }}>
                <p><strong>Сеть:</strong> {network}</p>
                <p><strong>Валюта:</strong> {currencySymbol}</p>
                <p><strong>Примерная стоимость газа:</strong> {gasInfo.estimated_gas_cost} {gasInfo.currency_symbol}</p>
                <p style={{ fontSize: '12px', color: '#93c5fd', marginTop: '8px' }}>
                  * Стоимость может измениться в зависимости от загрузки сети
                </p>
              </div>
            </div>
          )}

          {/* Дополнительная информация */}
          <div style={{ 
            backgroundColor: 'rgba(107, 114, 128, 0.1)', 
            padding: '12px', 
            borderRadius: '8px', 
            marginBottom: '12px',
            textAlign: 'left'
          }}>
            <h4 style={{ fontWeight: 'bold', color: '#d1d5db', marginBottom: '8px', fontSize: '14px' }}>
              Что это означает для вас:
            </h4>
            <ul style={{ color: '#9ca3af', paddingLeft: '16px', lineHeight: '1.4', fontSize: '13px' }}>
              <li>Общая стоимость перевода будет выше обычной</li>
              <li>Время обработки может быть немного больше</li>
              <li>Безопасность ваших средств повышена</li>
              <li>Все переводы проходят дополнительную проверку</li>
            </ul>
          </div>

          {/* Кнопки */}
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={onClose}
              style={{
                backgroundColor: '#4b5563',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                transition: 'background-color 0.3s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#6b7280'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#4b5563'}
            >
              Отменить
            </button>
            <button
              onClick={onConfirm}
              style={{
                backgroundColor: '#f59e0b',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                transition: 'background-color 0.3s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#d97706'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#f59e0b'}
            >
              Понятно, продолжить
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Рендерим модальное окно в body через портал
  return createPortal(modalContent, document.body);
};

export default GasWarningModal;
