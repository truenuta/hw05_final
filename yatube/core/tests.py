from django.test import TestCase
from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        status = response.status_code
        self.assertEqual(status, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
