from django.contrib import admin

from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    search_fields = ("text",)
    list_display = (
        "id",
        "title",
        "author",
        "text",
        "category",
        "pub_date",
        "location",
        "is_published",
        "created_at",
    )
    list_display_links = ("title",)
    list_editable = ("category", "is_published", "location")
    list_filter = ("created_at",)
    empty_value_display = "Не задано"


admin.site.register(Post, PostAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_published", "created_at")
    list_editable = ("is_published",)
    empty_value_display = "Не задано"


admin.site.register(Location, LocationAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "slug", "is_published")
    list_display_links = ("title",)
    list_editable = ("description", "is_published")


admin.site.register(Category, CategoryAdmin)
