from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.conf import settings
from .models import Category, Post
from django.views.generic import CreateView






class PostCreateView(CreateView):
    model = Post
    fields = '__all__'
    template_name = 'blog/create.html'
    success_url = 'blog:index'


def get_published_posts():
    return Post.objects.select_related(
        "author", "category", "location"
    ).filter(
        is_published=True, pub_date__lt=now(), category__is_published=True
    )


def index(request):
    post_db = get_published_posts()[:settings.AMOUNT_POSTS]
    return render(request, "blog/index.html", {"post_list": post_db})


def post_detail(request, post_id):
    post = get_object_or_404(get_published_posts(), id=post_id)
    return render(request, "blog/detail.html", {"post": post})


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
