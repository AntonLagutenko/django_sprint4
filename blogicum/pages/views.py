
from django.views.generic import TemplateView
from django.http import HttpResponseForbidden


class AboutView(TemplateView):
    template_name = 'pages/about.html'
    view_class = TemplateView


class RulesView(TemplateView):
    template_name = 'pages/rules.html'
    view_class = TemplateView


class CsrfFailureView(TemplateView):
    template_name = 'pages/403csrf.html'

    def post(self, request, *args, **kwargs):
        return HttpResponseForbidden()


def csrf_failure(request, *args, **kwargs):
    view = CsrfFailureView.as_view()
    return view(request, *args, **kwargs)


class Custom403View(TemplateView):
    template_name = 'pages/403csrf.html'
    status = 403

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = self.status
        return response


class Custom404View(TemplateView):
    template_name = 'pages/404.html'
    status = 404

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = self.status
        return response


class Custom500View(TemplateView):
    template_name = 'pages/500.html'
    status = 500

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = self.status
        return response


def custom_500(request):
    # Создаем экземпляр вашего класса представления
    view = Custom500View.as_view()

    # Вызываем его для получения HttpResponse объекта
    response = view(request)
    # Устанавливаем статус код на 500
    response.status_code = 500
    return response
