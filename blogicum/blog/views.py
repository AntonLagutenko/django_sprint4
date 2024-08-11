from constants.constants import AMOUNT_POSTS
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from .forms import (
    CommentForm, PostForm, UserProfileForm
)
from .models import Category, Comment, Post, User


class AuthorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile',
                       args=(self.object.author.username,))

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditPostView(AuthorRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', args=(self.object.pk,))


class DeletePostView(LoginRequiredMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            obj = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        except Http404:
            raise Http404("Публикация не найдена")
        if obj.author != self.request.user:
            return HttpResponseRedirect(reverse('blog:post_detail',
                                                kwargs={'post_id': obj.pk}))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def test_func(self):
        return self.request.user.username == self.kwargs.get('username')

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context


class PostListMixin:
    paginate_by = AMOUNT_POSTS

    def get_queryset(self):
        return Post.objects.annotate(
            comment_count=Count('post_comments')).order_by('-pub_date')


class UserProfileView(PostListMixin, ListView):
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        username = self.kwargs.get('username')
        author = get_object_or_404(User, username=username)
        if self.request.user == author:
            return super().get_queryset().filter(author=author)
        else:
            return super().get_queryset().filter(author=author,
                                                 is_published=True,
                                                 pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        context['profile'] = get_object_or_404(User, username=username)
        return context


def get_published_posts():
    return Post.objects.select_related(
        "author", "category", "location"
    ).filter(
        is_published=True, pub_date__lt=now(), category__is_published=True
    )


def index(request):
    post_db = get_published_posts().annotate(
        comments_count=Count('post_comments')
    ).order_by('-pub_date')
    paginator = Paginator(post_db, AMOUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    for post in page_obj:
        post.title = f"{post.title} ({post.comments_count})"
    return render(request, "blog/index.html", {"page_obj": page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if (not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()) and post.author != request.user:
        raise Http404("Post not found")
    comments = post.post_comments.all().order_by('created_at')
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
    post_list = get_published_posts().filter(category=category).annotate(
        comments_count=Count('post_comments')
    ).order_by('-pub_date')
    paginator = Paginator(post_list, AMOUNT_POSTS)
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
        return reverse('blog:post_detail',
                       kwargs={'post_id': comment.post.pk})

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author


class DeleteCommentView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'post_id': post_id})

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        try:
            post_obj = Post.objects.get(pk=self.kwargs.get('post_id'))
        except Post.DoesNotExist:
            return render(self.request, 'pages/404.html', status=404)
        form.instance.post = post_obj
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.kwargs.get('post_id')})
