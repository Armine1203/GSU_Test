from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Student'),
        (2, 'Instructor'),
        (3, 'Administrator'),
    )

    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)

    def is_student(self):
        return self.user_type == 1

    def is_instructor(self):
        return self.user_type == 2

    def is_admin(self):
        return self.user_type == 3

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'