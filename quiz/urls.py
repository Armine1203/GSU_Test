from django.urls import path
from . import views
from .views import (
    AddSubject,
    get_groups_for_subject,
    results,
    Quiz,
    QuestionAPIView,
)

urlpatterns = [
    path("", views.Quiz.as_view(), name="quiz"),
    path("student/", views.StudentDashboard.as_view(), name="student_dashboard"),
    path("lecturer/", views.LecturerDashboard.as_view(), name="lecturer_dashboard"),
    path('leaderboard/', views.Leaderboard.as_view(), name='leaderboard'),
    path('leaderboard/<int:exam_id>/', views.Leaderboard.as_view(), name='exam_leaderboard'),

    # Question management URLs
    path('questions/<int:subject_id>/', views.ViewQuestions.as_view(), name='view_questions'),
    path('questions/delete/<int:pk>/', views.DeleteQuestion.as_view(), name='delete_question'),
    path('add_questions/', views.AddQuestion.as_view(), name='add_question'),
    path('get-question/<int:question_id>/', views.get_question, name='get_question'),
    path('update-question/', views.update_question, name='update_question'),

    # API endpoints
    path('api/questions/', views.api_questions_list, name='api_questions_list'),
    path('api/questions/<int:pk>/', QuestionAPIView.as_view(), name='question-api'),
    path('api/groups/', get_groups_for_subject, name='get_groups'),

    # Exam management URLs
    path('create-exam/', views.create_exam, name='create_exam'),
    path('select_question_count/', views.SelectQuestionCount.as_view(), name='select_question_count'),
    path('add_subject/', AddSubject.as_view(), name='add_subject'),
    path('exam/<int:exam_id>/', views.exam_detail_view, name='exam_detail'),

    # Results URLs (new implementation)
    path('quiz/', Quiz.as_view(), name='quiz'),
    path('results/', results, name='results'),  # List of all results
    path('results/<int:result_id>/', views.result_detail, name='result_detail'),  # Detailed view of a specific result

    # feedback
    path('feedback/', views.feedback_view, name='feedback_form'),
    path('feedback/success/', views.feedback_success, name='feedback_success'),
    path('ajax/load-questions/', views.load_questions, name='ajax_load_questions'),

    # caTEGORY
    path('create-category/', views.create_category, name='create_category'),
    # path('delete_category/<int:category_id>/', views.delete_category, name='delete_category'),
    # path('update-category/<int:category_id>/', views.update_category, name='update_category'),

]
