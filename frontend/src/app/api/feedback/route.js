import { NextResponse } from 'next/server';

// В реальном проекте здесь будет взаимодействие с базой данных
// Пока сохраняем отзывы в памяти (для демонстрации)
let feedbacks = [];

export async function POST(request) {
  try {
    const data = await request.json();
    
    // Валидация данных
    if (!data.name || !data.email || !data.text || !data.rating) {
      return NextResponse.json(
        { success: false, message: 'Необходимо заполнить все обязательные поля' },
        { status: 400 }
      );
    }
    
    // Проверка корректности email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
      return NextResponse.json(
        { success: false, message: 'Некорректный email' },
        { status: 400 }
      );
    }
    
    // Дополняем данные отзыва
    const newFeedback = {
      id: Date.now(), // Генерируем временный ID
      name: data.name,
      email: data.email,
      rating: data.rating,
      text: data.text,
      date: new Date().toLocaleDateString('ru-RU'),
      verified: false, // По умолчанию отзыв не верифицирован (требует модерации)
      createdAt: new Date().toISOString()
    };
    
    // Сохраняем отзыв (в реальном проекте здесь будет сохранение в БД)
    feedbacks.push(newFeedback);
    
    // В реальном проекте здесь могут быть дополнительные действия:
    // - Отправка уведомления администратору о новом отзыве
    // - Логирование действия
    // - Сохранение в базу данных
    
    return NextResponse.json({ 
      success: true, 
      message: 'Отзыв успешно отправлен',
      feedback: newFeedback
    });
    
  } catch (error) {
    console.error('Ошибка при обработке отзыва:', error);
    return NextResponse.json(
      { success: false, message: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
}

// Эндпоинт для получения всех отзывов (обычно с пагинацией)
export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Получаем параметры запроса для фильтрации и пагинации
    const filter = searchParams.get('filter') || 'all';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    
    // Фильтрация отзывов
    let filteredFeedbacks = [...feedbacks];
    if (filter === 'positive') {
      filteredFeedbacks = feedbacks.filter(feedback => feedback.rating >= 4);
    } else if (filter === 'negative') {
      filteredFeedbacks = feedbacks.filter(feedback => feedback.rating < 4);
    }
    
    // Сортировка по дате (сначала новые)
    filteredFeedbacks.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
    // Пагинация
    const startIndex = (page - 1) * limit;
    const endIndex = page * limit;
    const paginatedFeedbacks = filteredFeedbacks.slice(startIndex, endIndex);
    
    // Информация о пагинации для фронтенда
    const pagination = {
      total: filteredFeedbacks.length,
      pages: Math.ceil(filteredFeedbacks.length / limit),
      currentPage: page,
      limit
    };
    
    return NextResponse.json({
      success: true,
      feedbacks: paginatedFeedbacks,
      pagination
    });
    
  } catch (error) {
    console.error('Ошибка при получении отзывов:', error);
    return NextResponse.json(
      { success: false, message: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
} 