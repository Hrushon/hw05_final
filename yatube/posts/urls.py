from django.urls import path

from . import views

app_name: str = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    # Страница группы
    path('group/<slug:slug>/', views.group_posts, name='group_list'),
    # Профайл пользователя
    path('profile/<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('posts/<int:id>/', views.post_detail, name='post_detail'),
    # Создание новой записи
    path('create/', views.post_create, name='post_create'),
    # Редактирование записи
    path('posts/<int:id>/edit/', views.post_edit, name='post_edit'),
    # Добавление комментария
    path('posts/<int:id>/comment/', views.add_comment, name='add_comment'),
    # Просмотр постов любимых авторов
    path('follow/', views.follow_index, name='follow_index'),
    # Подписка на автора
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    # Отписка от автора
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
