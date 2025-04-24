import { NextResponse } from 'next/server';
import { authConfig } from '@/config/auth';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');

  if (!code) {
    return NextResponse.redirect('/login?error=no_code');
  }

  try {
    // Обмен кода на токены
    const tokenResponse = await fetch('https://oauth.yandex.ru/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        client_id: authConfig.yandex.clientId,
        client_secret: process.env.YANDEX_CLIENT_SECRET || '',
      }),
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      throw new Error('Failed to get access token');
    }

    // Получение информации о пользователе
    const userResponse = await fetch('https://login.yandex.ru/info', {
      headers: {
        Authorization: `OAuth ${tokenData.access_token}`,
      },
    });

    const userData = await userResponse.json();

    if (!userResponse.ok) {
      throw new Error('Failed to get user data');
    }

    // Отправка данных на бэкенд
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/yandex`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: userData.default_email,
        name: userData.real_name || userData.display_name,
        yandexId: userData.id,
      }),
    });

    if (!backendResponse.ok) {
      throw new Error('Failed to authenticate with backend');
    }

    const { token } = await backendResponse.json();

    // Редирект на главную с токеном
    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_URL}/dashboard?token=${token}`);
  } catch (error) {
    console.error('Yandex auth error:', error);
    return NextResponse.redirect('/login?error=auth_failed');
  }
} 