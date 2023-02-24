from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Это тестовый пост в проекте Яндекс Практикум',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group_str = self.group.title
        with self.subTest(field=group_str):
            self.assertEqual(str(self.group), group_str)
        post_str = self.post.text[:15]
        with self.subTest(field=post_str):
            self.assertEqual(str(self.post), post_str)
