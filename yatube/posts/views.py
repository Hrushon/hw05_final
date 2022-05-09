from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .paginator import paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница."""
    posts = Post.objects.select_related('author', 'group').all()
    page_obj = paginator(posts, request)
    text = 'Последние обновления на сайте'
    template = 'posts/index.html'
    context = {'page_obj': page_obj,
               'text': text}
    return render(request, template, context)


def group_posts(request, slug):
    """Страница со списком групп."""
    text = 'Записи сообщества'
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = group.posts.select_related('group').all()
    page_obj = paginator(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
        'text': text
    }
    return render(request, template, context)


def profile(request, username):
    """Страница профиля."""
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    posts = author.posts.select_related('group').all()
    count_article = posts.count()
    page_obj = paginator(posts, request)
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user))
    context = {
        'author': author,
        'count': count_article,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, id):
    """Отдельные записи пользователя."""
    post = Post.objects.get(id=id)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    cnt = author.posts.count()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'count': cnt,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Создание новой записи."""
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None, files=request.FILES or None
    )

    if not form.is_valid():
        return render(request, template, {'form': form})

    form = form.save(commit=False)
    form.author = request.user
    form.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, id):
    """Редактирование записи."""
    post = get_object_or_404(Post, id=id)
    template = 'posts/create_post.html'
    is_edit = 'is_edit'
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if request.user != post.author:
        return redirect('posts:post_detail', id=post.id)

    context = {
        'is_edit': is_edit,
        'form': form,
    }

    if not form.is_valid():
        return render(request, template, context)
    form.save()
    return redirect('posts:post_detail', id=post.id)


@login_required
def add_comment(request, id):
    post = get_object_or_404(Post, id=id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', id=post.id)


@login_required
def follow_index(request):
    text = 'Посты любимых авторов'
    authors = request.user.follower.values_list('author')
    if not authors:
        text = (
            'У Вас еще нет любимых авторов.<br>'
            'Подпишитесь на кого-нибудь!'
        )
    posts = Post.objects.filter(
        author__in=authors
    ).select_related('group').all()
    page_obj = paginator(posts, request)
    template = 'posts/follow.html'
    context = {'page_obj': page_obj,
               'text': text}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        follow = Follow.objects.get_or_create(
            user=request.user, author=author
        )[0]
        follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    request.user.follower.all().filter(author=author).delete()
    return redirect('posts:profile', username=username)
