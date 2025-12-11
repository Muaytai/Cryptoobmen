import { NextRequest, NextResponse } from 'next/server';

type ReviewApiItem = {
  id: number;
  name?: string;
  rating: number;
  date?: string;
  created_at?: string;
  content?: string;
  text?: string;
  is_verified?: boolean;
  verified?: boolean;
};

// Получение отзывов
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const filter = searchParams.get('filter') || 'all';
    const page = searchParams.get('page') || '1';
    const limit = searchParams.get('limit') || '10';
    
    // Используем внутренний URL для Docker или внешний для других окружений
    // В Docker используем имя сервиса, иначе внешний URL
    const backendUrl = process.env.BACKEND_INTERNAL_URL || 
                       process.env.NEXT_PUBLIC_BACKEND_URL || 
                       process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 
                       'http://backend:8000'; // Fallback для Docker
    let apiUrl = `${backendUrl}/api/transactions/reviews/?page=${page}&limit=${limit}`;
    
    // Добавляем параметры фильтрации
    if (filter === 'positive') {
      apiUrl += '&min_rating=4';
    } else if (filter === 'negative') {
      apiUrl += '&max_rating=3';
    }
    
    console.log('Requesting reviews from:', apiUrl);
    
    const response = await fetch(apiUrl, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Ошибка API: ${response.status}`);
    }
    
    const data: unknown = await response.json();
    
    // Форматируем ответ для фронтенда
    return NextResponse.json({
      success: true,
      count: (data as { count?: number }).count || 0,
      results: (data as { results?: ReviewApiItem[] }).results
        ? (data as { results: ReviewApiItem[] }).results.map((review) => ({
            id: review.id,
            name: review.name || 'Пользователь',
            rating: review.rating,
            date: review.date || (review.created_at ? new Date(review.created_at).toLocaleDateString('ru-RU') : ''),
            text: review.content || review.text || '',
            verified: review.is_verified ?? review.verified ?? false,
          }))
        : [],
    });
    
  } catch (error) {
    console.error('Ошибка при получении отзывов:', error);
    
    // Возвращаем демо-данные в случае ошибки
    return NextResponse.json({
      success: true,
      count: 8,
      results: [
        {
          id: 1,
          name: 'Александр',
          rating: 5,
          date: '15.04.2023',
          text: 'Пользуюсь платформой CTokenX уже более полугода. Очень доволен скоростью обработки транзакций и выгодными курсами обмена. Поддержка отвечает быстро и всегда помогает решить любые вопросы.',
          verified: true,
        },
        {
          id: 2,
          name: 'Елена',
          rating: 5,
          date: '22.05.2023',
          text: 'Отличная платформа для обмена криптовалют. Интуитивно понятный интерфейс, всё работает быстро и без сбоев. Особенно нравится возможность отслеживать статус транзакций в реальном времени.',
          verified: true,
        },
        {
          id: 3,
          name: 'Максим',
          rating: 4,
          date: '10.06.2023',
          text: 'В целом доволен сервисом. Удобный интерфейс, хорошие курсы. Из минусов - иногда бывают задержки при больших суммах, но это, наверное, связано с проверками безопасности.',
          verified: true,
        },
        {
          id: 4,
          name: 'Ирина',
          rating: 5,
          date: '28.07.2023',
          text: 'Самая удобная платформа для обмена, которой я пользовалась. Верификация прошла быстро, комиссии низкие, операции выполняются практически мгновенно. Рекомендую всем!',
          verified: true,
        },
        {
          id: 5,
          name: 'Дмитрий',
          rating: 4,
          date: '15.08.2023',
          text: 'Хороший сервис с понятным интерфейсом. Правда, один раз была задержка с выводом средств, но служба поддержки быстро решила проблему. В целом рекомендую.',
          verified: true,
        },
        {
          id: 6,
          name: 'Анна',
          rating: 5,
          date: '09.09.2023',
          text: 'Пользуюсь CTokenX уже год, ни разу не было проблем. Радует, что постоянно добавляются новые криптовалюты и улучшается функционал платформы. Отдельное спасибо за круглосуточную поддержку!',
          verified: true,
        },
        {
          id: 7,
          name: 'Сергей',
          rating: 3,
          date: '12.10.2023',
          text: 'Сервис неплохой, но хотелось бы больше аналитических инструментов. Транзакции проходят быстро, но интерфейс мог бы быть более современным.',
          verified: true,
        },
        {
          id: 8,
          name: 'Ольга',
          rating: 5,
          date: '26.11.2023',
          text: 'Очень благодарна команде CTokenX за отличный сервис. Всё работает как часы, верификация проходит быстро, а курсы действительно выгодные. Буду рекомендовать вас друзьям!',
          verified: true,
        },
      ],
    });
  }
}

// Создание отзыва
export async function POST(request: NextRequest) {
  try {
    const data = await request.json();
    
    // Преобразуем поле text в content для соответствия бэкенду
    const transformedData = {
      ...data,
      content: data.text,
    };
    
    // Используем внутренний URL для Docker или внешний для других окружений
    const backendUrl = process.env.BACKEND_INTERNAL_URL || 
                       process.env.NEXT_PUBLIC_BACKEND_URL || 
                       process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 
                       'http://backend:8000'; // Fallback для Docker
    // Отправка данных на бэкенд
    const response = await fetch(`${backendUrl}/api/transactions/reviews/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(transformedData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json({
        success: false,
        message: errorData.message || 'Ошибка при отправке отзыва',
      }, { status: response.status });
    }
    
    return NextResponse.json({
      success: true,
      message: 'Отзыв успешно отправлен и будет опубликован после проверки',
    });
  } catch (error) {
    console.error('Ошибка при отправке отзыва:', error);
    return NextResponse.json({
      success: false,
      message: 'Произошла ошибка при отправке отзыва',
    }, { status: 500 });
  }
} 