from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls', namespace='pages')),
    path('', include('blog.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration')
    

]
handler404 = 'core.views.custom_404_view' 
handler500 = 'core.views.custom_500_view' 
handler403 = 'core.views.custom_403_view'