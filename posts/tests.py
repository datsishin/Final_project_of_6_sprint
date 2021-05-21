from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User, Follow


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="sarah",
                                             email="connor.s@skynet.com",
                                             password="12345")
        self.user.save()
        self.client.login(username="sarah", password="12345")

        self.post = Post.objects.create(
            text="You're talking about things "
                 "I haven't done yet in the past tense. I"
                 "t's driving me crazy!",
            author=self.user)

    def test_profile(self):
        response = self.client.get("/sarah/")
        self.assertEqual(response.status_code, 200)  # Проверка кода ответа сервера (200 - страница существует)
        self.assertEqual(Post.objects.filter(author__username='sarah').count(), 1)  # Проверка кол-ва постов автора с username = 'sarah'
        self.assertEqual(response.context['author_id'].username, self.user.username)  # Проверка отображения username на странице профиля
        self.assertEqual(response.context['page'][0].text, self.post.text)  # Проверка соотвествия текста поста на странице профиля

    def test_new_post_un_auth(self):
        self.client.logout()  # Разлогинивание пользователя
        response = self.client.get("/new", follow=True)  # Ответ на запрос страницы добавления нового поста
        self.assertRedirects(response, expected_url='/auth/login/?next=/new/', status_code=301)  # Проверка 301 редиректа на главную страницу

    def test_new_post(self):  # Проверка соотвествия текста поста на разных страницах
        response = self.client.get("/")
        self.assertEqual(response.context['page'][0].text, self.post.text)  # Сравнение текста первого элемента страницы
        response = self.client.get(f'/{self.user.username}/')  # Запрос страницы профиля
        self.assertEqual(response.context['page'][0].text, self.post.text)  # Сравнение текста первого элемента страницы
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')  # Запрос страницы поста
        self.assertEqual(response.context['post'].text, self.post.text)  # Сравнение текста

    def test_post_edit(self):  # Проверка текста поста после редактирования на разных страницах
        response = self.client.get(f'/{self.user.username}/{self.post.id}/edit/')  # Запрос страницы редактирования поста
        self.assertEqual(response.status_code, 200)
        self.client.post(f'/{self.user.username}/{self.post.id}/edit/', {'text': 'Отредактирован'})  # Запрос изменения текста поста по ссылке на него
        response = self.client.get(f'/{self.user.username}/{self.post.id}/')  # Запрос страницы поста
        self.assertEqual(response.context['post'].text, 'Отредактирован')  # Проверка изменения текста поста

        response = self.client.get(f'/{self.user.username}/')  # Запрос страницы профиля
        self.assertEqual(response.context['page'][0].text, 'Отредактирован')  # Проверка изменения текста поста в профиле

        response = self.client.get('/')  # Запрос главной страницы
        self.assertEqual(response.context['page'][0].text, 'Отредактирован')  # Проверка изменения текста поста на гланой

    def test_image_on_post_page(self):
        with open('media/posts/1.jpg', 'rb') as img:
            self.client.post(f'/{self.user.username}/{self.post.id}/edit/',
                             {'author': self.user, 'text': 'post with image', 'image': img})
            response = self.client.get(f'/{self.user.username}/{self.post.id}/')
            self.assertContains(response, '<img')

            response = self.client.get(f'/{self.user.username}/')
            self.assertContains(response, '<img')

            cache.clear()
            response = self.client.get('')
            self.assertContains(response, 'post with image')

            post_value = Post.objects.count()
            self.assertEqual(post_value, 1)

    def test_another_file(self):
        with open('media/posts/tesla.py', 'rb') as img:
            post = self.client.post(f'/{self.user.username}/{self.post.id}/edit/', {'author': self.user, 'text': 'post with image', 'image': img})
            post_value = Post.objects.count()
            self.assertEqual(post_value, 1)

    def test_cache(self):
        self.client.post(f'/new/', {'author': self.user, 'text': 'first text'})
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'first text')
        self.client.post(f'/new/', {'author': self.user, 'text': 'second text'})
        self.assertNotContains(response, 'second text')
        cache.clear()
        response = self.client.get('')
        self.assertContains(response, 'first text')
        self.assertContains(response, 'second text')


class TestFollow(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_third = Client()
        self.user_follower = User.objects.create_user(username='follower', email='follower@mail.ru', password='12345678')
        self.user_following = User.objects.create_user(username='following', email='following@mail.ru', password='12345678')
        self.user_third = User.objects.create_user(username='third', email='third@mail.ru', password='12345678')
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.client_auth_third.force_login(self.user_third)

    def test_follow_and_unfollow(self):
        before = Follow.objects.all().count()
        self.client_auth_follower.get(reverse('profile_follow', kwargs={'username': self.user_following.username}))
        after = Follow.objects.all().count()
        self.assertEqual(before + 1, after)
        self.client_auth_follower.get(reverse('profile_unfollow', kwargs={'username': self.user_following.username}))
        old = Follow.objects.all().count()
        self.assertEqual(old, before)

    def test_new_post_follower(self):
        self.client_auth_follower.get(reverse('profile_follow', kwargs={'username': self.user_following.username}))
        self.user_following.post = Post.objects.create(
            text="My first post",
            author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        self.assertContains(response, 'My first post')
        response = self.client_auth_third.get('/follow/')
        self.assertNotContains(response, 'My first post')

    def test_comment(self):
        self.user_following.post = Post.objects.create(
            text="My first post",
            author=self.user_following)
        response = self.client_auth_follower.get('/')
        self.assertContains(response, 'Добавить комментарий')
        response = self.client.get('/')
        self.assertNotContains(response, 'Добавить комментарий')