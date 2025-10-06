/**
 * Утилиты для работы с cookies
 */

type CookieOptions = {
  path?: string;
  maxAge?: number;
  expires?: Date;
  domain?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
};

/**
 * Установка cookie
 * @param name Имя cookie
 * @param value Значение cookie
 * @param options Дополнительные параметры
 */
export function setCookie(name: string, value: string, options: CookieOptions = {}) {
  const cookieOptions = {
    path: '/',
    ...options
  };

  if (cookieOptions.expires instanceof Date) {
    cookieOptions.expires = cookieOptions.expires.toUTCString() as any;
  }

  let updatedCookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

  for (const optionKey in cookieOptions) {
    if (Object.prototype.hasOwnProperty.call(cookieOptions, optionKey)) {
      const optionValue = (cookieOptions as any)[optionKey];
      if (optionValue !== true && optionValue !== undefined) {
        updatedCookie += `; ${optionKey}=${optionValue}`;
      } else if (optionValue === true) {
        updatedCookie += `; ${optionKey}`;
      }
    }
  }

  document.cookie = updatedCookie;
}

/**
 * Получение значения cookie по имени
 * @param name Имя cookie
 * @returns Значение cookie или undefined, если cookie не найдена
 */
export function getCookie(name: string): string | undefined {
  const matches = document.cookie.match(
    new RegExp(`(?:^|; )${name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1')}=([^;]*)`)
  );
  return matches ? decodeURIComponent(matches[1]) : undefined;
}

/**
 * Удаление cookie
 * @param name Имя cookie
 * @param options Дополнительные параметры
 */
export function deleteCookie(name: string, options: CookieOptions = {}) {
  setCookie(name, '', {
    ...options,
    maxAge: -1,
  });
}

/**
 * Очистка всех cookies
 * @param paths Пути, для которых нужно очистить cookies
 * @param domains Домены, для которых нужно очистить cookies
 */
export function clearAllCookies(paths: string[] = ['/'], domains: string[] = ['']) {
  const cookies = document.cookie.split(';').map(cookie => cookie.trim().split('=')[0]);
  
  cookies.forEach(cookieName => {
    paths.forEach(path => {
      domains.forEach(domain => {
        if (domain) {
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; domain=${domain}; samesite=lax`;
        } else {
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; samesite=lax`;
        }
      });
    });
  });
}
