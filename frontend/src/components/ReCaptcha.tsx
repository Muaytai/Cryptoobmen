'use client';

import { useEffect, useRef } from 'react';

interface ReCaptchaProps {
  siteKey: string;
  onVerify: (token: string) => void;
  action?: string;
}

declare global {
  interface Window {
    grecaptcha: any;
    onRecaptchaLoad: () => void;
  }
}

export default function ReCaptcha({ siteKey, onVerify, action = 'submit' }: ReCaptchaProps) {
  const recaptchaRef = useRef<HTMLDivElement>(null);
  const scriptLoaded = useRef(false);

  useEffect(() => {
    // Если скрипт уже загружен, выполняем reCAPTCHA
    if (window.grecaptcha && window.grecaptcha.ready) {
      executeReCaptcha();
      return;
    }

    // Если скрипт еще не загружен
    if (!scriptLoaded.current) {
      scriptLoaded.current = true;
      
      // Функция, которая будет вызвана после загрузки скрипта
      window.onRecaptchaLoad = () => {
        if (window.grecaptcha) {
          window.grecaptcha.ready(() => {
            executeReCaptcha();
          });
        }
      };

      // Загружаем скрипт reCAPTCHA
      const script = document.createElement('script');
      script.src = `https://www.recaptcha.net/recaptcha/api.js?render=${siteKey}&onload=onRecaptchaLoad`;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);

      return () => {
        // Очистка при размонтировании
        document.head.removeChild(script);
        // Устанавливаем пустую функцию вместо undefined
        window.onRecaptchaLoad = () => {};
      };
    }
  }, [siteKey, action]);

  const executeReCaptcha = () => {
    if (window.grecaptcha) {
      window.grecaptcha.ready(() => {
        window.grecaptcha
          .execute(siteKey, { action })
          .then((token: string) => {
            onVerify(token);
          })
          .catch((error: any) => {
            console.error('reCAPTCHA error:', error);
          });
      });
    }
  };

  return <div ref={recaptchaRef} className="g-recaptcha" data-sitekey={siteKey} data-size="invisible" />;
}
