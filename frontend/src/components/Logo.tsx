'use client';

import Link from 'next/link';
import { withHydrationFix } from '@/lib/withHydrationFix';
import SafeImage from './SafeImage';

export const Logo = () => {
  return (
    <Link href="/" className="no-underline">
      <div className="flex items-center justify-center">
        <SafeImage
          src="/images/logo.webp"
          alt="GX Exchange"
          width={50}
          height={50}
        />
      </div>
    </Link>
  );
};

// Экспортируем компонент с исправлением гидратации по умолчанию
export default withHydrationFix(Logo);

// Экспортируем оригинальный компонент для использования в местах, где проблемы гидратации не важны
export { Logo as LogoOriginal }; 