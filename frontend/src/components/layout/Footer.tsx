'use client';

import React, { useEffect, useState } from 'react';
import styles from './Footer.module.css';
import Link from 'next/link';

export function Footer() {
  const currentYear = new Date().getFullYear();
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  if (!mounted) {
    return null;
  }
  
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.content}>
          <div className={styles.copyright}>
            <p suppressHydrationWarning>
              &copy; {currentYear} GX Exchange. Все права защищены.
            </p>
          </div>
          <div className={styles.links}>
            <Link href="/terms">Условия использования</Link>
            <Link href="/privacy">Политика конфиденциальности</Link>
            <Link href="/contacts">Контакты</Link>
          </div>
        </div>
      </div>
    </footer>
  );
} 