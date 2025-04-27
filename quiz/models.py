from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

#class CustomUser(AbstractUser):
#    USER_TYPE_CHOICES = (
#        (1, 'admin'),
#        (2, 'lecturer'),
#        (3, 'student'),
#    )
#    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=3)
#    pass

class Faculty(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.faculty})"

class Major(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.department}"

class Group(models.Model):
    name = models.CharField(max_length=50)
    year_of_creation = models.IntegerField()
    major = models.ForeignKey(Major, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.major})"

class Student(models.Model):
    name = models.CharField(max_length=100, default='Anun')
    last_name = models.CharField(max_length=100, default='Azganun')
    id_number = models.CharField(max_length=20, unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.id_number}"

class Lecturer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subjects = models.ManyToManyField('Subject')

    def __str__(self):
        return self.user.get_full_name()

class Subject(models.Model):
    name = models.CharField(max_length=100)
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    course = models.IntegerField()
    year = models.IntegerField()
    semester_choices = (
        (1, 'First Semester'),
        (2, 'Second Semester'),
    )
    semester = models.PositiveSmallIntegerField(choices=semester_choices)

    def __str__(self):
        return f"{self.name} - {self.major} (Year {self.year}, Semester {self.semester})"

class TestQuestion(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    question = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    score = models.IntegerField(default=1)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.question}"
        # return f"{self.subject}: {self.question[:50]}..."

class MidtermExam(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    questions = models.ManyToManyField(TestQuestion)
    due_date = models.DateTimeField()
    time_limit = models.IntegerField(default=40)  # in minutes

    def __str__(self):
        return f"{self.subject} - {self.group} (Due: {self.due_date})"

    def number_of_tests(self):
        return self.questions.count()

class Mark(models.Model):
    total = models.IntegerField(blank=False)
    got = models.IntegerField(blank=False, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Mark({self.got}/{self.total}, {self.user})"