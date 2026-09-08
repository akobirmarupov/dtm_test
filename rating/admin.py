from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Leaderboard, League, LeagueMembership,
    Rating, RatingHistory, SubjectRating, TopicRating,
)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 
        'period_display', 
        'stars_display', 
        'xp',
        'tests_completed', 
        'accuracy_percentage_display',
        'rank',
        'last_updated'
    )
    list_filter = ('period', 'period_start_date', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = (
        'created_at', 'updated_at', 'last_updated', 'rank',
        'earned_points', 'possible_points',
    )
    
    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user', 'period')
        }),
        ('Reytinglar', {
            'fields': ('stars', 'xp', 'rank'),
            'description': "Leaderboard XP bo'yicha saralanadi, ⭐ esa shaxsiy daraja. "
                           "`rank` ni qo'lda tahrirlash mumkin emas — u "
                           "`rebuild_leaderboard()` da butun ro'yxat uchun hisoblanadi.",
        }),
        ('Statistika', {
            'fields': (
                'tests_completed', 'correct_answers', 'incorrect_answers',
                'unanswered_answers', 'earned_points', 'possible_points',
            )
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('period_start_date', 'period_end_date', 'last_updated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def period_display(self, obj):
        colors = {
            'daily': '#3498db',
            'weekly': '#2ecc71',
            'all_time': '#e74c3c'
        }
        color = colors.get(obj.period, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_period_display()
        )
    period_display.short_description = 'Davr'
    
    def stars_display(self, obj):
        stars = '⭐' * int(obj.stars)
        return f'{obj.stars:.1f} {stars}'
    stars_display.short_description = '⭐ Yulduzlar'
    
    def accuracy_percentage_display(self, obj):
        accuracy = obj.accuracy_percentage
        if accuracy >= 80:
            color = '#27ae60'
        elif accuracy >= 60:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        accuracy_text = f'{accuracy:.1f}%'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            accuracy_text
        )
    accuracy_percentage_display.short_description = "To'g'rilik %"
    
    ordering = ['-stars', '-tests_completed']


@admin.register(RatingHistory)
class RatingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'period_display',
        'change_display',
        'rank_change_display',
        'reason',
        'created_at'
    )
    list_filter = ('period', 'created_at', 'rating__period')
    search_fields = ('user__email', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user', 'rating', 'period', 'test_session')
        }),
        ('O\'zgarishlar', {
            'fields': ('previous_stars', 'new_stars', 'stars_change', 'reason')
        }),
        ('Reyting Joylanishi', {
            'fields': ('previous_rank', 'new_rank'),
            'classes': ('collapse',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def period_display(self, obj):
        colors = {'daily': '#3498db', 'weekly': '#2ecc71', 'all_time': '#e74c3c'}
        color = colors.get(obj.period, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_period_display()
        )
    period_display.short_description = 'Davr'
    
    def change_display(self, obj):
        change_text = f'{obj.stars_change:.1f}'
        if obj.stars_change >= 0:
            return format_html(
                '<span style="color: #27ae60;">⬆️ +{} ⭐</span>',
                change_text
            )
        else:
            return format_html(
                '<span style="color: #e74c3c;">⬇️ {} ⭐</span>',
                change_text
            )
    change_display.short_description = 'O\'zgarish'
    
    def rank_change_display(self, obj):
        if obj.previous_rank is None or obj.new_rank is None:
            return '—'
        change = obj.previous_rank - obj.new_rank
        if change > 0:
            return format_html(
                '<span style="color: #27ae60;">⬆️ #{} → #{}</span>',
                obj.previous_rank,
                obj.new_rank
            )
        elif change < 0:
            return format_html(
                '<span style="color: #e74c3c;">⬇️ #{} → #{}</span>',
                obj.previous_rank,
                obj.new_rank
            )
        else:
            return f'#{obj.new_rank}'
    rank_change_display.short_description = 'Reyting O\'zgarishi'
    
    ordering = ['-created_at']


@admin.register(TopicRating)
class TopicRatingAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'topic_name',
        'stars_display',
        'tests_completed',
        'accuracy_percentage_display',
        'last_updated'
    )
    list_filter = ('created_at', 'last_updated', 'topic__subject')
    search_fields = ('user__email', 'topic__name')
    readonly_fields = ('created_at', 'updated_at', 'last_updated')
    
    fieldsets = (
        ('Bog\'lanishlar', {
            'fields': ('user', 'topic')
        }),
        ('Reyting', {
            'fields': ('stars',)
        }),
        ('Statistika', {
            'fields': ('tests_completed', 'correct_answers', 'incorrect_answers')
        }),
        ('Vaqt', {
            'fields': ('last_updated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def topic_name(self, obj):
        return f"{obj.topic.subject.name} → {obj.topic.name}"
    topic_name.short_description = 'Fan → Mavzu'
    
    def stars_display(self, obj):
        stars = '⭐' * int(obj.stars)
        return f'{obj.stars:.1f} {stars}'
    stars_display.short_description = '⭐'
    
    def accuracy_percentage_display(self, obj):
        accuracy = obj.accuracy_percentage
        color = '#27ae60' if accuracy >= 80 else '#f39c12' if accuracy >= 60 else '#e74c3c'
        accuracy_text = f'{accuracy:.1f}%'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            accuracy_text
        )
    accuracy_percentage_display.short_description = "To'g'rilik %"
    
    ordering = ['-stars']


@admin.register(SubjectRating)
class SubjectRatingAdmin(admin.ModelAdmin):
    list_display = (
        'user_email',
        'subject_name',
        'stars_display',
        'tests_completed',
        'topics_completed',
        'accuracy_percentage_display',
        'last_updated'
    )
    list_filter = ('created_at', 'last_updated', 'subject')
    search_fields = ('user__email', 'subject__name')
    readonly_fields = ('created_at', 'updated_at', 'last_updated')
    
    fieldsets = (
        ('Bog\'lanishlar', {
            'fields': ('user', 'subject')
        }),
        ('Reyting', {
            'fields': ('stars',)
        }),
        ('Statistika', {
            'fields': ('tests_completed', 'topics_completed', 'correct_answers', 'incorrect_answers')
        }),
        ('Vaqt', {
            'fields': ('last_updated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def subject_name(self, obj):
        return obj.subject.name
    subject_name.short_description = 'Fan'
    
    def stars_display(self, obj):
        stars = '⭐' * int(obj.stars)
        return f'{obj.stars:.1f} {stars}'
    stars_display.short_description = '⭐'
    
    def accuracy_percentage_display(self, obj):
        accuracy = obj.accuracy_percentage
        color = '#27ae60' if accuracy >= 80 else '#f39c12' if accuracy >= 60 else '#e74c3c'
        accuracy_text = f'{accuracy:.1f}%'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            accuracy_text
        )
    accuracy_percentage_display.short_description = "To'g'rilik %"
    
    ordering = ['-stars']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Leaderboardning tayyor kesimi. Bu jadvalga `rebuild_leaderboard()`
    yozadi — qo'lda tahrirlash ma'nosiz, keyingi hisobda qayta yoziladi."""

    list_display = (
        'rank_display',
        'user_email',
        'period_display',
        'xp',
        'stars_display',
        'tests_completed',
        'period_start_date',
    )
    list_filter = ('period', 'period_start_date')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = (
        'period', 'period_start_date', 'period_end_date', 'rank', 'user',
        'xp', 'stars', 'tests_completed', 'generated_at', 'created_at', 'updated_at',
    )
    ordering = ('period', 'rank')

    fieldsets = (
        ('Qator', {'fields': ('period', 'rank', 'user')}),
        ('Ko\'rsatkichlar', {'fields': ('xp', 'stars', 'tests_completed')}),
        ('Davr', {
            'fields': (
                'period_start_date', 'period_end_date', 'generated_at',
                'created_at', 'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False
    
    def rank_display(self, obj):
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        medal = medals.get(obj.rank, '')
        return format_html(
            '{}  <span style="font-weight: bold;">#{}</span>',
            medal,
            obj.rank
        )
    rank_display.short_description = 'O\'rni'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Foydalanuvchi'
    
    def period_display(self, obj):
        colors = {'daily': '#3498db', 'weekly': '#2ecc71', 'all_time': '#e74c3c'}
        color = colors.get(obj.period, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_period_display()
        )
    period_display.short_description = 'Davr'
    
    def stars_display(self, obj):
        stars = '⭐' * int(obj.stars)
        return f'{obj.stars:.1f} {stars}'
    stars_display.short_description = '⭐'


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    """Haftalik liga guruhi (30 kishilik)."""

    list_display = ('__str__', 'tier', 'group_number', 'period_start_date',
                    'member_count', 'is_closed')
    list_filter = ('tier', 'is_closed', 'period_start_date')
    search_fields = ('group_number', 'period_start_date')
    ordering = ('-period_start_date', '-tier', 'group_number')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description="A'zolar")
    def member_count(self, obj):
        return obj.memberships.count()


@admin.register(LeagueMembership)
class LeagueMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'league', 'xp', 'rank', 'outcome')
    list_filter = ('outcome', 'league__tier', 'league__period_start_date')
    search_fields = ('user__email', 'user__full_name')
    autocomplete_fields = ('user', 'league')
    ordering = ('-league__period_start_date', 'league', '-xp')
    readonly_fields = ('rank', 'outcome', 'created_at', 'updated_at')
