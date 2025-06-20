from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections, ProgrammingError
from django.contrib.auth import get_user_model
from django.db.models import Count
from accounts.models import UserProfile, UserDocument
from crypto.models import UserWallet
from transactions.models import Transaction, Exchange, Deposit, Withdrawal, Review
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Удаляет пользователя и все связанные с ним данные'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='ID пользователя или email (если не указано, будет предложен выбор из списка)',
            required=False
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет удалено, но не удалять',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Показать список пользователей',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run')
        list_users = options.get('list')
        
        # Если указан флаг --list, показываем список пользователей и выходим
        if list_users:
            self._list_users()
            return
        
        # Если user_id не указан, предлагаем выбрать пользователя из списка
        if not user_id:
            user = self._select_user_interactive()
            if not user:
                return
        else:
            # Пытаемся найти пользователя по ID или email
            try:
                # Сначала пробуем найти по ID
                try:
                    user_id_int = int(user_id)
                    user = User.objects.get(id=user_id_int)
                except (ValueError, User.DoesNotExist):
                    # Если не получилось, ищем по email
                    user = User.objects.get(email=user_id)
            except User.DoesNotExist:
                raise CommandError(f"Пользователь с ID или email '{user_id}' не найден")
                
        self.stdout.write(f"Найден пользователь: {user.email} (ID: {user.id})")
        
        # Если это тестовый запуск, показываем только информацию
        if dry_run:
            self._show_related_data(user)
            self.stdout.write(self.style.SUCCESS(
                f"Тестовый запуск завершен. Для удаления запустите команду без флага --dry-run"
            ))
            return
            
        # Если это не тестовый запуск, удаляем пользователя и все связанные данные
        try:
            with transaction.atomic():
                user_email = user.email
                user_id_val = user.id
                
                deleted_data = self._delete_user_data(user)
                
                self.stdout.write(self.style.SUCCESS(
                    f"Пользователь {user_email} (ID: {user_id_val}) и все связанные данные успешно удалены."
                ))
                
                # Выводим статистику удаленных данных
                for model_name, count in deleted_data.items():
                    if count > 0:
                        self.stdout.write(f"  - Удалено {count} записей из {model_name}")
        except Exception as e:
            raise CommandError(f"Ошибка при удалении пользователя: {str(e)}")
    
    def _show_related_data(self, user):
        """Показывает связанные с пользователем данные без удаления"""
        self.stdout.write(self.style.WARNING("Следующие данные будут удалены:"))
        
        tables_to_check = [
            ('accounts_userprofile', 'Профиль пользователя'),
            ('accounts_userdocument', 'Документы пользователя'),
            ('crypto_userwallet', 'Кошельки пользователя'),
            ('transactions_transaction', 'Транзакции'),
            ('transactions_exchange', 'Обмены валют'),
            ('transactions_deposit', 'Депозиты'),
            ('transactions_withdrawal', 'Выводы средств'),
            ('transactions_review', 'Отзывы'),
            ('transactions_transfer', 'Переводы'),
            ('account_emailaddress', 'Email адреса (allauth)'),
            ('socialaccount_socialaccount', 'Социальные аккаунты (allauth)')
        ]
        
        for table_name, display_name in tables_to_check:
            if self._table_exists(table_name):
                try:
                    with connections['default'].cursor() as cursor:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = %s", [user.id])
                        count = cursor.fetchone()[0]
                        if count > 0:
                            self.stdout.write(f"  - {display_name}: {count}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Ошибка при подсчете записей в {table_name}: {e}"))
    
    def _list_users(self):
        """Выводит список пользователей с количеством связанных данных"""
        users = User.objects.all().order_by('id')
        
        if not users.exists():
            self.stdout.write(self.style.WARNING("В базе данных нет пользователей."))
            return
        
        self.stdout.write(self.style.SUCCESS("Список пользователей в базе данных:"))
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'ID':<5} {'Email':<30} {'Имя пользователя':<20} {'Дата регистрации':<20}")
        self.stdout.write("-" * 80)
        
        for user in users:
            self.stdout.write(f"{user.id:<5} {user.email:<30} {user.username:<20} {user.date_joined.strftime('%Y-%m-%d %H:%M'):<20}")
        
        self.stdout.write("-" * 80)
        self.stdout.write(f"Всего пользователей: {users.count()}")
    
    def _select_user_interactive(self):
        """Интерактивный выбор пользователя из списка"""
        users = User.objects.all().order_by('id')
        
        if not users.exists():
            self.stdout.write(self.style.ERROR("В базе данных нет пользователей."))
            return None
        
        self.stdout.write(self.style.SUCCESS("Выберите пользователя для удаления:"))
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'№':<3} {'ID':<5} {'Email':<30} {'Имя пользователя':<20}")
        self.stdout.write("-" * 80)
        
        # Выводим список пользователей с номерами для выбора
        for i, user in enumerate(users, 1):
            self.stdout.write(f"{i:<3} {user.id:<5} {user.email:<30} {user.username:<20}")
        
        self.stdout.write("-" * 80)
        self.stdout.write("Введите номер пользователя для удаления (или 'q' для выхода): ")
        
        try:
            choice = input().strip()
            
            if choice.lower() == 'q':
                self.stdout.write("Операция отменена.")
                return None
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= users.count():
                    selected_user = users[choice_num - 1]
                    
                    # Запрашиваем подтверждение
                    self.stdout.write(f"Вы выбрали: {selected_user.email} (ID: {selected_user.id})")
                    self.stdout.write("Подтвердите удаление (y/n): ")
                    confirm = input().strip().lower()
                    
                    if confirm == 'y':
                        return selected_user
                    else:
                        self.stdout.write("Операция отменена.")
                        return None
                else:
                    self.stdout.write(self.style.ERROR(f"Некорректный выбор. Введите число от 1 до {users.count()}."))
                    return None
            except ValueError:
                self.stdout.write(self.style.ERROR("Некорректный ввод. Введите число."))
                return None
                
        except KeyboardInterrupt:
            self.stdout.write("\nОперация отменена.")
            return None
    
    def _table_exists(self, table_name):
        """Проверяет, существует ли таблица в базе данных"""
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM information_schema.tables WHERE table_name = %s", [table_name])
                return cursor.fetchone() is not None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Ошибка при проверке таблицы {table_name}: {e}"))
            return False

    def _safe_delete_sql(self, table_name, condition_column, condition_value):
        """Выполняет SQL DELETE только если таблица существует"""
        if not self._table_exists(table_name):
            self.stdout.write(self.style.WARNING(f"Таблица {table_name} не найдена, пропускаем."))
            return 0
        
        try:
            with connections['default'].cursor() as cursor:
                # Сначала подсчитаем количество строк для удаления
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {condition_column} = %s", [condition_value])
                count = cursor.fetchone()[0]
                
                # Затем удаляем
                if count > 0:
                    cursor.execute(f"DELETE FROM {table_name} WHERE {condition_column} = %s", [condition_value])
                    self.stdout.write(f"  - Удалено {count} записей из {table_name}")
                
                return count
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Ошибка при удалении из {table_name}: {e}"))
            return 0

    def _delete_user_data(self, user):
        """Удаляет все данные, связанные с пользователем, с проверкой существования таблиц"""
        deleted_data = {}
        
        # Строго определенный порядок удаления для соблюдения ограничений внешних ключей
        
        # 1. Отзывы пользователя
        deleted_data['Review'] = self._safe_delete_sql('transactions_review', 'user_id', user.id)
        
        # 2. Выводы средств
        deleted_data['Withdrawal'] = self._safe_delete_sql('transactions_withdrawal', 'user_id', user.id)
        
        # 3. Депозиты
        deleted_data['Deposit'] = self._safe_delete_sql('transactions_deposit', 'user_id', user.id)
        
        # 4. Обмены
        deleted_data['Exchange'] = self._safe_delete_sql('transactions_exchange', 'user_id', user.id)
        
        # 5. Переводы (если есть)
        deleted_data['Transfer'] = self._safe_delete_sql('transactions_transfer', 'user_id', user.id)
        
        # 6. Транзакции
        deleted_data['Transaction'] = self._safe_delete_sql('transactions_transaction', 'user_id', user.id)
        
        # 7. Кошельки
        deleted_data['UserWallet'] = self._safe_delete_sql('crypto_userwallet', 'user_id', user.id)
        
        # 8. Документы
        deleted_data['UserDocument'] = self._safe_delete_sql('accounts_userdocument', 'user_id', user.id)
        
        # 9. Профиль
        deleted_data['UserProfile'] = self._safe_delete_sql('accounts_userprofile', 'user_id', user.id)
        
        # 10. Email адреса (allauth)
        deleted_data['EmailAddress'] = self._safe_delete_sql('account_emailaddress', 'user_id', user.id)

        # 11. Социальные аккаунты (allauth)
        deleted_data['SocialAccount'] = self._safe_delete_sql('socialaccount_socialaccount', 'user_id', user.id)
        
        # 12. Наконец, удаляем самого пользователя
        user_table = User._meta.db_table
        deleted_data['User'] = self._safe_delete_sql(user_table, 'id', user.id)
        
        return deleted_data
