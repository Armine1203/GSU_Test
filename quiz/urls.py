from django.urls import path
from . import views

urlpatterns = [
    path("", views.Quiz.as_view(), name="quiz"),
    path("student/", views.StudentDashboard.as_view(), name="student_dashboard"),
    path("lecturer/", views.LecturerDashboard.as_view(), name="lecturer_dashboard"),
    path("add_question/", views.AddQuestion.as_view(), name="add_question"),
    path("result/", views.Result.as_view(), name="result"),
    path("leaderboard/", views.Leaderboard.as_view(), name="leaderboard")
]
