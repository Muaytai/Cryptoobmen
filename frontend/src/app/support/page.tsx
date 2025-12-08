import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Поддержка - CTokenX | Свяжитесь с нами',
  description: 'Центр поддержки CTokenX. Получите помощь по вопросам обмена криптовалют, транзакций и работы платформы. Свяжитесь с нами через форму обратной связи или по контактам.',
};

import SupportPageClient from './SupportPageClient';

export default function SupportPage() {
  return <SupportPageClient />;
}
