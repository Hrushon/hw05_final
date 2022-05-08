from django.test import Client, TestCase
from django.urls import reverse


class AboutPagesURLTests(TestCase):
    """Тестирует URL приложения."""

    def setUp(self):
        """Создание экземпляра клиента."""
        self.guest_client = Client()

    def test_about_urls(self):
        """Проверка доступности адресов приложения."""
        pages = (reverse('about:author'), reverse('about:tech'))
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.reason_phrase, 'OK')

    def test_about_urls_uses_correct_template(self):
        """Проверка использования URL-адресами шаблонов."""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
