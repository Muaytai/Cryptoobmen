import { Metadata } from 'next';
import PrivacyPageClient from './PrivacyPageClient';

export const metadata: Metadata = {
  title: 'Политика конфиденциальности - CTokenX | Защита персональных данных',
  description: 'Ознакомьтесь с политикой конфиденциальности CTokenX. Узнайте, как мы собираем, используем и защищаем ваши персональные данные, ваши права в соответствии с GDPR и другими нормативными актами.',
};

export default function PrivacyPage() {
  return <PrivacyPageClient />;
}
