import Link from 'next/link';

export function Logo() {
  return (
    <Link href="/" className="logo-text">
      <div className="logo-text">
        <span className="logo-g">G</span>
        <span className="logo-x">X</span>
      </div>
    </Link>
  );
} 