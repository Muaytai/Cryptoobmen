import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Пропускаем запросы для социальной авторизации и API
  if (request.nextUrl.pathname.startsWith('/accounts/') || 
      request.nextUrl.pathname.startsWith('/api/') ||
      request.nextUrl.pathname.includes('/google/') ||
      request.nextUrl.pathname.includes('/yandex/') ||
      request.nextUrl.pathname.includes('/login/callback/')) {
    // console.log('Middleware: Path is for API or social auth, skipping.');
    return NextResponse.next();
  }

  // Проверяем наличие токенов в URL
  const searchParams = request.nextUrl.searchParams;
  const access_token_url = searchParams.get('access_token'); // Переименовал для ясности
  const refresh_token_url = searchParams.get('refresh_token'); // Переименовал для ясности

  if (access_token_url && refresh_token_url) {
    console.log('Middleware: Tokens found in URL, skipping cookie check.');
    return NextResponse.next();
  }

  // Проверяем наличие токенов в cookies или localStorage
  const cookieNameFromEnv = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME;
  const primaryCookieNameToCheck = cookieNameFromEnv || 'auth-token';
  
  let token = request.cookies.get(primaryCookieNameToCheck)?.value;
  console.log(`Middleware: Attempting to read cookie "${primaryCookieNameToCheck}": ${token ? 'FOUND' : 'NOT FOUND'}`);

  if (!token) {
    token = request.cookies.get('access_token')?.value;
    console.log(`Middleware: Attempting to read fallback cookie "access_token": ${token ? 'FOUND' : 'NOT FOUND'}`);
  }
  
  console.log(`Middleware: Final token check for path "${request.nextUrl.pathname}": ${token ? 'Token EXISTS' : 'Token NOT FOUND'}`);

  // Если нет токена и пользователь пытается получить доступ к защищенным маршрутам
  if (!token && (
    request.nextUrl.pathname.startsWith('/profile') ||
    request.nextUrl.pathname.startsWith('/dashboard') ||
    request.nextUrl.pathname.startsWith('/wallet') ||
    request.nextUrl.pathname.startsWith('/funds') ||
    request.nextUrl.pathname.startsWith('/exchange')
    // Добавьте другие защищенные маршруты здесь, если они есть
  )) {
    // Сохраняем ПОЛНЫЙ путь (с параметрами), куда пытался попасть пользователь
    const redirectPath = request.nextUrl.pathname + request.nextUrl.search;
    const redirect = encodeURIComponent(redirectPath);
    console.log(`Middleware: Redirecting to /login?redirect=${redirect} because token was not found for a protected route.`);
    return NextResponse.redirect(new URL(`/login?redirect=${redirect}`, request.url));
  }
  
  console.log(`Middleware: Proceeding with request for path "${request.nextUrl.pathname}". Token presence: ${token ? 'EXISTS' : 'NOT FOUND'}`);
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/profile/:path*',
    '/dashboard/:path*',
    '/wallet/:path*',
    '/funds/:path*',
    '/exchange/:path*',
    '/login/:path*',
    '/register/:path*',
  ],
}; 