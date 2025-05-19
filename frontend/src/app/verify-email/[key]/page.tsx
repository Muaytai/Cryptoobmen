import { Suspense } from 'react';
import VerifyEmailClient from './VerifyEmailClient';

interface Props {
  params: { key: string };
}

export default async function VerifyEmail({ params }: Props) {
  // Получаем параметры асинхронно
  const resolvedParams = await Promise.resolve(params);
  
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <VerifyEmailClient emailKey={resolvedParams.key} />
    </Suspense>
  );
} 