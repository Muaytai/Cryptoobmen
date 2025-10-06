'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import ClientOnly from './ClientOnly';

type SafeImageMultiProps = {
  src: string;
  altSrc?: string[];
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
  quality?: number;
};

/**
 * Улучшенный компонент для загрузки изображений с поддержкой альтернативных источников
 * Полезно для работы с файлами, которые могут иметь разные имена (например, латиница/кириллица)
 */
export function SafeImageMulti({
  src,
  altSrc = [],
  alt,
  width,
  height,
  className = '',
  priority = false,
  quality = 80
}: SafeImageMultiProps) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [currentSrcIndex, setCurrentSrcIndex] = useState(-1);
  
  // Создаем полный список источников
  const allSources = [src, ...altSrc];
  
  useEffect(() => {
    // Сбрасываем состояние при изменении источников
    setImageSrc(src);
    setLoadError(false);
    setCurrentSrcIndex(-1);
  }, [src, altSrc]);
  
  // Обработчик ошибки загрузки
  const handleError = () => {
    setLoadError(true);
    
    // Пробуем следующий источник, если он есть
    const nextIndex = currentSrcIndex + 1;
    if (nextIndex < allSources.length) {
      setCurrentSrcIndex(nextIndex);
      setImageSrc(allSources[nextIndex]);
    }
  };
  
  // Только на клиенте
  return (
    <ClientOnly>
      {imageSrc ? (
        width && height ? (
          // Если указаны размеры, используем компонент Image из next/image
          <Image
            src={imageSrc}
            alt={alt}
            width={width}
            height={height}
            className={className}
            priority={priority}
            quality={quality}
            unoptimized={imageSrc.startsWith('data:') || imageSrc.startsWith('blob:')}
            onError={handleError}
          />
        ) : (
          // Иначе используем стандартный тег img
          <img
            src={imageSrc}
            alt={alt}
            className={className}
            onError={handleError}
          />
        )
      ) : (
        // Временная заглушка
        <div className={`${className} bg-gray-200 animate-pulse`} 
             style={{width: width ? `${width}px` : '100%', height: height ? `${height}px` : '100%'}} 
        />
      )}
    </ClientOnly>
  );
}

export default SafeImageMulti; 