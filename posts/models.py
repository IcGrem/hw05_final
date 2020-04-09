from django.db import models
from django.contrib.auth import get_user_model

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
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_author")
    group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.CASCADE, related_name="group")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return str(self.id)
    def __str__(self):
        return self.text

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comment")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_author")
    text = models.TextField(blank=False, null=False)
    created = models.DateTimeField("comment_date_pub", auto_now_add=True)
    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower") #ссылка на объект пользователя, который подписывается ПОДПИЩИК
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following") #ссылка на объект пользователя, на которого подписываются
    def __str__(self):
        return f'follower - {self.user} | following - {self.author}'
