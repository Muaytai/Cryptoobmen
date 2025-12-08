import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Оставить отзыв - CTokenX | Поделитесь своим мнением',
  description: 'Оставьте отзыв о платформе CTokenX. Поделитесь своим опытом использования нашего сервиса обмена криптовалют. Ваше мнение важно для нас!',
};

import FeedbackPageClient from './FeedbackPageClient';

export default function FeedbackPage() {
  return <FeedbackPageClient />;
}
