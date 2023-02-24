from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.paginator import Page
from django.core.cache import cache

from posts.models import Post, Group, User, Follow
from posts.forms import PostForm, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Anya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}
            ): 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.author = User.objects.create_user(username='author')

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        expected = list(Post.objects.filter(author_id=self.user.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_show_correct_contecst(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        fields = {response.context.get('post').text: self.post.text,
                  response.context.get('post').author: self.post.author,
                  response.context.get('post').group: self.post.group
                  }
        for value, expected in fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_check_group_in_pages(self):
        """Пост создан на страницах с выбранной группой"""
        fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={'slug': self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={'username': self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Пост с группой не попап в чужую группу."""
        fields = {
            reverse(
                "posts:group_list", kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_check_cache(self):
        """Тестирование работы кеша."""
        response1 = self.authorized_client.get(reverse('posts:index'))
        cnt1 = Post.objects.count()
        res1 = response1.content
        form_data = {
            'text': 'Тестируем кеш'
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response2 = self.authorized_client.get(reverse('posts:index'))
        res2 = response2.content
        self.assertEqual(res1, res2)
        cache.clear()
        cnt2 = Post.objects.count()
        self.assertNotEqual(cnt1, cnt2)


class PaginatorViewsTest(TestCase):
    TOTAL_AMOUNT_OF_POSTS = 13
    POSTS_ON_FIRST_PAGE = 10
    POSTS_ON_SECOND_PAGE = TOTAL_AMOUNT_OF_POSTS - POSTS_ON_FIRST_PAGE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Anya')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тестовая группа для тестирования пагинатора',
        )
        Post.objects.bulk_create([
            Post(text=f'Тестовый текст для тестирования пагинатора {i}',
                 author=cls.author, group=cls.group
                 ) for i in range(cls.TOTAL_AMOUNT_OF_POSTS)
        ])

    def setUp(self):
        self.urls_expected_post_number = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=['Anya'])]

    def test_paginator_first_page(self):
        """Тестируем пагинатор 1-ю страницу"""
        for url in self.urls_expected_post_number:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertEqual(
                    len(page_obj), self.POSTS_ON_FIRST_PAGE
                )

    def test_paginator_second_page(self):
        """Тестируем пагинатор 2-ю страницу"""
        for url in self.urls_expected_post_number:
            with self.subTest(url=url):
                response2 = self.client.get(url + '?page=2')
                self.assertEqual(response2.status_code, HTTPStatus.OK)
                page_obj2 = response2.context.get('page_obj')
                self.assertIsNotNone(page_obj2)
                self.assertIsInstance(page_obj2, Page)
                self.assertEqual(
                    len(page_obj2), self.POSTS_ON_SECOND_PAGE
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Anya')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тестирование загрузки изображения',
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        obj = response.context["post"]
        self.assertEqual(obj.image, self.post.image)

    def test_image_on_main_page(self):
        """Картинка передается на главную страницу"""
        response = self.guest_client.get(
            reverse("posts:index")
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_on_profile_page(self):
        """Картинка передается на профайл"""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый пост",
                image="posts/small.gif").exists()
        )


class CommentsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Anya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="Тестовый комментарий",
        )

    def setUp(self):
        self.other_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentsTests.user)
        self.author = User.objects.create_user(username='author')

    def test_only_authorized_client_enable_to_add_comment(self):
        """Авторизированный пользователь можем оставлить комментарий
        и будет перенапрвлен на страницу поста"""
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))

    def test_authorized_client_add_comment_correctly(self):
        comments_count = Comment.objects.count()
        form_data = {"text": "Новый тестовый коммент"}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text="Новый тестовый коммент"
        ).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)


class FollowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='Anya')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.create_user(username='author')
        self.follow = reverse(
            'posts:profile_follow',
            kwargs={'username': self.author})
        self.unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author})
        self.follow_index = reverse('posts:follow_index')

    def test_authorized_client_enable_to_follow_and_unfollow(self):
        """Авторизированный пользователь может подписываться
        и отписываться"""
        followers_before = Follow.objects.count()
        self.authorized_client.get(self.follow)
        self.assertEqual(Follow.objects.count(), followers_before + 1)
        self.authorized_client.get(self.unfollow)
        self.assertEqual(Follow.objects.count(), followers_before)

    def test_new_post_appears_for_followers(self):
        """Новая запись автора
        появляется у его подписчиков"""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        post = Post.objects.create(
            author=self.author,
            text='Тестовый пост для теста подписок'
        )
        response = self.authorized_client.get(self.follow_index)
        self.assertEqual(response.context['page_obj'][0], post)

    def test_new_post_doesnt_appears_for_followers(self):
        """Новая запись автора не
        появляется у его неподписчиков"""
        Post.objects.create(
            author=self.author,
            text='Тестовый пост для теста подписок'
        )
        response = self.authorized_client.get(self.follow_index)
        self.assertEqual(len(response.context['page_obj']), 0)
