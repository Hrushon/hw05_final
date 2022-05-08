import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    """Тестирует View приложения."""

    @classmethod
    def setUpClass(cls):
        """Создание экземпляра Post и Group."""
        super().setUpClass()
        cls.user_1 = User.objects.create_user(username='Neo')
        cls.user_2 = User.objects.create_user(username='Rick')
        cls.user = User.objects.create_user(username='auth')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 2',
            slug='slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Тестовый пост',
            group=cls.group_1,
        )
        cls.follow = Follow.objects.create(user=cls.user, author=cls.user_1)
        cls.follow_1 = Follow.objects.create(user=cls.user_2, author=cls.user)

    @classmethod
    def tearDownClass(cls):
        """Прибирает за собой."""
        super().tearDownClass()
        cls.user.delete()
        cls.user_1.delete()
        cls.user_2.delete()
        cls.group.delete()
        cls.group_1.delete()
        cls.post.delete()
        cls.post_1.delete()
        cls.follow.delete()
        cls.follow_1.delete()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание экземпляра клиента."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_views_uses_correct_template(self):
        """Проверка использования View шаблонов."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'auth'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'id': f'{self.post.id}'}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_edit', kwargs={'id': f'{self.post.id}'}): (
                'posts/create_post.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_main_detail_page_show_correct_context(self):
        """
        Проверка контекста шаблона главной страницы и отдельного поста.
        """
        pages = {
            (reverse('posts:index')): 'page_obj',
            (reverse('posts:post_detail',
                     kwargs={'id': f'{self.post.id}'})): 'post'
        }
        for address, tip in pages.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                object = response.context.get(tip)

                # Выбираем нужный пост из post_obj главной страницы,
                # для исключения конфликта имен
                if tip != 'post':
                    object_1 = object[0]
                    object_2 = object[1]
                    if object_1.author != self.user:
                        object = object_2
                    else:
                        object = object_1

                self.assertEqual(object.author, self.user)
                self.assertEqual(object.text, 'Тестовый пост')
                self.assertEqual(object.pub_date, self.post.pub_date)
                self.assertEqual(object.group.title, 'Тестовая группа')
                self.assertEqual(object.image, 'posts/small.gif')
                self.assertEqual(
                    object.group.description, 'Тестовое описание'
                )

    def test_group_profile_page_show_correct_context(self):
        """Проверка контекста шаблона страницы группы и профиля."""
        pages = (
            reverse('posts:group_list', kwargs={'slug': 'slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        for address in pages:
            response = self.authorized_client.get(address)
            object = response.context['page_obj'][0]
            self.assertNotRegex(object.author.username, 'Neo')
            self.assertEqual(object.text, 'Тестовый пост')
            self.assertEqual(object.pub_date, self.post.pub_date)
            self.assertNotRegex(object.group.title, 'Тестовая группа 2')
            self.assertEqual(object.image, 'posts/small.gif')
            self.assertEqual(
                object.group.description, 'Тестовое описание'
            )

    def test_creat_pages_show_correct_context(self):
        """
        Проверка контекста шаблона страниц создания и редактирования постов.
        """
        PAGES = (
            reverse('posts:post_edit', kwargs={'id': f'{self.post.id}'}),
            reverse('posts:post_edit', kwargs={'id': f'{self.post_1.id}'}),
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }

        for address in PAGES:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

            if address == reverse(
                'posts:post_edit', kwargs={'id': f'{self.post_1.id}'}
            ):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
            else:
                response = self.authorized_client.get(address)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_follow_page_show_correct_context(self):
        """Проверка контекста шаблона страницы подписок."""
        page = reverse('posts:follow_index')

        # Создает тестовый пост
        post_2 = Post.objects.create(
            author=self.user_1,
            text='Тест для подписок',
            group=self.group_1,
        )

        # Проверяет, что подписчик видит новый пост автора
        response = self.authorized_client.get(page)
        object = response.context['page_obj'][0]
        self.assertEqual(object.author.username, post_2.author.username)
        self.assertEqual(object.text, post_2.text)
        self.assertEqual(object.pub_date, post_2.pub_date)
        self.assertEqual(object.group.title, post_2.group.title)

        # Авторизовывает пользователя, который не подписан на автора
        self.authorized_client.force_login(self.user_2)

        # Проверяет, что пользователь не видит новый пост автора
        response = self.authorized_client.get(page)
        object = response.context['page_obj'][0]
        self.assertNotEqual(object.author.username, post_2.author.username)
        self.assertNotEqual(object.text, post_2.text)
        self.assertNotEqual(object.pub_date, post_2.pub_date)
        self.assertNotEqual(object.group.title, post_2.group.title)

    def test_caches(self):
        """
        Проверка кэширования главной страницы.
        """
        post_3 = Post.objects.create(
            author=self.user_1,
            text='FROM-RUSSIA-WITH-LOVE',
        )

        # Создаёт информацию в кэше
        response = self.authorized_client.get(reverse('posts:index'))

        # Удаляет Пост №3 и проверяет, что в кэше данные Поста №3 сохранены
        post_3.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertRegex(str(response.content), post_3.text)

        # Чистит кэш и проверяет, что данные Поста №3 отсутствуют в кэше
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotRegex(str(response.content), post_3.text)


class PaginatorViewsTest(TestCase):
    """Тестирует Паджинатор View приложения."""

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
        for i in range(14):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )
        cls.PAGES = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        cls.FIRST_PAGE = 10
        cls.SECOND_PAGE = 4

    def setUp(self):
        """Создание экземпляра клиента."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        """Прибирает за собой."""
        super().tearDownClass()
        cls.user.delete()
        cls.group.delete()
        cls.post.delete()

    def test_paginator(self):
        """Проверка контекста шаблона страниц."""
        for address in self.PAGES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), self.FIRST_PAGE
                )
                response = self.authorized_client.get(address + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), self.SECOND_PAGE
                )
