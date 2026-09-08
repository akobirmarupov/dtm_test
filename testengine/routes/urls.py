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
from testengine.routes.guest_view import (
    GuestStartTestAPIView,
    GuestSubmitTestAPIView,
    GuestTopicsAPIView,
)
from testengine.routes.mistake_view import (
    MistakeListAPIView,
    MistakeStartTestAPIView,
)
from testengine.routes.topic_test_view import (
    MyTestLimitsAPIView,
    TopicAvailableCountsAPIView,
    TopicStartTestAPIView,
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
    # --- Mavzu bo'yicha test: son tanlash va boshlash ---------------------
    path(
        "topics/<int:topic_id>/available-counts/",
        TopicAvailableCountsAPIView.as_view(),
        name="topic-available-counts",
    ),
    path(
        "topics/<int:topic_id>/start-test/",
        TopicStartTestAPIView.as_view(),
        name="topic-start-test",
    ),
    path("my-limits/", MyTestLimitsAPIView.as_view(), name="my-limits"),

    # --- Xatolar banki ----------------------------------------------------
    path("mistakes/", MistakeListAPIView.as_view(), name="mistake-list"),
    path("mistakes/start-test/", MistakeStartTestAPIView.as_view(), name="mistake-start-test"),

    # --- Guest (ro'yxatdan o'tmagan) oqimi --------------------------------
    path("guest/topics/", GuestTopicsAPIView.as_view(), name="guest-topics"),
    path("guest/start/", GuestStartTestAPIView.as_view(), name="guest-start"),
    path("guest/submit/", GuestSubmitTestAPIView.as_view(), name="guest-submit"),

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
