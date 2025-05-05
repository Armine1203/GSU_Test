from django.urls import path
from . import views
from .views import (
    AddSubject,
    get_groups_for_subject,
    results,  # Add this import
    result_detail, Quiz,  # Add this import
)

urlpatterns = [
    path("", views.Quiz.as_view(), name="quiz"),
    path("student/", views.StudentDashboard.as_view(), name="student_dashboard"),
    path("lecturer/", views.LecturerDashboard.as_view(), name="lecturer_dashboard"),
    path("leaderboard/", views.Leaderboard.as_view(), name="leaderboard"),

    # Question management URLs
    path('questions/<int:subject_id>/', views.ViewQuestions.as_view(), name='view_questions'),
    path('questions/delete/<int:pk>/', views.DeleteQuestion.as_view(), name='delete_question'),
    path('add_questions/', views.AddQuestion.as_view(), name='add_question'),

    # API endpoints
    path('api/questions/', views.api_questions_list, name='api_questions_list'),
    path('api/questions/<int:pk>/', views.api_question_detail, name='api_question_detail'),
    path('api/groups/', get_groups_for_subject, name='get_groups'),

    # Exam management URLs
    path('create-exam/', views.create_exam, name='create_exam'),
    path('select_question_count/', views.SelectQuestionCount.as_view(), name='select_question_count'),
    path('add_subject/', AddSubject.as_view(), name='add_subject'),

    # Results URLs (new implementation)
    path('quiz/', Quiz.as_view(), name='quiz'),
    path('results/', results, name='results'),  # List of all results
    path('results/<int:result_id>/', views.result_detail, name='result_detail'),  # Detailed view of a specific result
]