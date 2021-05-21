import datetime as dt

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, PostForm, Group, User, CommentForm, Comment, Follow


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 3)  # показывать по 3 записей на странице.

    page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number)  # получить записи с нужным смещением
    comment = Comment.objects.all()  # Все комментарии (для счетчика)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator, 'comment': comment}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date')[:11]
    return render(request, "group.html", {"group": group, "posts": posts})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.pub_date = dt.datetime.now()
            post.save()
            return redirect('index')
        return render(request, 'new.html', {'form': form, 'top': 'Добавление новой записи',
                                            'title': 'Создать',
                                            'button': 'Опубликовать'})
    form = PostForm()
    return render(request, 'new.html', {'form': form, 'top': 'Добавление новой записи',
                                        'title': 'Создать',
                                        'button': 'Опубликовать'})


def profile(request, username):
    author_id = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author_id).order_by('-pub_date').all()
    paginator = Paginator(posts, 3)
    count_posts = paginator.count
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    comment = Comment.objects.filter(author=author_id)
    following = User.objects.get(id=request.user.id).follower.filter(author=author_id)
    following_count = User.objects.get(id=author_id.id)
    return render(request, 'profile.html',
                  {'count_posts': count_posts,
                   'page': page,
                   'paginator': paginator,
                   'author_id': author_id,
                   'comment': comment,
                   'following': following,
                   'following_count': following_count})


def post_view(request, username, post_id):
    author_id = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, id=post_id)
    count = len(Post.objects.filter(author=author_id).all())
    form = CommentForm()
    items = post.comments.all()
    return render(request, 'post.html', {'post': post,
                                         'author_id': author_id,
                                         'count': count,
                                         'form': form,
                                         'items': items})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != author:
        return redirect(f'/{username}/{post_id}/')
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect(f'/{username}/{post_id}/')

    return render(request, 'new.html',
                  {'form': form,
                   'post': post,
                   'title': 'Редактировать',
                   'button': 'Сохранить',
                   'top': 'Редактирование записи'
                   })


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.created = dt.datetime.now()
            comment.post = post
            comment.save()
            return redirect(f'/{username}/{post_id}/')
        render(request, 'post.html', {'form': form, 'post': post})


@login_required
def follow_index(request):
    users = User.objects.get(id=request.user.id).follower.all().values_list('author')
    posts = Post.objects.filter(author__in=users)
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page,
                                           'paginator': paginator})


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        user = get_object_or_404(User, username=username)
        Follow.objects.get_or_create(author=user, user=request.user)
        return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    if request.user.username != username:
        user = get_object_or_404(User, username=username)
        follower = Follow.objects.get(author=user, user=request.user)
        follower.delete()
        return redirect('profile', username=username)
