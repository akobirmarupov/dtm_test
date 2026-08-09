from django.urls import path

from progress.routes.reviewcard_view import ReviewCardListAPIView, ReviewCardTodayAPIView, ReviewCardSubmitAPIview
from progress.routes.streak_view import StreakDetailAPIView, StreakFreezeAPIView
from progress.routes.transaktion_view import XPTransactionListAPIView, XPSummaryAPIView, WeeklyLeaderboardAPIView

urlpatterns = [
    # ReviewCard
    path('reviews/', ReviewCardListAPIView.as_view(), name='review-card-list'),
    path('reviews/today/', ReviewCardTodayAPIView.as_view(), name='review-card-today'),
    path('reviews/<int:pk>/submit/', ReviewCardSubmitAPIview.as_view(), name='review-card-submit'),

    # Streak
    path('streak/', StreakDetailAPIView.as_view(), name='streak-detail'),
    path('streak/freeze/', StreakFreezeAPIView.as_view(), name='streak-freeze'),

    # XP
    path('xp/transactions/', XPTransactionListAPIView.as_view(), name='xp-transaction-list'),
    path('xp/summary/', XPSummaryAPIView.as_view(), name='xp-summary'),
    path('leaderboard/weekly/', WeeklyLeaderboardAPIView.as_view(), name='leaderboard-weekly'),
]
