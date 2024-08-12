from django.shortcuts import redirect
from django.db.models import Count

from .models import Post

from constants.constants import AMOUNT_POSTS


class AuthorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)


class PostListMixin:
    paginate_by = AMOUNT_POSTS

    def get_queryset(self):
        return Post.objects.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
