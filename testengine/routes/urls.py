from django.urls import path

from testengine.routes.testsession_view import (
    TestSessionListCreateAPIView, TestSessionDetailAPIView,
    TestSessionNextQuestionAPIView, TestSessionFinishAPIView,
    TestSessionSyncAPIView
)
from testengine.routes.answer_view import (
    AnswerListCreateAPIView, AnswerDetailAPIView,
    AnswerBulkCreateAPIView
)
from testengine.routes.testresult_view import (
    TestResultListAPIView, TestResultDetailAPIView,
    MyTestResultsAPIView
)

app_name = "testengine"

urlpatterns = [
    # TestSession URLs
    path("sessions/", TestSessionListCreateAPIView.as_view(), name="session-list-create"),
    path("sessions/<int:pk>/", TestSessionDetailAPIView.as_view(), name="session-detail"),
    path("sessions/<int:pk>/next-question/", TestSessionNextQuestionAPIView.as_view(), name="session-next-question"),
    path("sessions/<int:pk>/finish/", TestSessionFinishAPIView.as_view(), name="session-finish"),
    path("sessions/<int:pk>/sync/", TestSessionSyncAPIView.as_view(), name="session-sync"),
    
    # Answer URLs
    path("sessions/<int:session_id>/answers/", AnswerListCreateAPIView.as_view(), name="answer-list-create"),
    path("sessions/<int:session_id>/answers/<int:answer_id>/", AnswerDetailAPIView.as_view(), name="answer-detail"),
    path("sessions/<int:session_id>/answers/bulk/", AnswerBulkCreateAPIView.as_view(), name="answer-bulk-create"),
    
    # TestResult URLs
    path("results/", TestResultListAPIView.as_view(), name="result-list"),
    path("results/<int:pk>/", TestResultDetailAPIView.as_view(), name="result-detail"),
    path("results/my-results/", MyTestResultsAPIView.as_view(), name="my-results"),
]
