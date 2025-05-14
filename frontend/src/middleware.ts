import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Получаем путь текущего запроса
  const path = request.nextUrl.pathname;
  
  // Проверяем куки авторизации, поддерживая разные типы куки (Django, Next.js)
  const isAuthenticated = 
    request.cookies.has('sessionid') || 
    request.cookies.has('dj_session_id') || 
    request.cookies.has('auth_token') ||
    (request.cookies.has('csrftoken') && request.cookies.has('next-auth.session-token'));
  
  // Проверяем наличие флага disableAutoLogin в cookies
  const disableAutoLogin = request.cookies.has('disableAutoLogin');
  
  // Если установлен флаг disableAutoLogin, считаем пользователя неавторизованным
  const effectiveIsAuthenticated = isAuthenticated && !disableAutoLogin;
  
  // Маршруты, требующие авторизации
  const authRoutes = ['/profile', '/dashboard', '/wallet', '/exchange/history'];
  
  // Страница регистрации должна быть всегда доступна
  if (path === '/register') {
    return NextResponse.next();
  }
  
  // Если пользователь пытается получить доступ к защищенному маршруту без авторизации
  if (authRoutes.some(route => path.startsWith(route)) && !effectiveIsAuthenticated) {
    console.log('Перенаправление на страницу входа: пользователь не авторизован');
    const redirectUrl = new URL('/login', request.url);
    // Сохраняем оригинальный путь для перенаправления после входа
    if (path !== '/profile') {
      redirectUrl.searchParams.set('redirect', path.substring(1));
    } else {
      // Для профиля не нужен дополнительный параметр, т.к. это путь по умолчанию
      redirectUrl.searchParams.set('redirect', 'profile');
    }
    return NextResponse.redirect(redirectUrl);
  }
  
  // Если авторизованный пользователь пытается попасть на страницу входа
  if (path === '/login' && effectiveIsAuthenticated) {
    const referer = request.headers.get('referer') || '';
    
    // Проверяем referer, чтобы определить, была ли нажата кнопка "Войти"
    const isDirectLoginAttempt = referer && new URL(referer).pathname !== '/login';
    
    // Если это не прямая попытка входа через кнопку (или нет referer), перенаправляем в профиль
    if (!isDirectLoginAttempt) {
      console.log('Перенаправление на профиль: пользователь уже авторизован');
      return NextResponse.redirect(new URL('/profile', request.url));
    }
    
    // Иначе позволяем продолжить на страницу входа
    console.log('Позволяем доступ к странице входа, несмотря на авторизацию');
  }
  
  return NextResponse.next();
}

// Указываем расширенный список маршрутов для middleware
export const config = {
  matcher: [
    '/profile/:path*', 
    '/dashboard/:path*',
    '/wallet/:path*',
    '/exchange/history/:path*',
    '/login',
    '/register'
  ],
}; 