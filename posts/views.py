from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.decorators.cache import cache_page

def page_not_found(request, exception):
        # Переменная exception содержит отладочную информацию, 
        # выводить её в шаблон пользователской страницы 404 мы не станем
        return render(request, "misc/404.html", {"path": request.path}, status=404)

def server_error(request):
        return render(request, "misc/500.html", status=500)

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    #group_list = Post.objects.prefetch_related('author').get(pk=group.id)
    group_list = Post.objects.filter(group=group).order_by("-pub_date").all()
    paginator = Paginator(group_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'page': page, 'paginator': paginator, "group": group})

#@cache_page(60 * 15)
def index(request):
    post_list = Post.objects.select_related('author', 'group').order_by('-pub_date').all()
    #post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10) # показывать по 10 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, 'index.html', {'page': page, 'paginator': paginator, 'post': post_list})

@login_required
def new_post(request):
    author = User.objects.get(username=request.user)
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    return render(request, 'new.html', {'form': form, 'author': author})

def profile(request, username):
    profile = get_object_or_404(User, username=username)
    #post_list = Post.objects.select_related('author', 'group').order_by('-pub_date').get(pk=profile.id)
    post_list = Post.objects.filter(author=profile).order_by("-pub_date")
    paginator = Paginator(post_list, 5) # показывать по 5 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    post_count = Post.objects.filter(author=profile).count()
    if request.user.is_authenticated:
        follow_stat = Follow.objects.filter(user=request.user).filter(author=profile)
        if not follow_stat:
            following = False
        else:
            following = True
        return render(request, 'profile.html', {'page': page,'paginator': paginator,
        'profile': profile,'post_count': post_count,'following': following})
    return render(request, 'profile.html', {'page': page,'paginator': paginator,
    'profile': profile,'post_count': post_count,})

def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    profile = get_object_or_404(User, username=username)
    
    items = Comment.objects.filter(post=post_id)
    if post.author != profile:
        return redirect('profile', username)
    post_count = Post.objects.filter(author=profile).count()
    form = CommentForm()
    if request.user.is_authenticated:
        follow_stat = Follow.objects.filter(user=request.user).filter(author=profile)
        if not follow_stat:
            following = False
        else:
            following = True
        return render(request, 'post.html', {'post': post,'form': form,'profile': profile,
        'post_count': post_count,'items': items,'following': following})
    return render(request, 'post.html', {'post': post,'form': form,'profile': profile,
    'post_count': post_count,'items': items,})

@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect('post', username=request.user.username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('post', username=request.user.username, post_id=post_id)
    return render(request, 'new.html', {'form': form, 'post': post, 'profile': profile})

@login_required
def add_comment(request, username, post_id): #username это post.author.username - автор поста
    profile = get_object_or_404(User, username=username) # текущий, авторизованный юзер - автор комментария
    user = get_object_or_404(User, username=request.user)
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = user
            comment.save()
            return redirect('post', username, post_id)
    return render(request, 'post.html', {'username': username,'profile': profile,'post_id': post_id,'post': post})

@login_required
def follow_index(request):
    following_list = [] 
    user = get_object_or_404(User, username=request.user)
    follows = Follow.objects.filter(user=user).values('author')
    following_list = Post.objects.filter(author_id__in=follows).order_by("-pub_date")
    paginator = Paginator(following_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page,'paginator': paginator,'post': following_list,'username': user.username})

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow_stat = Follow.objects.filter(user=request.user).filter(author=author)
    if request.user != author:
        if not follow_stat:
            Follow.objects.create(user=request.user, author=author)
            return redirect('profile', username)
    return redirect('profile', username)

@login_required
def profile_unfollow(request, username):# имя пользователя профайла(на которого подписка)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user).filter(author=author).delete()
    return redirect('profile', username)


    ''' # Альтернативный способ подсчёта подписчиков
    follower_count = Follow.objects.filter(author=profile).count()
    if request.user == profile:
        following_count = Follow.objects.filter(author=request.user).count()
    else:
        following_count = Follow.objects.filter(user=profile).count()
    '''
 