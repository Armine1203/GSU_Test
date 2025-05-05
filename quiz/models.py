from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

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
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='student', null=True)
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
    # group = models.ForeignKey(Group, on_delete=models.CASCADE)
    course = models.IntegerField()
    year = models.IntegerField()
    semester_choices = (
        (1, '1-ին կիսամյակ'),
        (2, '2-րդ կիսամյակ'),
    )
    semester = models.PositiveSmallIntegerField(choices=semester_choices)
    lecturers = models.ManyToManyField(User, related_name='taught_subjects')

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
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.question}"

class MidtermExam(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    questions = models.ManyToManyField(TestQuestion)
    due_date = models.DateTimeField()
    time_limit = models.IntegerField(default=40)  # in minutes
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,default=1)

    def __str__(self):
        return f"{self.subject} - {self.group} (Due: {self.due_date})"

    def number_of_tests(self):
        return self.questions.count()


class Mark(models.Model):
    total = models.IntegerField()
    got = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(MidtermExam, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def percentage(self):
        """Read-only property that calculates the percentage"""
        if self.total == 0:
            return 0
        return round((self.got / self.total) * 100, 2)

    def save(self, *args, **kwargs):
        """Optionally calculate and store percentage if needed"""
        # If you need to store percentage, add a field to the model
        # and calculate it here
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mark({self.got}/{self.total}, {self.user})"


class StudentAnswer(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question}: {self.answer} ({'Correct' if self.is_correct else 'Incorrect'})"


class ExamResult(models.Model):
    exam = models.ForeignKey(MidtermExam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)
    answers = models.ManyToManyField(StudentAnswer)

    @property
    def total_questions(self):
        return self.exam.questions.count()

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 2)

    def __str__(self):
        return f"{self.student} - {self.exam} ({self.score}/{self.total_questions})"