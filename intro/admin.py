from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import IntroQuestion


@admin.register(IntroQuestion)
class IntroQuestionAdmin(ModelAdmin):
    """Kirish testi savollari — rasm va video shu yerdan yuklanadi."""

    list_display = ('id', 'short_text', 'kind', 'correct_option', 'has_media', 'order', 'is_active')
    list_filter = ('kind', 'is_active')
    search_fields = ('text', 'text_ru', 'text_en')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'id')
    fieldsets = (
        ('Asosiy', {
            'fields': ('kind', 'correct_option', 'order', 'is_active'),
            'description': "Psixologik savolda to'g'ri javob bo'lmaydi — "
                           "«To'g'ri javob» maydonini bo'sh qoldiring.",
        }),
        ('Media', {
            'fields': ('image', 'video', 'video_url'),
            'description': "Video fayl 50 MB gacha. Server diski redeploy'da "
                           "tozalanadi, shuning uchun havola (video_url) ishonchliroq.",
        }),
        ("O'zbekcha", {'fields': ('text', 'options', 'explanation')}),
        ('Ruscha', {'fields': ('text_ru', 'options_ru', 'explanation_ru')}),
        ('Inglizcha', {'fields': ('text_en', 'options_en', 'explanation_en')}),
    )

    @admin.display(description='Savol')
    def short_text(self, obj):
        return obj.text[:60]

    @admin.display(description='Media', boolean=True)
    def has_media(self, obj):
        return bool(obj.image or obj.video or obj.video_url)
