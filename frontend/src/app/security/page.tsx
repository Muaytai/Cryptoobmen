import { Metadata } from 'next';
import SecurityPageClient from './SecurityPageClient';

export const metadata: Metadata = {
  title: 'Безопасность - CTokenX | Защита данных и средств',
  description: 'Узнайте о мерах безопасности платформы CTokenX. Многоуровневая защита данных, двухфакторная аутентификация, холодное хранение средств и другие технологии обеспечения безопасности.',
};

export default function SecurityPage() {
  return <SecurityPageClient />;
}
