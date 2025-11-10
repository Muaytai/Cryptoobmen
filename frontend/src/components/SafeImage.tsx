'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import ClientOnly from './ClientOnly';

type SafeImageProps = {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
  quality?: number;
};

/**
 * Безопасный компонент для изображений, который не вызывает проблем с гидратацией
 * и правильно обрабатывает загрузку
 */
export function SafeImage({ 
  src, 
  alt, 
  width, 
  height, 
  className = '', 
  priority = false,
  quality = 80
}: SafeImageProps) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  
  // Загружаем изображение только на клиенте
  useEffect(() => {
    setImageSrc(src);
  }, [src]);
  
  // Рендерим только на клиенте и только когда imageSrc установлен
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
            unoptimized={src.startsWith('data:') || src.startsWith('blob:')}
          />
        ) : (
          // Иначе используем стандартный тег img
          <img
            src={imageSrc}
            alt={alt}
            className={className}
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

export default SafeImage; 