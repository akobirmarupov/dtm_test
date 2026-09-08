from django.conf import settings
from django.views.generic import TemplateView


class GoogleTestView(TemplateView):
    """`/google-test/` — Google orqali ro'yxatdan o'tish/kirishni brauzerda
    sinab ko'rish sahifasi.

    Sahifa Google'dan `id_token` oladi va uni `/api/auth/google/` ga yuboradi,
    ya'ni haqiqiy ro'yxatdan o'tish oqimining o'zi. Faqat dev uchun.
    """

    template_name = "google_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Client id ni shablonga qo'lda yozib qo'ymaymiz — u `.env` dagi
        # `GOOGLE_CLIENT_ID` bilan bir xil bo'lishi kerak, aks holda backend
        # tokenni rad etadi va sabab ko'rinmaydi.
        context['google_client_id'] = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        context['debug'] = settings.DEBUG
        return context
