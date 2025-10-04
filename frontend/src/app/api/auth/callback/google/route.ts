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
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        client_id: authConfig.google.clientId,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        redirect_uri: authConfig.google.redirectUri,
        grant_type: 'authorization_code',
      }),
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      throw new Error('Failed to get access token');
    }

    // Получение информации о пользователе
    const userResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${tokenData.access_token}`,
      },
    });

    const userData = await userResponse.json();

    if (!userResponse.ok) {
      throw new Error('Failed to get user data');
    }

    // Здесь нужно отправить данные на бэкенд для создания/входа пользователя
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: userData.email,
        name: userData.name,
        googleId: userData.id,
      }),
    });

    if (!backendResponse.ok) {
      throw new Error('Failed to authenticate with backend');
    }

    const { token } = await backendResponse.json();

    // Редирект на главную с токеном
    return NextResponse.redirect(`${process.env.NEXT_PUBLIC_URL}/dashboard?token=${token}`);
  } catch (error) {
    console.error('Google auth error:', error);
    return NextResponse.redirect('/login?error=auth_failed');
  }
} 