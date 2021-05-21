from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ModelForm

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, related_name="posts",
                              blank=True, null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


#  Дальше модель комментариев

class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name="comments")  # Ссылка на пост, к которому добавлен комментарий
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(max_length=1000)
    created = models.DateTimeField("date commented", auto_now_add=True)

    def __str__(self):
        return self.text


class CommentForm(ModelForm):
    text = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=200)

    class Meta:
        model = Comment
        fields = ['text']


#  Дальше модель подписки

class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower")  # Пользователь, который подписывается
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following")  # Пользователь, на которого подписываются


class FollowForm(ModelForm):
    user = forms.CharField()
    author = forms.CharField()

    class Meta:
        model = Follow
        fields = ['user', 'author']
