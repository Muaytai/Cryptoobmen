import React from 'react';
import DepositForm from '@/components/DepositForm';

const DepositPage = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold text-center mb-8">Пополнение счета</h1>
      <DepositForm />
    </div>
  );
};

export default DepositPage; 