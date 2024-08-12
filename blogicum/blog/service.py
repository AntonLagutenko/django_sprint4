from django.utils.timezone import now
from .models import Post
from django.core.paginator import Paginator

from constants.constants import AMOUNT_POSTS


def get_published_posts():
    return Post.objects.select_related(
        "author", "category", "location"
    ).filter(
        is_published=True, pub_date__lt=now(), category__is_published=True
    )


def paginate_posts(request, posts):
    paginator = Paginator(posts, AMOUNT_POSTS)
    page = request.GET.get('page')
    return paginator.get_page(page)
