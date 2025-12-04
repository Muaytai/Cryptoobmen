import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'О нас - CTokenX | Надежная платформа для обмена криптовалют',
  description: 'Узнайте больше о CTokenX, нашей истории, миссии и команде. Мы создаем безопасную и удобную платформу для обмена цифровых активов.',
};

import AboutPageClient from "./AboutPageClient";

export default function AboutPage() {
  return <AboutPageClient />;
}