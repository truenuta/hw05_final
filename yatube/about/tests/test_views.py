from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class AboutViewTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls(self):
        """Проверяем доступность по адресам"""
        templates_url = ['about:author', 'about:tech']
        for adress in templates_url:
            with self.subTest(adress):
                response = self.guest_client.get(reverse(adress))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_patterns(self):
        """Проверяем, что запрос напрявляет к верному шаблону"""
        templates_url_names = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(url))
                self.assertTemplateUsed(response, template)
