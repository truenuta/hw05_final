from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='SomeName')
        self.author = User.objects.create_user(username='author')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )

        self.urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        ]

        self.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.unexisting_page = '/unexisting_page/'
        self.create_page = '/create/'
        self.post_edit = f'/posts/{self.post.id}/edit/'
        self.post_detail_url = f'/posts/{self.post.pk}/'
        self.profile = f"/profile/{self.user}/"

    def test_url_http_status(self):
        """Проверяем доступность страниц
        для неавторизированному пользователю"""
        for address in self.urls:
            with self.subTest('NOTauthorized_client', address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_non_existing_page(self):
        """Несущетсвующая страница"""
        response = self.authorized_client.get(self.unexisting_page)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_exists(self):
        """Страница create доступна только авторизированному пользователю"""
        with self.subTest('authorized_client', address=self.create_page):
            response = self.authorized_client.get(self.create_page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists(self):
        """Страница create доступна только авторизированному пользователю"""
        with self.subTest('authorized_client', address=self.create_page):
            response = self.authorized_client.get(self.create_page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists(self):
        """Страница post_edit доступна только автору поста"""
        response = self.author_client.get(self.post_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_create_page_redirect_guest_client(self):
        """Страница create перенаправит неавторизированного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get(self.create_page, follow=True)
        self.assertRedirects(
            response, reverse('users:login')
            + '?next=' + reverse('posts:post_create'))

    def test_post_edit_redirect_author_to_post_detail(self):
        """Страница posts/{post.id}/edit перенаправит пользователя
        (автора) на страницу c деталями поста.
        """
        response = self.authorized_client.get(self.post_edit, follow=True)
        self.assertRedirects(response, self.post_detail_url)
