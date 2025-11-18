'use client';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';

export default function SidebarWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = pathname.startsWith('/dashboard') || pathname.startsWith('/referral');
  return (
    <div className="flex flex-row flex-1 min-h-screen">
      {showSidebar && <Sidebar />}
      <main className="flex-1">{children}</main>
    </div>
  );
} 