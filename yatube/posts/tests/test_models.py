from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестирует модели приложения Post."""

    @classmethod
    def setUpClass(cls):
        """Создает экземпляры User и Group."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        """Прибирает за собой."""
        super().tearDownClass()
        cls.user.delete()
        cls.group.delete()
        cls.post.delete()

    def test_models_have_correct_object_names(self):
        """Проверяет, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        field_str = {
            post: post.text[:15],
            post.group: PostModelTest.group.title
        }
        for field, expected_value in field_str.items():
            with self.subTest(field=field):
                self.assertEqual(str(field), expected_value)

    def test_verbose_name(self):
        """Проверяет verbose name."""
        post = PostModelTest.post
        for i in (post, post.group):
            if i == post:
                field_verboses = {
                    'pub_date': 'Дата создания поста',
                    'text': 'Текст поста',
                    'author': 'Автор',
                    'group': 'Группа',
                }
            else:
                field_verboses = {
                    'title': 'Название группы',
                    'description': 'Описание группы',
                }
            for field, expected_value in field_verboses.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        i._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """Проверяет help_text."""
        post = PostModelTest.post
        for i in (post, post.group):
            if i == post:
                field_help_texts = {
                    'group': 'Группа, к которой будет относиться пост',
                    'text': 'Введите текст',
                }
            else:
                field_help_texts = {
                    'title': 'Введите название группы',
                    'description': 'Введите описание группы',
                }
            for field, expected_value in field_help_texts.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        i._meta.get_field(field).help_text, expected_value)
