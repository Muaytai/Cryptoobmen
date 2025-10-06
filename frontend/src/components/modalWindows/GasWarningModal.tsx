import React from 'react';
import styles from './mainModalWrapper/Modal.module.css';

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
  if (!isOpen) return null;

  return (
    <div className={styles.modalWrapper} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className="text-center">
          {/* Иконка предупреждения */}
          <div className="mb-3 sm:mb-4">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-12 w-12 sm:h-16 sm:w-16 mx-auto text-amber-500 dark:text-amber-500" 
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
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white mb-3 px-2">
            Важное предупреждение
          </h2>

          {/* Блоки информации - адаптивное расположение */}
          <div className="flex flex-col xl:flex-row gap-3 mb-3 sm:mb-4">
            {/* Основное предупреждение */}
            <div className="bg-amber-50 dark:bg-amber-900 bg-opacity-30 dark:bg-opacity-30 border-l-4 border-amber-500 p-3 sm:p-4 rounded-md text-left flex-1">
              <h3 className="font-bold text-amber-800 dark:text-amber-300 mb-2 sm:mb-3 flex items-center text-sm sm:text-base">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="break-words">Перевод через прокси кошелек</span>
              </h3>
              <p className="text-amber-700 dark:text-amber-200 text-xs sm:text-sm leading-relaxed mb-2 sm:mb-3">
                В целях безопасности ваш перевод будет осуществлен через прокси кошелек. 
                Это означает, что <strong>газ будет списан дважды</strong>:
              </p>
              <ul className="list-disc pl-4 sm:pl-5 text-amber-700 dark:text-amber-200 text-xs sm:text-sm space-y-1">
                <li>Первый раз - при переводе с вашего кошелька на прокси</li>
                <li>Второй раз - при переводе с прокси на финальный адрес</li>
              </ul>
            </div>

            {/* Информация о газе */}
            {gasInfo && (
              <div className="bg-blue-50 dark:bg-blue-900 bg-opacity-30 dark:bg-opacity-30 border-l-4 border-blue-500 p-3 sm:p-4 rounded-md text-left flex-1">
                <h4 className="font-bold text-blue-800 dark:text-blue-300 mb-2 flex items-center text-sm sm:text-base">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 sm:h-5 sm:w-5 mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="break-words">Текущая стоимость газа</span>
                </h4>
                <div className="text-blue-700 dark:text-blue-200 text-xs sm:text-sm space-y-1">
                  <p className="break-words"><strong>Сеть:</strong> {network}</p>
                  <p className="break-words"><strong>Валюта:</strong> {currencySymbol}</p>
                  <p className="break-words"><strong>Примерная стоимость газа:</strong> {gasInfo.estimated_gas_cost} {gasInfo.currency_symbol}</p>
                  <p className="text-xs text-blue-600 dark:text-blue-300 mt-2 leading-relaxed">
                    * Стоимость может измениться в зависимости от загрузки сети
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Дополнительная информация */}
          <div className="bg-gray-100 dark:bg-gray-700 bg-opacity-50 dark:bg-opacity-50 p-3 rounded-md mb-3 text-left">
            <h4 className="font-bold text-gray-800 dark:text-gray-300 mb-2 text-sm sm:text-base">Что это означает для вас:</h4>
            <ul className="list-disc pl-4 sm:pl-5 text-gray-700 dark:text-gray-300 text-xs sm:text-sm space-y-1">
              <li>Общая стоимость перевода будет выше обычной</li>
              <li>Время обработки может быть немного больше</li>
              <li>Безопасность ваших средств повышена</li>
              <li>Все переводы проходят дополнительную проверку</li>
            </ul>
          </div>

          {/* Кнопки */}
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 justify-center">
            <button
              onClick={onClose}
              className="bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-700 text-gray-800 dark:text-white py-2.5 sm:py-3 px-4 sm:px-6 rounded-lg transition font-medium text-sm sm:text-base"
            >
              Отменить
            </button>
            <button
              onClick={onConfirm}
              className="bg-amber-500 dark:bg-amber-600 hover:bg-amber-600 dark:hover:bg-amber-700 text-white py-2.5 sm:py-3 px-4 sm:px-6 rounded-lg transition font-medium text-sm sm:text-base"
            >
              Понятно, продолжить
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GasWarningModal;
