from django.views.generic import TemplateView


class GoogleTestView(TemplateView):
    template_name = "google_test.html"