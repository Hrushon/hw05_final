import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Тестирует View приложения."""

    @classmethod
    def setUpClass(cls):
        """Создание экземпляра Post и Group."""
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
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.uploaded_1 = SimpleUploadedFile(
            name='small1.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        # Константы для создания/поиска поста по id
        # и проверке его после изменения
        cls.TEST_ONE = 1
        cls.TEST_TWO = 2

    @classmethod
    def tearDownClass(cls):
        """Прибирает за собой."""
        super().tearDownClass()
        cls.user.delete()
        cls.group.delete()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание авторизованного клиента."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_create(self):
        """Проверка сохранения поста в БД."""
        form_data = {
            'text': 'Прыг-Скок',
            'group': self.TEST_ONE,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяет что изменилось количество постов в БД
        self.assertEqual(Post.objects.count(), self.TEST_TWO)

        # Проверяет что пост корректно создан
        response_test = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'id': self.TEST_TWO})
        )
        object = response_test.context.get('post')
        self.assertEqual(object.author.username, 'auth')
        self.assertEqual(object.text, 'Прыг-Скок')
        self.assertEqual(object.group.title, 'Тестовая группа')
        self.assertEqual(object.image, 'posts/small.gif')
        self.assertIsNotNone(object.pub_date)

    def test_edit(self):
        """Проверка изменения поста в БД."""
        form_data = {
            'text': 'Скок-Прыг, Прыг-Скок',
            'group': self.group.id,
            'image': self.uploaded_1,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response_test = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'id': self.post.id})
        )

        # Проверяет что пост корректно изменен
        object = response_test.context.get('post')
        self.assertEqual(object.author.username, 'auth')
        self.assertEqual(object.text, 'Скок-Прыг, Прыг-Скок')
        self.assertEqual(object.group.title, 'Тестовая группа')
        self.assertEqual(object.image, 'posts/small1.gif')
        self.assertIsNotNone(object.pub_date)

        # Проверяет что количество постов в БД не изменилось
        self.assertEqual(Post.objects.count(), self.TEST_ONE)

    def test_comment(self):
        """Проверка комментирования поста."""
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяет что комментарий корректно создан
        response_test = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'id': self.post.id})
        )
        object = response_test.context['comments']
        # Проверяет что изменилось количество комментариев
        self.assertEqual(object.count(), self.TEST_ONE)

        object = object[0]
        self.assertEqual(object.author.username, 'auth')
        self.assertEqual(object.text, 'Тестовый коммент')
        self.assertEqual(object.post.text, 'Тестовый пост')
        self.assertIsNotNone(object.created)
