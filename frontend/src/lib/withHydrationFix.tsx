'use client';

import React from 'react';
import ClientOnly from '@/components/ClientOnly';

/**
 * HOC (компонент высшего порядка) для предотвращения ошибок гидратации,
 * обертывая компонент в ClientOnly.
 * 
 * @param Component - Компонент, который нужно обернуть
 * @param fallback - Опциональное содержимое для отображения во время загрузки
 * @returns Компонент, обернутый в ClientOnly
 */
export function withHydrationFix<P extends object>(
  Component: React.ComponentType<P>,
  fallback: React.ReactNode = null
) {
  return function WithHydrationFix(props: P) {
    return (
      <ClientOnly fallback={fallback}>
        <Component {...props} />
      </ClientOnly>
    );
  };
} 