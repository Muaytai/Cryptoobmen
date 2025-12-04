import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Контакты - CTokenX | Свяжитесь с нами',
  description: 'Свяжитесь с CTokenX. Наши контакты, адрес офиса, время работы и способы связи. Мы всегда готовы помочь вам с вопросами об обмене криптовалют.',
};

import ContactsPageClient from './ContactsPageClient';

export default function ContactsPage() {
  return <ContactsPageClient />;
} 