from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.conf import settings
from .models import Category, Post, Comment, User
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm, UserProfileForm, EditCommentForm, DeleteCommentForm, CommentForm
from django.core.paginator import Paginator


class PostCreateView(CreateView):
    """Создание поста."""

    model = Post
    fields = '__all__'
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.object.author.username})


class EditPostView(UpdateView):
    """Изменение поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.pk})


class DeletePostView(DeleteView):
    """Удаление поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.object.author.username})


class EditProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'blog/profile.html'
    success_url = reverse_lazy('blog:profile')

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def test_func(self):
        return self.request.user.username == self.kwargs.get('username')

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})

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
            author=self.object).order_by('-pub_date')
        # Показывать по 10 публикаций на странице
        paginator = Paginator(posts_list, 10)
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
    return render(request, "blog/index.html", {"page_obj": post_db})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
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
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = get_published_posts().filter(
        category=category
    )
    return render(
        request, "blog/category.html",
        {"category": category, "post_list": post_list}
    )


class EditCommentView(UpdateView):
    model = Comment
    form_class = EditCommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.post_id})


class DeleteCommentView(DeleteView):
    model = Comment
    form_class = DeleteCommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.post_id})


class AddCommentView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'includes:comments.html'  # Укажите здесь имя вашего шаблона

    def get_success_url(self):
        post_id = self.kwargs['post_id']
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post_id})

    def form_valid(self, form):
        form.instance.post_id = self.kwargs['post_id']
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return context
