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
  
  console.log('ReCaptcha: siteKey =', siteKey, 'action =', action);

  useEffect(() => {
    console.log('ReCaptcha useEffect: siteKey =', siteKey, 'action =', action);
    
    // Если скрипт уже загружен, выполняем reCAPTCHA
    if (window.grecaptcha && window.grecaptcha.ready) {
      console.log('ReCaptcha: скрипт уже загружен, выполняем reCAPTCHA');
      executeReCaptcha();
      return;
    }

    // Если скрипт еще не загружен
    if (!scriptLoaded.current) {
      console.log('ReCaptcha: загружаем скрипт');
      scriptLoaded.current = true;
      
      // Функция, которая будет вызвана после загрузки скрипта
      window.onRecaptchaLoad = () => {
        console.log('ReCaptcha: скрипт загружен, onRecaptchaLoad вызван');
        if (window.grecaptcha) {
          window.grecaptcha.ready(() => {
            console.log('ReCaptcha: grecaptcha.ready вызван');
            executeReCaptcha();
          });
        }
      };

      // Загружаем скрипт reCAPTCHA
      const script = document.createElement('script');
      script.src = `https://www.recaptcha.net/recaptcha/api.js?render=${siteKey}&onload=onRecaptchaLoad`;
      script.async = true;
      script.defer = true;
      console.log('ReCaptcha: добавляем скрипт:', script.src);
      document.head.appendChild(script);

      return () => {
        // Очистка при размонтировании
        console.log('ReCaptcha: очистка скрипта');
        document.head.removeChild(script);
        // Устанавливаем пустую функцию вместо undefined
        window.onRecaptchaLoad = () => {};
      };
    }
  }, [siteKey, action]);

  const executeReCaptcha = () => {
    console.log('ReCaptcha executeReCaptcha: grecaptcha доступен =', !!window.grecaptcha);
    if (window.grecaptcha) {
      console.log('ReCaptcha: вызываем grecaptcha.ready');
      window.grecaptcha.ready(() => {
        console.log('ReCaptcha: grecaptcha.ready callback, вызываем execute с action =', action);
        window.grecaptcha
          .execute(siteKey, { action })
          .then((token: string) => {
            console.log('ReCaptcha: токен получен, длина =', token ? token.length : 0);
            onVerify(token);
          })
          .catch((error: any) => {
            console.error('ReCaptcha: ошибка при выполнении:', error);
          });
      });
    } else {
      console.error('ReCaptcha: grecaptcha недоступен в window');
    }
  };

  return <div ref={recaptchaRef} className="g-recaptcha" data-sitekey={siteKey} data-size="invisible" />;
}
