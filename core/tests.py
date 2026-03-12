from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class IndexViewTests(TestCase):
    """Проверка главной страницы и редиректа неавторизованных."""

    def setUp(self):
        self.client = Client()

    def test_index_requires_login(self):
        """Главная перенаправляет неавторизованного на логин."""
        response = self.client.get(reverse('index'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')) or 'login' in response.url)

    def test_login_page_accessible(self):
        """Страница входа доступна без авторизации."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)


class URLResolveTests(TestCase):
    """Проверка разрешения основных URL."""

    def test_index_url_resolves(self):
        self.assertEqual(reverse('index'), '/')

    def test_login_url_resolves(self):
        self.assertEqual(reverse('login'), '/login/')
