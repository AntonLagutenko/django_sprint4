from django.shortcuts import render


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403) 


def custom_403_view(request, exception=None):
    return render(request, 'pages/403.html', status=403)


def custom_404_view(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def custom_500_view(request):
    return render(request, 'pages/500.html', status=500)
