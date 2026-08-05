from django.urls import path
from catalog.routes.views import SubjectDetailAPIView, SubjectListCreateAPIView

app_name = "catalog"

urlpatterns = [
    path("subjects/", SubjectListCreateAPIView.as_view(), name="subject-list-create"),
    path("subjects/<int:pk>/", SubjectDetailAPIView.as_view(), name="subject-detail"),
]
