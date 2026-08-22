from django.urls import path

from testengine.routes.answer_view import (
    AnswerBulkCreateAPIView,
    AnswerDetailAPIView,
    AnswerListCreateAPIView,
)
from testengine.routes.testresult_view import (
    MyTestResultsAPIView,
    TestResultDetailAPIView,
    TestResultListAPIView,
)
from testengine.routes.testsession_view import (
    SessionQuestionDetailAPIView,
    SessionQuestionListAPIView,
    TestSessionDetailAPIView,
    TestSessionFinishAPIView,
    TestSessionListCreateAPIView,
    TestSessionNextQuestionAPIView,
    TestSessionProgressAPIView,
    TestSessionReviewAPIView,
    TestSessionSyncAPIView,
)

app_name = "testengine"

urlpatterns = [
    # Sessiya
    path("sessions/", TestSessionListCreateAPIView.as_view(), name="session-list-create"),
    path("sessions/<int:pk>/", TestSessionDetailAPIView.as_view(), name="session-detail"),

    # Test varaqasi: oldinga-orqaga yurish va javobni o'zgartirish
    path(
        "sessions/<int:pk>/questions/",
        SessionQuestionListAPIView.as_view(),
        name="session-questions",
    ),
    path(
        "sessions/<int:pk>/questions/<int:order>/",
        SessionQuestionDetailAPIView.as_view(),
        name="session-question-detail",
    ),
    path(
        "sessions/<int:pk>/questions/<int:order>/answer/",
        SessionQuestionDetailAPIView.as_view(),
        name="session-question-answer",
    ),

    path("sessions/<int:pk>/progress/", TestSessionProgressAPIView.as_view(), name="session-progress"),
    path("sessions/<int:pk>/next-question/", TestSessionNextQuestionAPIView.as_view(), name="session-next-question"),

    # Yakunlash va natija
    path("sessions/<int:pk>/finish/", TestSessionFinishAPIView.as_view(), name="session-finish"),
    path("sessions/<int:pk>/review/", TestSessionReviewAPIView.as_view(), name="session-review"),
    path("sessions/<int:pk>/sync/", TestSessionSyncAPIView.as_view(), name="session-sync"),

    # Javoblar (savol ID si bo'yicha)
    path("sessions/<int:session_id>/answers/", AnswerListCreateAPIView.as_view(), name="answer-list-create"),
    path("sessions/<int:session_id>/answers/bulk/", AnswerBulkCreateAPIView.as_view(), name="answer-bulk-create"),
    path(
        "sessions/<int:session_id>/answers/<int:answer_id>/",
        AnswerDetailAPIView.as_view(),
        name="answer-detail",
    ),

    # Natijalar
    path("results/", TestResultListAPIView.as_view(), name="result-list"),
    path("results/my-results/", MyTestResultsAPIView.as_view(), name="my-results"),
    path("results/<int:pk>/", TestResultDetailAPIView.as_view(), name="result-detail"),
]
