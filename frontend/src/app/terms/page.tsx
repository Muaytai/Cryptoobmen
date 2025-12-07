import { Metadata } from 'next';
import TermsPageClient from './TermsPageClient';

export const metadata: Metadata = {
  title: 'Условия использования - CTokenX | Правила и условия платформы',
  description: 'Ознакомьтесь с условиями использования платформы CTokenX. Правила регистрации, финансовых операций, реферальной программы и другие важные условия использования сервиса.',
};

export default function TermsPage() {
  return <TermsPageClient />;
}
