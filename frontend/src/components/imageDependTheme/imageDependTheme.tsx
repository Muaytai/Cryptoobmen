'use client';

import Image from 'next/image';
import { useTheme } from '@/lib/ThemeProvider'; // путь к твоему useTheme
import { useEffect, useState } from 'react';

type Props = {
  srcDark: string;
  srcLight: string;
  alt?: string;
  width?: number;
  height?: number;
};

export default function ImageDependTheme({
  srcDark,
  srcLight,
  alt = 'Themed Image',
  width = 80,
  height = 80
}: Props) {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Чтобы избежать ошибки гидрации
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const imageSrc = theme === 'dark' ? srcDark : srcLight;

  return (
    <Image
      src={imageSrc}
      alt={alt}
      width={width}
      height={height}
      priority
    />
  );
}
