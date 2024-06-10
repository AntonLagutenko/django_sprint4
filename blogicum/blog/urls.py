from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('category/<slug:category_slug>/', views.category_posts,
         name='category_posts'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    #path('profile/<str:username>/', views.UserProfileDetailView.as_view(), name='profile'),
    #path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    #path('profile/change_password/', views.ChangePasswordView.as_view(), name='password_change_form'),

]
