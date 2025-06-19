import { Suspense } from 'react';
import { DepositPage } from './DepositPage';

export default function DepositPageWrapper() {
  return (
    <Suspense fallback={<div>Загрузка страницы пополнения...</div>}>
      <DepositPage />
    </Suspense>
  );
}
