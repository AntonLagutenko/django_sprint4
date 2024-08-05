from constants.my_constants import (
    REPRESENTATION_LENGTH,
    MAX_FIELD_LENGTH,
    MAX_COMMENT_LENGTH
)

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class BasePublication(models.Model):
    is_published = models.BooleanField(
        "Опубликовано",
        default=True,
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ("created_at",)


class Location(BasePublication):
    name = models.CharField(
        "Название места", max_length=MAX_FIELD_LENGTH)

    class Meta(BasePublication.Meta):
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"

    def __str__(self):
        return self.name[:REPRESENTATION_LENGTH]


class Category(BasePublication):
    title = models.CharField("Заголовок", max_length=MAX_FIELD_LENGTH)
    description = models.TextField("Описание")
    slug = models.SlugField(
        "Идентификатор",
        help_text=(
            "Идентификатор страницы для URL; "
            "разрешены символы латиницы, цифры, дефис и подчёркивание."
        ),
        unique=True,
    )

    class Meta(BasePublication.Meta):
        verbose_name = "категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title[:REPRESENTATION_LENGTH]


class Post(BasePublication):
    title = models.CharField("Заголовок", max_length=MAX_FIELD_LENGTH)
    text = models.TextField("Текст")
    pub_date = models.DateTimeField(
        "Дата и время публикации",
        default=timezone.now,
        help_text=('Если установить дату и время в будущем — '
                   'можно делать отложенные публикации.')
    )
    image = models.ImageField(verbose_name='Картинка у публикации', blank=True)

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Автор публикации"
    )

    location = models.ForeignKey(
        Location,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Местоположение"
    )

    category = models.ForeignKey(
        Category,
        null=True, on_delete=models.SET_NULL, verbose_name="Категория"
    )

    class Meta():
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"
        default_related_name = "posts"
        ordering = ("-pub_date",)

    def comments_count(self):
        return self.post_comments.count()

    def __str__(self):
        return self.title[:REPRESENTATION_LENGTH]


class Comment(BasePublication):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='user_comments'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Комментируемый пост',
        related_name='post_comments'
    )
    text = models.TextField(verbose_name='Текст комментария')

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def __str__(self) -> str:
        return self.text[:MAX_COMMENT_LENGTH]
