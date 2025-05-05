from django.urls import path
from . import views
from .views import UploadQuestion, DownloadQuestionTemplate

urlpatterns = [
    path("", views.Manage.as_view(), name="manage"),
    path('upload_questions/', UploadQuestion.as_view(), name='upload_question'),
    path('download-question-template/', DownloadQuestionTemplate.as_view(), name='download_question_template'),
]
