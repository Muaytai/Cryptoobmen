import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'FAQ - CTokenX | Часто задаваемые вопросы',
  description: 'Найдите ответы на часто задаваемые вопросы о платформе CTokenX. Узнайте о регистрации, пополнении счета, выводе средств, реферальной программе и безопасности.',
};

import FaqPageClient from './FaqPageClient';

export default function FAQPage() {
  return <FaqPageClient />;
}
