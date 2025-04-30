from django.core.management.base import BaseCommand
from transactions.models import Review
from django.utils import timezone


class Command(BaseCommand):
    help = 'Создает тестовые отзывы для демонстрации'

    def handle(self, *args, **options):
        reviews_data = [
            {
                'name': 'Александр',
                'email': 'alex@example.com',
                'rating': 5,
                'content': 'Пользуюсь платформой уже более полугода. Очень доволен скоростью обработки транзакций и выгодными курсами обмена.',
                'is_verified': True,
                'is_published': True,
                'is_featured': True,
            },
            {
                'name': 'Елена',
                'email': 'elena@example.com',
                'rating': 5,
                'content': 'Отличная платформа для обмена криптовалют. Интуитивно понятный интерфейс, всё работает быстро и без сбоев.',
                'is_verified': True,
                'is_published': True,
                'is_featured': True,
            },
            {
                'name': 'Максим',
                'email': 'max@example.com',
                'rating': 4,
                'content': 'В целом доволен сервисом. Удобный интерфейс, хорошие курсы. Рекомендую всем!',
                'is_verified': True,
                'is_published': True,
                'is_featured': True,
            },
            {
                'name': 'Ирина',
                'email': 'irina@example.com',
                'rating': 5,
                'content': 'Самая удобная платформа для обмена, которой я пользовалась. Верификация прошла быстро, комиссии низкие, операции выполняются практически мгновенно. Рекомендую всем!',
                'is_verified': True,
                'is_published': True,
                'is_featured': False,
            },
            {
                'name': 'Дмитрий',
                'email': 'dmitry@example.com',
                'rating': 4,
                'content': 'Хороший сервис с понятным интерфейсом. Правда, один раз была задержка с выводом средств, но служба поддержки быстро решила проблему. В целом рекомендую.',
                'is_verified': True,
                'is_published': True,
                'is_featured': False,
            },
            {
                'name': 'Анна',
                'email': 'anna@example.com',
                'rating': 5,
                'content': 'Пользуюсь уже год, ни разу не было проблем. Радует, что постоянно добавляются новые криптовалюты и улучшается функционал платформы. Отдельное спасибо за круглосуточную поддержку!',
                'is_verified': True,
                'is_published': True,
                'is_featured': False,
            },
            {
                'name': 'Сергей',
                'email': 'sergey@example.com',
                'rating': 3,
                'content': 'Сервис неплохой, но хотелось бы больше аналитических инструментов. Транзакции проходят быстро, но интерфейс мог бы быть более современным.',
                'is_verified': True,
                'is_published': True,
                'is_featured': False,
            },
            {
                'name': 'Ольга',
                'email': 'olga@example.com',
                'rating': 5,
                'content': 'Очень благодарна команде за отличный сервис. Всё работает как часы, верификация проходит быстро, а курсы действительно выгодные. Буду рекомендовать вас друзьям!',
                'is_verified': True,
                'is_published': True,
                'is_featured': False,
            },
        ]

        # Очищаем существующие отзывы перед добавлением новых
        Review.objects.all().delete()
        
        # Создаем новые отзывы
        for data in reviews_data:
            Review.objects.create(**data)
        
        self.stdout.write(self.style.SUCCESS(f'Успешно создано {len(reviews_data)} тестовых отзывов')) 