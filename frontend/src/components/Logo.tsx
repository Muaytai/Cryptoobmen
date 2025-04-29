import Link from 'next/link';
import Image from 'next/image';
import styles from './Logo.module.css';

export function Logo() {
  return (
    <Link href="/" className={styles.logoLink}>
      <div className={styles.logoImage}>
        <Image 
          src="/images/Логотип.png" 
          alt="GX Exchange" 
          width={50} 
          height={50}
          priority
        />
      </div>
    </Link>
  );
} 