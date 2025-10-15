# Руководство по управлению администраторами сайта

## Обзор

В Django admin добавлена функция для назначения администраторов сайта. Суперпользователи теперь могут назначать обычных пользователей администраторами сайта, которые получают специальные права для управления платформой.

## Что добавлено

- Новое булево поле `is_site_admin` в модели пользователя `accounts.models.User`.
- Метод `User.is_site_administrator()` для удобной проверки административных прав сайта (True, если `is_site_admin` или `is_superuser`).
- Обновление Django Admin (`accounts.admin.CustomUserAdmin`):
  - Показ колонки `is_site_admin` в списке пользователей (`list_display`).
  - Фильтр по `is_site_admin` (`list_filter`).
  - Поле `is_site_admin` в разделе Permissions (`fieldsets`).
  - Два массовых действия:
    - "Назначить администраторами сайта" — устанавливает `is_site_admin=True` для выбранных пользователей.
    - "Снять права администратора сайта" — устанавливает `is_site_admin=False`.
- Добавлены утилиты контроля доступа:
  - `accounts/decorators.py`: декораторы `@site_admin_required`, `@site_admin_or_staff_required`.
  - `accounts/mixins.py`: миксины `SiteAdminRequiredMixin`, `SiteAdminOrStaffRequiredMixin` для CBV/ViewSet.
- Примеры использования добавлены в `accounts/views.py` (эндпоинты-демо `admin_dashboard`, `admin_or_staff_dashboard`, пример ViewSet-ов с миксинами).
- Ручная миграция `accounts/migrations/0003_user_is_site_admin.py` для добавления колонки в БД.
- Тесты: `accounts/tests_admin.py` (проверка метода, поля и доступа в админку).

## Фронтенд: кнопка «Админ-панель» в личном кабинете

- В компоненте сайдбара профиля `frontend/src/app/(profile)/components/sidebar.tsx` добавлен пункт меню:
  - Заголовок: «Админ-панель»
  - Путь: `/admin`
  - Иконка: `public/images/profile/settings.svg`
- Кнопка отображается ТОЛЬКО если у текущего пользователя флаг `is_site_admin === true`.
  - Для этого на фронтенде используется стор `frontend/src/store/useAuthStore.ts` и поле `user.is_site_admin`.
  - Бэкенд возвращает это поле в `UserDetailsSerializer`.

Важно: кнопка ведет на фронтовой маршрут `/admin`. Доступ к нативной Django-админке остаётся недоступным для не-staff пользователей; текущая задача — только кнопка. Логику фронтовой админки добавим позже.

## Какие файлы изменены/добавлены

Изменены:
- `backend/accounts/models.py`
  - Добавлено поле:
    - `is_site_admin = models.BooleanField(default=False, verbose_name='Site Administrator', help_text='Designates this user as a site administrator who can manage the platform.')`
  - Добавлен метод:
    - `def is_site_administrator(self): return self.is_site_admin or self.is_superuser`
- `backend/accounts/admin.py`
  - В `CustomUserAdmin` добавлены `is_site_admin` в `list_display`, `list_filter`, `fieldsets` и добавлены `actions` (`make_site_admin`, `remove_site_admin`).
- `backend/accounts/views.py`
  - Импортированы декораторы/миксины и добавлены демонстрационные представления/вьюсеты.
- `backend/accounts/serializers.py`
  - Добавлено поле `is_site_admin` в `UserDetailsSerializer`.
- `frontend/src/store/useAuthStore.ts`
  - Добавлено поле `is_site_admin?: boolean` в интерфейс `User`.
- `frontend/src/app/(profile)/components/sidebar.tsx`
  - Добавлен пункт меню «Админ-панель» с условным отображением по `user?.is_site_admin`.

Добавлены:
- `backend/accounts/migrations/0003_user_is_site_admin.py`
- `backend/accounts/decorators.py`
- `backend/accounts/mixins.py`
- `backend/accounts/tests_admin.py`

## Новые поля и функции

### 1. Поле `is_site_admin` в модели User

- **Тип**: BooleanField
- **По умолчанию**: False
- **Описание**: Обозначает пользователя как администратора сайта
- **Отличие от `is_staff`**: `is_staff` дает доступ к Django admin, `is_site_admin` - специальные права для управления платформой

### 2. Метод `is_site_administrator()`

```python
user.is_site_administrator()  # Возвращает True если user.is_site_admin или user.is_superuser
```

### 3. Админские действия

В Django admin добавлены два действия для массового управления:

- **"Назначить администраторами сайта"** - устанавливает `is_site_admin=True` для выбранных пользователей
- **"Снять права администратора сайта"** - устанавливает `is_site_admin=False` для выбранных пользователей

## Использование в коде

### Декораторы

```python
from accounts.decorators import site_admin_required, site_admin_or_staff_required

@site_admin_required
def admin_only_view(request):
    # Доступно только администраторам сайта
    pass

@site_admin_or_staff_required  
def admin_or_staff_view(request):
    # Доступно администраторам сайта или персоналу
    pass
```

### Миксины для ViewSet

