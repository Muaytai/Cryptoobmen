'use client';

import { useEffect, useState } from 'react';

/**
 * Компонент, который рендерит своих дочерних элементов только на клиенте,
 * чтобы избежать проблем с гидратацией для компонентов, которые зависят от DOM или браузерного API.
 * 
 * @param {Object} props - Свойства компонента
 * @param {React.ReactNode} props.children - Дочерние элементы
 * @param {React.ReactNode} props.fallback - Опциональное содержимое для рендеринга во время загрузки
 */
export default function ClientOnly({ 
  children, 
  fallback = null 
}: { 
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return fallback;
  }

  return <>{children}</>;
} 