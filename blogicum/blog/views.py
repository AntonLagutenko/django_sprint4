from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.conf import settings
from .models import Category, Post, Comment, User
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import (
    PostForm, UserProfileForm, EditCommentForm, DeleteCommentForm, CommentForm
)
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.db.models import Count
from django.http import Http404


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание поста."""

    model = Post
    fields = ('title', 'text', 'image', 'location',
              'category', 'pub_date')
    template_name = 'blog/create.html'
    # URL для перенаправления при неавторизованном доступе
    login_url = settings.LOGIN_URL
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.author = self.request.user
            return super().form_valid(form)
        else:
            return HttpResponseRedirect(settings.LOGIN_URL)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.object.author.username})


class EditPostView(UpdateView):
    """Изменение поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        # Проверяем, авторизован ли пользователь
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        # Получаем объект поста
        post = self.get_object()
        # Проверяем, является ли текущий пользователь автором поста
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.pk})


class DeletePostView(DeleteView):
    """Удаление поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            post = self.get_object()
        except Post.DoesNotExist:
            raise Http404("Публикация не найдена.")
        if post.author != request.user and not request.user.is_staff:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.object.author.username})


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def test_func(self):
        return self.request.user.username == self.kwargs.get('username')

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context


class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(self.model, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts_list = Post.objects.filter(
            author=self.object
        ).annotate(
            comment_count=Count('post_comments')
        ).order_by('-pub_date')

        paginator = Paginator(posts_list, settings.AMOUNT_POSTS)
        page = self.request.GET.get('page')
        context['page_obj'] = paginator.get_page(page)
        return context


def get_published_posts():
    return Post.objects.select_related(
        "author", "category", "location"
    ).filter(
        is_published=True, pub_date__lt=now(), category__is_published=True
    )


def index(request):
    post_db = get_published_posts()[:settings.AMOUNT_POSTS]
    for post in post_db:
        post.comment_count = post.comments_count()
    return render(request, "blog/index.html", {"page_obj": post_db})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not post.is_published and post.author != request.user and not request.user.is_staff:
        return redirect('pages:custom_404')

    comments = post.post_comments.all().order_by('created_at')
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            comment = Comment(author=request.user, post=post, text=text)
            comment.save()
            return redirect('post_detail', post_id=post_id)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = get_published_posts().filter(category=category)
    # Показывать по 10 публикаций на странице
    paginator = Paginator(post_list, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request,
                  "blog/category.html",
                  {"category": category, "page_obj": page_obj})


class EditCommentView(UpdateView):
    model = Comment
    form_class = EditCommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.post_id})


class DeleteCommentView(DeleteView):
    model = Comment
    form_class = DeleteCommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.post_id})


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'includes:comments.html'
    post = None

    def dispatch(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        self.post = get_object_or_404(Post, pk=post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.post.pk})

    def form_valid(self, form):
        form.instance.post = self.post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def http_method_not_allowed(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['GET'])  # Define the allowed HTTP methods

    def post(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)
