'use client';

import React from 'react';
import styles from './Footer.module.css';
import Link from 'next/link';
import { useTheme } from '@/lib/ThemeProvider';

export function Footer() {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';

  return (
    <footer className={`${styles.footer} ${isDarkMode ? styles.dark : styles.light}`}>
      <div className={styles.container}>
        <div className={styles.footerContent}>
          {/* Колонка О нас */}
          <div className={styles.footerColumn}>
            <h3 className={styles.columnTitle}>О нас</h3>
            <nav className={styles.columnLinks}>
              <Link href="/about" className={styles.footerLink}>Компания</Link>
              <Link href="/reviews" className={styles.footerLink}>Отзывы</Link>
              <Link href="/faq" className={styles.footerLink}>FAQ</Link>
              <Link href="/support" className={styles.footerLink}>Центр поддержки</Link>
              <Link href="/contacts" className={styles.footerLink}>Контакты</Link>
            </nav>
          </div>

          {/* Колонка Документы */}
          <div className={styles.footerColumn}>
            <h3 className={styles.columnTitle}>Документы</h3>
            <nav className={styles.columnLinks}>
              <Link href="/terms" className={styles.footerLink}>Условия использования</Link>
              <Link href="/privacy" className={styles.footerLink}>Политика конфиденциальности</Link>
              <Link href="/aml" className={styles.footerLink}>Политика AML</Link>
              <Link href="/agreement" className={styles.footerLink}>Пользовательское соглашение</Link>
              <Link href="/funds" className={styles.footerLink}>Пополнение и вывод средств</Link>
            </nav>
          </div>

          {/* Колонка Навигация */}
          <div className={styles.footerColumn}>
            <h3 className={styles.columnTitle}>Навигация</h3>
            <nav className={styles.columnLinks}>
              <Link href="/" className={styles.footerLink}>Главная</Link>
              <Link href="/login" className={styles.footerLink}>Вход</Link>
              <Link href="/register" className={styles.footerLink}>Регистрация</Link>
              <Link href="/dashboard" className={styles.footerLink}>Личный кабинет</Link>
              <Link href="/referral" className={styles.footerLink}>Реферальная программа</Link>
            </nav>
          </div>

          {/* Колонка с предупреждением */}
          <div className={`${styles.footerColumn} ${styles.disclaimerColumn}`}>
            <p className={styles.disclaimer}>
              *Использование нашей платформы связано с определёнными рисками. 
              Рекомендуем внимательно ознакомиться с условиями предоставления услуг и тщательно
              оценить все возможные последствия перед принятием решений. Мы не несем 
              ответственности за возможные потери или ущерб, который может возникнуть
              в результате использования платформы
            </p>
          </div>
        </div>
        
        {/* Копирайт */}
        <div className={styles.copyright}>
          <p>© 2025 CTokenX CryptoPlatform. Все права защищены</p>
        </div>
      </div>
    </footer>
  );
} 