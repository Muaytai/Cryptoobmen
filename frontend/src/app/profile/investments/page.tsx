'use client';

import React from 'react';
import { InvestmentsPage } from './InvestmentsPage';

export default function Page() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white">
      <InvestmentsPage />
    </div>
  );
}
