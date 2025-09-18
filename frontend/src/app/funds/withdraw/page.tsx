import { Suspense } from 'react';
import { WithdrawPage } from './WithdrawPage';

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <WithdrawPage />
    </Suspense>
  );
}
