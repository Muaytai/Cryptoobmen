import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Отзывы - CTokenX | Отзывы пользователей о платформе',
  description: 'Читайте отзывы пользователей о платформе CTokenX. Узнайте о реальном опыте работы с нашей платформой для обмена криптовалют. Оставьте свой отзыв и поделитесь мнением.',
};

import ReviewsPageClient from './ReviewsPageClient';

export default function ReviewsPage() {
  return <ReviewsPageClient />;
}
