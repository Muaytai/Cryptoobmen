import { Suspense } from 'react';
import VerifyEmailClient from './VerifyEmailClient';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Подтверждение Email | Cryptoobmen',
  description: 'Подтверждение электронной почты для регистрации на платформе'
};

export default async function VerifyEmail({
  params,
}: {
  params: Promise<{ key: string }>
}) {
  const { key } = await params;
  
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <VerifyEmailClient emailKey={key} />
    </Suspense>
  );
} 