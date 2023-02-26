from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        self.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif', content=self.small_gif, content_type='image/gif'
        )

    def test_post_form(self):
        """Создаётся новая запись в базе данных."""
        posts_cnt = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'image': self.uploaded

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
