from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    """Создает пост."""

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )

    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Загрузите картинку',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        """Возвращает текст поста."""
        return self.text[:15]

    class Meta:
        """
        Сортирует посты по дате и добавляет русские название в админке.
        """
        ordering = ('-pub_date', )
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Group(models.Model):
    """Создает группу."""

    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Введите название группы'
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы'
    )

    def __str__(self):
        """Возвращает имя группы."""
        return self.title

    class Meta:
        """Добавляет русские названия в админке."""
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания комментария'
    )

    def __str__(self):
        """Возвращает текст комментария."""
        return self.text[:15]

    class Meta:
        """
        Сортирует комментарии по дате и добавляет русские названия в админке.
        """
        ordering = ('-created', )
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ManyToManyField(
        User,
        related_name='following',
        verbose_name='Подписываемый'
    )

    class Meta:
        """
        Добавляет русские названия в админке.
        """
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
