import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Проверка работы прокси к Django бэкенду
    const response = await fetch('http://localhost:8000/api/accounts/users/', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.text();
    console.log('Ответ от бэкенда:', response.status, data);

    return NextResponse.json({
      status: response.status,
      statusText: response.statusText,
      responseText: data,
    });
  } catch (error) {
    console.error('Ошибка при запросе к API:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Неизвестная ошибка' },
      { status: 500 }
    );
  }
} 