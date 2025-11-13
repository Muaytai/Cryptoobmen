'use client';

import { useState, useCallback } from 'react';
import { useGoogleReCaptcha } from 'react-google-recaptcha-v3';

export const useReCaptcha = () => {
  const { executeRecaptcha } = useGoogleReCaptcha();
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(async (action: string = 'submit') => {
    if (!executeRecaptcha) {
      setError('reCAPTCHA не инициализирована');
      return null;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const token = await executeRecaptcha(action);
      return token;
    } catch (err) {
      setError('Ошибка при проверке reCAPTCHA');
      console.error('reCAPTCHA error:', err);
      return null;
    } finally {
      setIsVerifying(false);
    }
  }, [executeRecaptcha]);

  return {
    getToken,
    isVerifying,
    error
  };
}; 