import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

type CookieOptions = {
  path?: string;
  maxAge?: number;
  httpOnly?: boolean;
  secure?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
};

// Определяем настройки cookies в зависимости от окружения
const getCookieOptions = (): CookieOptions => ({
  path: '/',
  maxAge: parseInt(process.env.NEXT_PUBLIC_AUTH_COOKIE_MAX_AGE || '2592000'),
  httpOnly: true,
  secure: process.env.NEXT_PUBLIC_SECURE_COOKIE === 'true',
  sameSite: (process.env.NEXT_PUBLIC_SAME_SITE || 'lax') as 'strict' | 'lax'
});

export function middleware(request: NextRequest) {
  // Пропускаем запросы для социальной авторизации и API
  if (request.nextUrl.pathname.startsWith('/accounts/') || 
      request.nextUrl.pathname.startsWith('/api/') ||
      request.nextUrl.pathname.includes('/google/') ||
      request.nextUrl.pathname.includes('/yandex/') ||
      request.nextUrl.pathname.includes('/login/callback/')) {
    return NextResponse.next();
  }

  // Проверяем наличие токенов в URL
  const searchParams = request.nextUrl.searchParams;
  const access_token = searchParams.get('access_token');
  const refresh_token = searchParams.get('refresh_token');

  // Если есть токены в URL, пропускаем запрос
  if (access_token && refresh_token) {
    return NextResponse.next();
  }

  // Проверяем наличие токенов в cookies или localStorage
  const cookieName = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || 'auth-token';
  const token = request.cookies.get(cookieName)?.value || request.cookies.get('access_token')?.value;

  // Если нет токена и пользователь пытается получить доступ к защищенным маршрутам
  if (!token && (
    request.nextUrl.pathname.startsWith('/profile') ||
    request.nextUrl.pathname.startsWith('/wallet') ||
    request.nextUrl.pathname.startsWith('/funds/deposit')
  )) {
    // Сохраняем путь, куда пытался попасть пользователь, чтобы вернуться после авторизации
    const redirect = encodeURIComponent(request.nextUrl.pathname);
    return NextResponse.redirect(new URL(`/login?redirect=${redirect}`, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/profile/:path*',
    '/dashboard/:path*',
    '/wallet/:path*',
    '/funds/:path*',
    '/login/:path*',
    '/register/:path*',
  ],
}; 