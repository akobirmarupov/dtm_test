from django.urls import path

from rating.routes.rating_view import MyRatingAPIView
from rating.routes.leaderboard_view import LeaderboardListAPIView
from rating.routes.topicrating_view import TopicRatingListAPIView, TopicRatingDetailAPIView
from rating.routes.subjectrating_view import SubjectRatingListAPIView, SubjectRatingDetailAPIView
from rating.routes.ratinghistory_view import RatingHistoryListAPIView

urlpatterns = [
    # Rating (umumiy: daily/weekly/all_time)
    path('me/', MyRatingAPIView.as_view(), name='rating-me'),

    # Leaderboard
    path('leaderboard/<str:period>/', LeaderboardListAPIView.as_view(), name='rating-leaderboard'),

    # TopicRating
    path('topics/', TopicRatingListAPIView.as_view(), name='rating-topic-list'),
    path('topics/<int:topic_id>/', TopicRatingDetailAPIView.as_view(), name='rating-topic-detail'),

    # SubjectRating
    path('subjects/', SubjectRatingListAPIView.as_view(), name='rating-subject-list'),
    path('subjects/<int:subject_id>/', SubjectRatingDetailAPIView.as_view(), name='rating-subject-detail'),

    # RatingHistory
    path('history/', RatingHistoryListAPIView.as_view(), name='rating-history'),
]
