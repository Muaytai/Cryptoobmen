import { Metadata } from 'next';
import AgreementPageClient from './AgreementPageClient';

export const metadata: Metadata = {
  title: 'Пользовательское соглашение - CTokenX | Условия использования платформы',
  description: 'Ознакомьтесь с пользовательским соглашением CTokenX. Условия использования платформы для обмена криптовалют, права и обязанности пользователей, политика безопасности и конфиденциальности.',
};

export default function AgreementPage() {
  return <AgreementPageClient />;
} 