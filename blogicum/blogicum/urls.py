from django.conf import settings

from django.conf.urls.static import static
from django.urls import path, include, reverse_lazy

from django.contrib import admin

from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm

from pages.views import Custom403View, Custom404View


urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls', namespace='pages')),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/',
         CreateView.as_view(
             template_name='registration/registration_form.html',
             form_class=UserCreationForm,
             success_url=reverse_lazy('blog:index'),),
         name='registration'),
    path('', include('blog.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT,)

handler404 = Custom404View.as_view()
handler403 = Custom403View.as_view()
handler500 = 'pages.views.custom_500'
