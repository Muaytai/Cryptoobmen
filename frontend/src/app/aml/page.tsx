import { Metadata } from 'next';
import AmlPageClient from './AmlPageClient';

export const metadata: Metadata = {
  title: 'Политика AML - CTokenX | Противодействие отмыванию денег',
  description: 'Ознакомьтесь с политикой AML (Anti-Money Laundering) платформы CTokenX. Процедуры KYC, мониторинг транзакций, оценка рисков и меры по предотвращению незаконной деятельности.',
};

export default function AMLPage() {
  return <AmlPageClient />;
}
