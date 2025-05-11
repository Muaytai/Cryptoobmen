'use client';

import React, { useEffect } from 'react';

/**
 * Компонент для исправления проблем с гидратацией, связанных с атрибутами,
 * которые могут добавляться сторонними расширениями браузера
 */
export const HydrationFix: React.FC = () => {
  useEffect(() => {
    // Список атрибутов, которые могут вызывать проблемы с гидратацией
    const problematicAttributes = [
      'bls_skin_checked',
      'data-bls',
      'data-reactroot',
      'data-reactid',
      'data-react-checksum',
      'type-rn'
    ];
    
    let totalCleaned = 0;
    
    // Функция для удаления проблемных атрибутов
    const cleanProblematicAttributes = () => {
      problematicAttributes.forEach(attrName => {
        const selector = `[${attrName}]`;
        try {
          const elements = document.querySelectorAll(selector);
          elements.forEach(el => {
            el.removeAttribute(attrName);
            totalCleaned++;
          });
          
          if (elements.length > 0) {
            console.log(`HydrationFix: removed ${attrName} from ${elements.length} elements`);
          }
        } catch (error) {
          console.error(`HydrationFix: Error removing attribute ${attrName}:`, error);
        }
      });
      
      // Дополнительная проверка для div с классом flex-col min-h-screen
      try {
        const flexColDivs = document.querySelectorAll('div.flex-col.min-h-screen');
        flexColDivs.forEach(div => {
          // Получить все атрибуты
          const attributes = Array.from(div.attributes);
          // Отфильтровать проблемные атрибуты (которые не являются class, id, style и т.д.)
          const suspiciousAttrs = attributes.filter(attr => 
            !['class', 'id', 'style', 'data-testid', 'aria-label'].includes(attr.name)
          );
          
          // Удалить проблемные атрибуты
          suspiciousAttrs.forEach(attr => {
            div.removeAttribute(attr.name);
            totalCleaned++;
            console.log(`HydrationFix: removed suspicious attribute ${attr.name} from div.flex-col.min-h-screen`);
          });
        });
      } catch (error) {
        console.error('HydrationFix: Error cleaning flex-col divs:', error);
      }
    };
    
    // Вызвать сразу после монтирования
    cleanProblematicAttributes();
    
    // Вызвать снова через небольшую задержку, чтобы поймать атрибуты, добавленные позже
    const timeoutId = setTimeout(cleanProblematicAttributes, 1000);
    
    // Дополнительные меры для решения проблемы с гидратацией
    const mutationObserver = new MutationObserver((mutations) => {
      let needsCleaning = false;
      
      mutations.forEach((mutation) => {
        // Проверка на добавление атрибутов
        if (mutation.type === 'attributes' && 
            problematicAttributes.includes(mutation.attributeName || '')) {
          const target = mutation.target as Element;
          target.removeAttribute(mutation.attributeName || '');
          needsCleaning = true;
        }
        
        // Проверка на добавление новых узлов
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          needsCleaning = true;
        }
      });
      
      // Если были обнаружены изменения, которые могут потребовать очистки
      if (needsCleaning) {
        cleanProblematicAttributes();
      }
    });
    
    // Начать наблюдение за изменениями DOM
    mutationObserver.observe(document.body, { 
      attributes: true, 
      childList: true,
      subtree: true, 
      attributeFilter: problematicAttributes 
    });
    
    if (totalCleaned > 0) {
      console.log(`HydrationFix: cleaned ${totalCleaned} total problematic attributes`);
    }
    
    // Очистка при размонтировании компонента
    return () => {
      mutationObserver.disconnect();
      clearTimeout(timeoutId);
    };
  }, []);

  // Компонент не рендерит видимый контент
  return null;
};

export default HydrationFix; 