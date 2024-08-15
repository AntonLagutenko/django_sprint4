from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse

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


class AutRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != self.request.user:
            return HttpResponseRedirect(reverse('blog:post_detail',
                                                kwargs={'post_id': obj.pk}))
        return super().dispatch(request, *args, **kwargs)
