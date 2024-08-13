from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import (CommentForm, PostForm, UserProfileForm)

from .mixins import (AuthorRequiredMixin, PostListMixin)

from .service import (get_published_posts, paginate_posts)

from .models import (Category, Comment, Post, User)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditPostView(LoginRequiredMixin, AuthorRequiredMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:post_detail', args=(self.object.pk,))


class AutRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return HttpResponseRedirect(reverse('blog:post_detail',
                                                kwargs={'post_id': obj.pk}))
        return super().dispatch(request, *args, **kwargs)


class DeletePostView(LoginRequiredMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})

    # не знаю как избавиться от этой конструкции
    # тест не проходит никак, кроме использования try except и прочего

    def dispatch(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Http404:
            if request.method == 'POST':
                return HttpResponseNotFound('Пост не найден')
            else:
                raise Http404('Пост не найден')
        if obj.author != self.request.user:
            return HttpResponseRedirect(reverse('blog:post_detail',
                                                kwargs={'post_id': obj.pk}))
        return super().dispatch(request, *args, **kwargs)


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context


class UserProfileView(PostListMixin, ListView):
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'

    def get_queryset(self):
        self.author = get_object_or_404(User,
                                        username=self.kwargs.get('username'))
        if self.request.user == self.author:
            return super().get_queryset().select_related('author').filter(
                author=self.author
            )
        else:
            return super().get_queryset().select_related('author').filter(
                author=self.author,
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


def index(request):
    post_db = get_published_posts().annotate(
        comments_count=Count('comments')
    ).order_by('-pub_date')
    page_obj = paginate_posts(request, post_db)
    for post in page_obj:
        post.title = f"{post.title} ({post.comments_count})"
    return render(request, "blog/index.html", {"page_obj": page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author', 'category'),
                             id=post_id)
    if (not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()) and post.author != request.user:
        raise Http404("Post not found")
    comments = post.comments.all().order_by('created_at')
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
        comments_count=Count('comments')
    ).order_by('-pub_date')
    page_obj = paginate_posts(request, post_list)
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
