from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from .models import Post, Group, Comment, Follow
from django.core.files.images import ImageFile
import time

User = get_user_model()

class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = User.objects.create_user(username="lermontov")
        self.text="Скажи-ка дядя, ведь не даром..."
        self.text_edit="Скажи-ка дядя, ведь не даром, Москва, спалённая пожаром COVIDу отдана..."


    def test_profile(self):
        self.client.force_login(self.username)
        response = self.client.get(f'/{self.username}/')
        self.assertEqual(response.status_code, 200)


    def test_new_post(self):
        self.client.force_login(self.username)
        response = self.client.post("/new/", {"text": self.text})
        self.assertRedirects(response, "/")


    def test_not_auth_redirect(self):
        response = self.client.post("/new/", {"text": self.text}, follow=True)
        self.assertRedirects(response, "/auth/login/?next=/new/", status_code=302,
                             target_status_code=200, msg_prefix='', fetch_redirect_response=True)


    @override_settings(CACHES=settings.TEST_CACHES)
    def test_new_post_exist(self):
        self.client.force_login(self.username)
        self.client.post("/new/", {"text": self.text})
        post = Post.objects.get(author=self.username, text=self.text)
        response = self.client.get("/")
        self.assertContains(response, self.text)
        response = self.client.get(f'/{self.username}/')
        self.assertContains(response, self.text)
        response = self.client.get(f'/{self.username}/{post.id}/')
        self.assertContains(response, self.text)


    @override_settings(CACHES=settings.TEST_CACHES)
    def test_auth_edit_post(self):
        self.client.force_login(self.username)
        self.client.post("/new/", {"text": self.text})
        post = Post.objects.get(author=self.username, text=self.text)
        self.client.post(f'/{self.username}/{post.id}/edit/', {"text": self.text_edit})
        response = self.client.get("/")
        self.assertContains(response, self.text_edit)
        response = self.client.get(f'/{self.username}/')
        self.assertContains(response, self.text_edit)
        response = self.client.get(f'/{self.username}/{post.id}/')
        self.assertContains(response, self.text_edit)


class CommFollTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = User.objects.create_user(username="lermontov")
        self.author = User.objects.create_user(username="leo")
        self.username1 = User.objects.create_user(username="pushkin")
        self.text="ТЕСТОВЫЙ ПОСТ"


    def test_404(self):
        response = self.client.get('/test09465/')
        self.assertEqual(response.status_code, 404)


    def test_cache(self):
        self.client.force_login(self.username)
        response_before_cache = self.client.get('/')
        self.client.post('/new/', {'text': self.text})
        response_after_cache = self.client.get('/')
        self.assertEqual(response_before_cache.content, response_after_cache.content)


    def test_img_tag(self):
        self.client.force_login(self.username)
        img = SimpleUploadedFile(name='1.png', content=open('file_for_test/1.png', 'rb').read(),
                                 content_type='image/png')
        self.client.post('/new/', {"text": self.text, 'image': img})
        post = Post.objects.get(text=self.text)
        response = self.client.get(f'/{self.username}/{post.id}/')
        self.assertContains(response, 'img')


    @override_settings(CACHES=settings.TEST_CACHES)
    def test_img_profile(self):
        self.client.force_login(self.username)
        group = Group.objects.create(title="img_group", slug="img_group")
        img = SimpleUploadedFile(name='1.png', content=open('file_for_test/1.png', 'rb').read(),
                                 content_type='image/png')
        self.client.post('/new/', {'group': group.id, 'text': self.text, 'image': img})
        group_s = Post.objects.get(text=self.text).group
        response = self.client.get("/")
        self.assertContains(response, 'img')
        response = self.client.get(f'/{self.username}/')
        self.assertContains(response, 'img')
        response = self.client.get(f'/group/{group_s.slug}/')
        self.assertContains(response, 'img')


    def test_img_non_img(self):
        self.client.force_login(self.username)
        not_img = SimpleUploadedFile(name='1.txt', content=open('file_for_test/1.txt', 'rb').read(),
                                     content_type='txt')
        self.client.post('/new/', {'text': self.text, 'image': not_img})
        post = Post.objects.filter(author=self.username, text=self.text).first()
        self.assertIsNone(post)


    def test_new_user_follow(self):
        self.client.force_login(self.username)
        self.client.post(f'/{self.author}/follow/')
        cnt = self.author.following.count()
        self.assertIsNotNone(cnt)


    def test_new_user_unfollow(self):
        self.client.force_login(self.username)
        self.client.post(f'/{self.author}/unfollow/')
        cnt = self.author.following.count()
        self.assertEqual(cnt, 0)


    @override_settings(CACHES=settings.TEST_CACHES)
    def test_new_user_lenta(self):
        self.client.force_login(self.author)# автор авторизовался
        self.client.post("/new/", {"text": self.text})#опубликовал пост
        self.client.logout()# автор вышел
        self.client.force_login(self.username)# юзер авторизовался
        self.client.post(f'/{self.author}/follow/') #юзер подписался на автора
        response = self.client.get("/follow/")
        self.assertContains(response, self.text)
        self.client.logout()# юзер вышел
        self.client.force_login(self.username1)# юзер1 авторизовался
        response = self.client.get("/follow/")
        self.assertNotContains(response, self.text)


    def test_auth_user_comment(self):
        comment_text = 'Комментарий'
        self.client.force_login(self.username)
        self.client.post("/new/", {"text": self.text})
        post = Post.objects.get(author=self.username, text=self.text)
        self.client.post(f'/{self.username}/{post.id}/comment/', {'post': post, 'author': self.username, 'text': comment_text})
        response = self.client.get(f'/{self.username}/{post.id}/')
        self.assertContains(response, comment_text)
