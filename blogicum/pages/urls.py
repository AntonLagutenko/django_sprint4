from django.urls import path
from .views import (
    CsrfFailureView,
    Custom403View,
    Custom404View,
    AboutView,
    RulesView
)

app_name = 'pages'

urlpatterns = [
    path('about/', AboutView.as_view(), name='about'),
    path('rules/', RulesView.as_view(), name='rules'),
    path('403csrf/', CsrfFailureView.as_view(), name='403csrf'),
    path('403/', Custom403View.as_view(), name='custom_403'),
    path('404/', Custom404View.as_view(), name='custom_404'),
]

handler500 = 'pages.views.custom_500'
