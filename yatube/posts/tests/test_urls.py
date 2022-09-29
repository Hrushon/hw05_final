from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    """Тестирует URL приложения."""

    @classmethod
    def setUpClass(cls):
        """Создание экземпляра Post и Group."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_1 = User.objects.create_user(username='Rick')
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
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            text='Другой пост',
            group=cls.group,
        )
        cls.MAIN_PAGE = reverse('posts:index')
        cls.POST_PAGE_CREATE = reverse('posts:post_create')
        cls.GROUP_PAGE = reverse(
            'posts:group_list', kwargs={'slug': 'slug'}
        )
        cls.PROFILE_PAGE = reverse(
            'posts:profile', kwargs={'username': 'auth'}
        )
        cls.POST_PAGE = reverse(
            'posts:post_detail', kwargs={'id': f'{PostURLTests.post.id}'}
        )
        cls.POST_PAGE_EDIT = reverse(
            'posts:post_edit', kwargs={'id': f'{PostURLTests.post.id}'}
        )
        cls.POST_PAGE_COMMENT = reverse(
            'posts:add_comment', kwargs={'id': f'{PostURLTests.post.id}'}
        )
        cls.POST_PAGE_EDIT_NOT = reverse(
            'posts:post_edit', kwargs={'id': f'{PostURLTests.post_1.id}'}
        )
        cls.ON_FOLLOW_PAGE = reverse(
            'posts:profile_follow', kwargs={'username': 'Rick'}
        )
        cls.UNFOLLOW_PAGE = reverse(
            'posts:profile_unfollow', kwargs={'username': 'Rick'}
        )
        cls.FOLLOW_INDEX_PAGE = reverse('posts:follow_index')
        cls.UNEXISTING_PAGE = '/unexisting_page/'
        cls.REDIRECT_PAGE_1 = f'/auth/login/?next={cls.POST_PAGE_EDIT}'
        cls.REDIRECT_PAGE_2 = f'/auth/login/?next={cls.POST_PAGE_CREATE}'
        cls.REDIRECT_PAGE_3 = f'/auth/login/?next={cls.FOLLOW_INDEX_PAGE}'
        cls.REDIRECT_PAGE_4 = f'/auth/login/?next={cls.POST_PAGE_COMMENT}'
        cls.REDIRECT_PAGE_5 = f'/auth/login/?next={cls.ON_FOLLOW_PAGE}'
        cls.REDIRECT_PAGE_6 = f'/auth/login/?next={cls.UNFOLLOW_PAGE}'
        cls.REDIRECT_PAGE_7 = reverse(
            'posts:post_detail', kwargs={'id': f'{PostURLTests.post_1.id}'}
        )

    @classmethod
    def tearDownClass(cls):
        """Прибирает за собой."""
        super().tearDownClass()
        cls.user.delete()
        cls.user_1.delete()
        cls.group.delete()
        cls.post.delete()
        cls.post_1.delete()

    def setUp(self):
        """Создание экземпляра клиента."""
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages(self):
        """Проверка доступа пользователей к страницам"""
        clients = (self.guest_client, self.authorized_client)
        PAGES_LIST = (
            self.MAIN_PAGE, self.GROUP_PAGE,
            self.PROFILE_PAGE, self.POST_PAGE,
            self.POST_PAGE_EDIT, self.POST_PAGE_CREATE,
            self.FOLLOW_INDEX_PAGE, self.POST_PAGE_COMMENT,
            self.ON_FOLLOW_PAGE, self.UNFOLLOW_PAGE,
            self.UNEXISTING_PAGE, self.POST_PAGE_EDIT_NOT,
            self.REDIRECT_PAGE_1, self.REDIRECT_PAGE_2,
            self.REDIRECT_PAGE_3, self.REDIRECT_PAGE_4,
            self.REDIRECT_PAGE_5, self.REDIRECT_PAGE_6,
            self.REDIRECT_PAGE_7,
        )

        # Проверяет свободный доступ пользователей
        for man in clients:
            if man != self.guest_client:
                pages = PAGES_LIST[0:7]
            else:
                pages = PAGES_LIST[0:4]
            for page in pages:
                with self.subTest(page=page):
                    response = man.get(page)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяет доступ пользователя к несуществующей странице
            response = man.get(PAGES_LIST[10])
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # Проверяет, что неавтор не отредактирует пост
        response = self.authorized_client.get(PAGES_LIST[11])
        self.assertRedirects(response, PAGES_LIST[18])

        # Проверяет редирект неавторизованного пользователя
        for i in (4, 5, 6, 7, 8, 9):
            page = PAGES_LIST[i]
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertRedirects(response, PAGES_LIST[i + 8])

        # Проверяет редирект авторизованного пользователя
        for i in (7, 8, 9):
            page = PAGES_LIST[i]
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """Проверка использования URL-адресами шаблонов."""
        templates_url_names = {
            self.MAIN_PAGE: 'posts/index.html',
            self.GROUP_PAGE: 'posts/group_list.html',
            self.PROFILE_PAGE: 'posts/profile.html',
            self.POST_PAGE: 'posts/post_detail.html',
            self.POST_PAGE_EDIT: 'posts/create_post.html',
            self.POST_PAGE_CREATE: 'posts/create_post.html',
            self.UNEXISTING_PAGE: 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
