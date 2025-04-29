import React from 'react';
import Image, { ImageProps } from 'next/image';
import { cn } from '@/lib/utils';

interface FigmaImageProps extends Omit<ImageProps, 'alt'> {
  alt: string;
  className?: string;
  containerClassName?: string;
  aspectRatio?: 'auto' | 'square' | 'video' | '4/3';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
}

export const FigmaImage: React.FC<FigmaImageProps> = ({
  src,
  alt,
  className,
  containerClassName,
  aspectRatio = 'auto',
  rounded = 'md',
  ...props
}) => {
  const aspectRatioClasses = {
    'auto': '',
    'square': 'aspect-square',
    'video': 'aspect-video',
    '4/3': 'aspect-[4/3]',
  };

  const roundedClasses = {
    'none': 'rounded-none',
    'sm': 'rounded-sm',
    'md': 'rounded-md',
    'lg': 'rounded-lg',
    'full': 'rounded-full',
  };

  return (
    <div className={cn(
      'overflow-hidden',
      aspectRatioClasses[aspectRatio],
      roundedClasses[rounded],
      containerClassName
    )}>
      <Image
        src={src}
        alt={alt}
        className={cn(
          'h-auto w-full object-cover',
          className
        )}
        {...props}
      />
    </div>
  );
}; 