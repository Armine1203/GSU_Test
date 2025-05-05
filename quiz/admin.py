from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import *

# Unregister the default User admin if needed
from django.contrib.auth import get_user_model

User = get_user_model()


# Register your models here
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty')
    list_filter = ('faculty',)
    search_fields = ('name', 'faculty__name')


class MajorAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'department')
    list_filter = ('faculty', 'department')
    search_fields = ('name', 'faculty__name', 'department__name')


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'year_of_creation', 'major')
    list_filter = ('major', 'year_of_creation')
    search_fields = ('name', 'major__name')
    filter_horizontal = ()


class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_name', 'id_number', 'group')
    list_filter = ('group',)
    search_fields = ('last_name', 'id_number')
    #raw_id_fields = ('user',)


class LecturerAdmin(admin.ModelAdmin):
    list_display = ('user', 'subjects_list')
    filter_horizontal = ('subjects',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

    def subjects_list(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])

    subjects_list.short_description = 'Subjects'


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'major', 'course', 'year', 'semester')
    list_filter = ('major', 'course', 'year', 'semester')
    search_fields = ('name', 'major__name')


class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'subject', 'correct_option', 'score', 'creator')
    list_filter = ('subject', 'creator')
    search_fields = ('question', 'subject__name')

    def question_short(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question

    question_short.short_description = 'Question'


class MidtermExamAdmin(admin.ModelAdmin):
    list_display = ('subject', 'group', 'due_date', 'time_limit', 'questions_count')
    list_filter = ('subject', 'group')
    filter_horizontal = ('questions',)
    date_hierarchy = 'due_date'

    def questions_count(self, obj):
        return obj.questions.count()

    questions_count.short_description = 'Questions'


#admin.site.register(User, CustomUserAdmin)
admin.site.register(Faculty, FacultyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Major, MajorAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Lecturer, LecturerAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(TestQuestion, TestQuestionAdmin)
admin.site.register(MidtermExam, MidtermExamAdmin)