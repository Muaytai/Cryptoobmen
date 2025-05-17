import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const authToken = request.cookies.get('auth-token');
  const isAuthPage = request.nextUrl.pathname.startsWith('/login') || 
                    request.nextUrl.pathname.startsWith('/register');
  
  // Если это страница авторизации и есть force_login параметр, пропускаем
  if (isAuthPage && request.nextUrl.searchParams.get('force_login') === 'true') {
    return NextResponse.next();
  }

  // Если пользователь авторизован (есть токен)
  if (authToken?.value) {
    // Если пытается зайти на страницы авторизации, редиректим на профиль
    if (isAuthPage) {
      console.log('Перенаправление на профиль: пользователь уже авторизован');
      const response = NextResponse.redirect(new URL('/profile/', request.url));
      // Копируем токен в новый ответ
      response.cookies.set('auth-token', authToken.value, {
        path: '/',
        maxAge: 2592000, // 30 дней
        httpOnly: false,
      });
      return response;
    }
    // Иначе пропускаем запрос
    const response = NextResponse.next();
    // Копируем токен в новый ответ
    response.cookies.set('auth-token', authToken.value, {
      path: '/',
      maxAge: 2592000, // 30 дней
      httpOnly: false,
    });
    return response;
  }

  // Если пользователь не авторизован
  if (!authToken?.value) {
    // Если пытается зайти на защищенные страницы
    if (request.nextUrl.pathname.startsWith('/profile') || 
        request.nextUrl.pathname.startsWith('/dashboard')) {
      return NextResponse.redirect(new URL('/login/', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/profile/:path*',
    '/dashboard/:path*',
    '/login/:path*',
    '/register/:path*',
  ],
}; 