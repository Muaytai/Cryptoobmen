"use client";

import { useTheme } from 'next-themes';
import React, { useEffect, useState } from 'react';
import Image from 'next/image';

type ImageDependThemeProps = {
  srcDark: string;
  srcLight: string;
};

const ImageDependTheme: React.FC<ImageDependThemeProps> = ({ srcDark, srcLight }) => {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
       // alert(theme); // будет работать только на клиенте
    }
  }, [mounted, theme]);

  if (!mounted) return null;

  const imageSrc = theme === 'dark' ? srcDark : srcLight;

  return (
    <div>
      <Image
        src={imageSrc}
        alt="Logo"
        width={80}
        height={80}
        priority
      />
    </div>
  );
};

export default ImageDependTheme;
