'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const menu = [
  { href: '/dashboard', icon: '🏠', label: 'Главная' },
  { href: '/wallet', icon: '👛', label: 'Кошелек' },
  { href: '/referral', icon: '🤝', label: 'Реф. программа' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-16 bg-[#181828] h-screen flex flex-col items-center py-6 space-y-6">
      {menu.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`flex flex-col items-center text-sm ${
            pathname === item.href ? 'text-[#a855f7]' : 'text-gray-400'
          } hover:text-[#a855f7] transition-colors`}
        >
          <span className="text-2xl mb-1">{item.icon}</span>
          <span className="text-xs text-center whitespace-nowrap">{item.label}</span>
        </Link>
      ))}
    </aside>
  );
} 