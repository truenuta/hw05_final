from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


class PostCreateFormTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='NoName')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
        )

    def test_post_form(self):
        """Создаётся новая запись в базе данных."""
        posts_cnt = Post.objects.count()
        form_data = {
            'text': 'Текст из формы'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_cnt + 1)
        self.assertTrue(Post.objects.filter(
            text='Текст из формы').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_form(self):
        """Происходит изменение поста."""
        form_data = {'text': 'Тестовый новый текст', 'group_id': self.group.id}
        posts_cnt = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_cnt)
        self.assertTrue(
            Post.objects.filter(text='Тестовый новый текст').exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
