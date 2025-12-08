import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Обмен криптовалют - CTokenX | Быстрый и безопасный обмен',
  description: 'Обменивайте криптовалюты на платформе CTokenX. Выгодные курсы, низкие комиссии, мгновенные транзакции. Безопасный обмен различных криптовалют.',
};

import ExchangePageClient from './ExchangePageClient';

export default function ExchangePage() {
  return <ExchangePageClient />;
}