```python
from accounts.mixins import SiteAdminRequiredMixin, SiteAdminOrStaffRequiredMixin

class AdminOnlyViewSet(SiteAdminRequiredMixin, viewsets.ModelViewSet):
    # Только для администраторов сайта
    pass

class AdminOrStaffViewSet(SiteAdminOrStaffRequiredMixin, viewsets.ModelViewSet):
    # Для администраторов сайта или персонала
    pass
```

### Проверка прав в шаблонах

```html
{% if user.is_site_administrator %}
    <p>Вы администратор сайта</p>
{% endif %}

{% if user.is_site_admin %}
    <p>У вас есть права администратора сайта</p>
{% endif %}
```

## Миграция

Создана миграция `0003_user_is_site_admin.py` для добавления нового поля в базу данных.

Для применения миграции выполните:
```bash
python manage.py migrate accounts
```

Если сервер запущен в WSL, выполните в том же окружении:

```bash
cd /mnt/c/Users/userSL0925/.cursor/Cryptoobmen/backend
source venv/bin/activate
python manage.py showmigrations accounts
# Если 0002 ломается из-за отсутствия старого столбца has_2fa, пометьте её как fake:
python manage.py migrate accounts 0002 --fake
# Примените миграцию, создающую колонку is_site_admin
python manage.py migrate accounts
```

Проверьте, что `accounts.0003_user_is_site_admin` отмечена как применённая (OK/[X]).

## Права доступа

### Иерархия прав:

1. **Суперпользователь** (`is_superuser=True`)
   - Все права Django admin
   - Все права администратора сайта
   - Доступ ко всем функциям платформы

2. **Администратор сайта** (`is_site_admin=True`)
   - Специальные права для управления платформой
   - Доступ к функциям администрирования сайта
   - НЕ имеет автоматически доступ к Django admin (если `is_staff=False`)

3. **Персонал** (`is_staff=True`)
   - Доступ к Django admin
   - НЕ имеет автоматически права администратора сайта

4. **Обычный пользователь**
   - Только базовые права

## Примеры использования

### В представлениях

```python
def some_admin_view(request):
    if not request.user.is_site_administrator():
        return HttpResponseForbidden("Доступ запрещен")
    
    # Логика для администраторов сайта
    pass
```

### В сериализаторах

```python
class UserSerializer(serializers.ModelSerializer):
    is_site_administrator = serializers.SerializerMethodField()
    
    def get_is_site_administrator(self, obj):
        return obj.is_site_administrator()
```

### В API фильтрации

```python
class UserViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_site_administrator():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
```

## Безопасность

- Все проверки прав выполняются на серверной стороне
- Декораторы и миксины автоматически проверяют аутентификацию
- При отсутствии прав возвращается HTTP 403 Forbidden
- Сообщения об ошибках локализованы

## Мониторинг

В Django admin можно легко отслеживать:
- Кто является администратором сайта (колонка `is_site_admin`)
- Фильтрация по статусу администратора
- Массовые операции с правами администратора

## Как пользоваться

- Через Django Admin:
  1) Зайдите в раздел `Users`.
  2) Отметьте пользователей галочками.
  3) В выпадающем списке действий выберите:
     - "Назначить администраторами сайта" — дать права (`is_site_admin=True`).
     - "Снять права администратора сайта" — отобрать права (`is_site_admin=False`).
  4) Можно также открыть карточку пользователя и включить флаг `Site Administrator` в Permissions.

- В коде:

```python
# Проверка прав
if request.user.is_site_administrator():
    # Логика для администраторов сайта
    ...

# Декораторы
from accounts.decorators import site_admin_required, site_admin_or_staff_required

@site_admin_required
def admin_view(request):
    ...

@site_admin_or_staff_required
def admin_or_staff_view(request):
    ...

# Миксины для CBV/ViewSet
from accounts.mixins import SiteAdminRequiredMixin, SiteAdminOrStaffRequiredMixin

class AdminOnlyView(SiteAdminRequiredMixin, View):
    ...

class AdminOnlyViewSet(SiteAdminRequiredMixin, viewsets.ModelViewSet):
    ...
```

## Отличие от is_staff

- `is_staff` — доступ в Django Admin (панель администратора Django).
- `is_site_admin` — доменно-специфичные права управления платформой (могут использоваться в API/вьюхах, не дают доступ к Django Admin сами по себе).

Часто для работы в Django Admin нужно `is_staff=True`. Для расширенных действий в вашем приложении используйте проверку `is_site_administrator()`.

## Откат изменений (при необходимости)

- В админке снимите флаг `Site Administrator` или массовым действием выполните "Снять права администратора сайта".
- Для БД: можно откатить миграцию `accounts` до состояния до 0003 (команда `python manage.py migrate accounts 0002`).

## Рекомендации

1. **Назначайте администраторов сайта осторожно** - они получают значительные права
2. **Регулярно проверяйте список администраторов** в Django admin
3. **Используйте логирование** для отслеживания действий администраторов
4. **Создавайте отдельные группы** для разных уровней доступа
5. **Тестируйте права доступа** перед развертыванием в продакшене
