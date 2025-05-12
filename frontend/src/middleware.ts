import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Логика middleware не требуется в данном случае, 
  // так как Next.js автоматически обрабатывает маршруты с группировкой
  return NextResponse.next();
}

// Указываем на каких путях будет работать middleware (пустой, так как редирект не нужен)
export const config = {
  matcher: [],
}; 