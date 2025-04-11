# from django.db import models
# from django.contrib.auth.models import User
# from django.utils import timezone
#
# # Create your models here.
# class Question(models.Model):
#     question = models.TextField(blank=False, unique=True)
#     option1 = models.CharField(blank=False, max_length=150)
#     option2 = models.CharField(blank=False, max_length=150)
#     option3 = models.CharField(blank=False, max_length=150)
#     option4 = models.CharField(blank=False, max_length=150)
#     correct_option = models.CharField(max_length=1)
#     creator = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
#     verified = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f"Question({self.question}, {self.creator})"
#
# class Mark(models.Model):
#     total = models.IntegerField(blank=False)
#     got = models.IntegerField(blank=False, default=0)
#     user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
#     created_at = models.DateTimeField(default=timezone.now)
#
#
#     def __str__(self):
#         return f"Mark({self.got}/{self.total}, {self.user})"

from django.db import models
from django.conf import settings  # Use this instead of direct User import

class Question(models.Model):
    question = models.TextField(unique=True)
    option1 = models.CharField(max_length=150)
    option2 = models.CharField(max_length=150)
    option3 = models.CharField(max_length=150)
    option4 = models.CharField(max_length=150)
    correct_option = models.CharField(max_length=1)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:50]}..."

class Mark(models.Model):
    total = models.PositiveIntegerField()
    got = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def percentage(self):
        return round((self.got / self.total) * 100, 2) if self.total > 0 else 0

    def __str__(self):
        return f"{self.user.username}: {self.got}/{self.total}"