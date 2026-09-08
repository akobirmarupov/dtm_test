from django.urls import path
from catalog.routes.views import (
    SubjectDetailAPIView, SubjectListCreateAPIView,
    GradeDetailAPIView, GradeListCreateAPIView,
    TopicDetailAPIView, TopicListCreateAPIView,
    QuestionDetailAPIView, QuestionListCreateAPIView,
)

app_name = "catalog"

urlpatterns = [
    path("subjects/", SubjectListCreateAPIView.as_view(), name="subject-list-create"),
    path("subjects/<int:pk>/", SubjectDetailAPIView.as_view(), name="subject-detail"),
    
    # Fan -> Sinf/Kitob -> Mavzu -> Savol
    path("grades/", GradeListCreateAPIView.as_view(), name="grade-list-create"),
    path("grades/<int:pk>/", GradeDetailAPIView.as_view(), name="grade-detail"),

    path("topics/", TopicListCreateAPIView.as_view(), name="topic-list-create"),
    path("topics/<int:pk>/", TopicDetailAPIView.as_view(), name="topic-detail"),
    
    path("questions/", QuestionListCreateAPIView.as_view(), name="question-list-create"),
    path("questions/<int:pk>/", QuestionDetailAPIView.as_view(), name="question-detail"),
]
