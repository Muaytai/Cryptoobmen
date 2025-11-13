from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from .models import User

User = get_user_model()


class SiteAdminTestCase(TestCase):
    """Тесты для функциональности администраторов сайта"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        
        # Создаем обычного пользователя
        self.regular_user = User.objects.create_user(
            email='regular@test.com',
            username='regular',
            password='testpass123'
        )
        
        # Создаем администратора сайта
        self.site_admin = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass123',
            is_site_admin=True
        )
        
        # Создаем суперпользователя
        self.superuser = User.objects.create_superuser(
            email='super@test.com',
            username='super',
            password='testpass123'
        )
    
    def test_is_site_administrator_method(self):
        """Тест метода is_site_administrator()"""
        # Обычный пользователь не является администратором сайта
        self.assertFalse(self.regular_user.is_site_administrator())
        
        # Администратор сайта является администратором сайта
        self.assertTrue(self.site_admin.is_site_administrator())
        
        # Суперпользователь является администратором сайта
        self.assertTrue(self.superuser.is_site_administrator())
    
    def test_site_admin_field(self):
        """Тест поля is_site_admin"""
        # По умолчанию False
        self.assertFalse(self.regular_user.is_site_admin)
        
        # Можно установить True
        self.regular_user.is_site_admin = True
        self.regular_user.save()
        self.assertTrue(self.regular_user.is_site_admin)
    
    def test_admin_interface_access(self):
        """Тест доступа к админке"""
        # Обычный пользователь не может войти в админку
        self.client.login(email='regular@test.com', password='testpass123')
        response = self.client.get('/admin/')
        self.assertNotEqual(response.status_code, 200)
        
        # Администратор сайта без is_staff не может войти в админку
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get('/admin/')
        self.assertNotEqual(response.status_code, 200)
        
        # Суперпользователь может войти в админку
        self.client.login(email='super@test.com', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_site_admin_with_staff_access(self):
        """Тест администратора сайта с правами персонала"""
        # Даем администратору сайта права персонала
        self.site_admin.is_staff = True
        self.site_admin.save()
        
        self.client.login(email='admin@test.com', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_creation_with_site_admin(self):
        """Тест создания пользователя с правами администратора сайта"""
        user = User.objects.create_user(
            email='newadmin@test.com',
            username='newadmin',
            password='testpass123',
            is_site_admin=True
        )
        
        self.assertTrue(user.is_site_admin)
        self.assertTrue(user.is_site_administrator())
    
    def test_full_name_display_property(self):
        """Тест свойства full_name_display"""
        # С полным именем
        self.regular_user.full_name = "Иван Иванов"
        self.regular_user.save()
        self.assertEqual(self.regular_user.full_name_display, "Иван Иванов")
        
        # Без полного имени - возвращает username
        self.regular_user.full_name = ""
        self.regular_user.save()
        self.assertEqual(self.regular_user.full_name_display, "regular")
