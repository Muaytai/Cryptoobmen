import { WithdrawPage } from './WithdrawPage';
import { Suspense } from 'react';

export default function WithdrawPageWrapper() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <WithdrawPage />
    </Suspense>
  );
}
