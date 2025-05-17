from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from quiz import views as quiz_views
from quizapp import views as core_views  # 'core' or 'main' or similar

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", core_views.Index.as_view(), name="index"),
    path("account/", include("account.urls")),
    path("quiz/", include("quiz.urls")),
    path("management/", include("management.urls")),
    path('get-question/<int:question_id>/', quiz_views.get_question, name='get_question'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)