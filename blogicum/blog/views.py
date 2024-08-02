from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.utils import timezone
from django.urls import reverse_lazy
from django.conf import settings
from .models import Category, Post, Comment, User
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from .forms import (
    PostForm, UserProfileForm, CommentForm
)
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ('title', 'text', 'image', 'location',
              'category', 'pub_date')
    template_name = 'blog/create.html'
    login_url = settings.LOGIN_URL
    redirect_field_name = 'redirect_to'

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.object.author.username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditPostView(UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.pk})


class DeletePostView(DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        if post.author != self.request.user and not self.request.user.is_staff:
            raise Http404("У вас нет прав на удаление этого поста")
        return post

    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return self.handle_no_permission()
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        return self.render_to_response(
            {'error': 'Публикация не найдена или нет прав на её удаление'},
            status=404)

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


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


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if (not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()) and post.author != request.user:
        raise Http404("Post not found")
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
    if not category.is_published:
        raise Http404("Post not found")
    post_list = get_published_posts().filter(category=category)
    paginator = Paginator(post_list, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request,
                  "blog/category.html",
                  {"category": category, "page_obj": page_obj})


class EditCommentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['text']
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        comment = self.get_object()
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': comment.post.pk})

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id)

    def test_func(self):
        comment = self.get_object()
        return (
            self.request.user.is_authenticated
            and self.request.user == comment.author
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context


class DeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id)

    def test_func(self):
        comment = self.get_object()
        return (
            self.request.user.is_authenticated
            and self.request.user == comment.author
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.get_object()
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            post = self.get_object()
        except Post.DoesNotExist:
            raise Http404("Пост не найден")
        if post.author != request.user and not request.user.is_staff:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    post_obj = None

    def dispatch(self, request, *args, **kwargs):
        try:
            self.post_obj = Post.objects.get(pk=self.kwargs.get('post_id'))
        except Post.DoesNotExist:
            return render(request, 'pages/404.html', status=404)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.post = self.post_obj
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.post_obj.pk})
