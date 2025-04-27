from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import *


class Command(BaseCommand):
    help = 'Creates initial users (admin, lecturer, student)'

    def handle(self, *args, **options):
        User = get_user_model()

        # Create admin
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@gsu.am',
            password='admin123',
            user_type=1,
            first_name='Admin',
            last_name='GSU'
        )

        # Create faculty, department, major
        faculty = Faculty.objects.create(name='Computer Science')
        department = Department.objects.create(name='Software Engineering', faculty=faculty)
        major = Major.objects.create(name='Computer Science', faculty=faculty, department=department)

        # Create group
        group = Group.objects.create(
            name='CS-101',
            year_of_creation=2024,
            major=major
        )

        # Create lecturer
        lecturer_user = User.objects.create_user(
            username='lecturer1',
            email='lecturer@gsu.am',
            password='lecturer123',
            user_type=2,
            first_name='John',
            last_name='Smith'
        )

        # Create subject
        subject = Subject.objects.create(
            name='Programming Basics',
            major=major,
            course=1,
            year=1,
            semester=1
        )

        # Assign subject to lecturer
        lecturer = Lecturer.objects.create(user=lecturer_user)
        lecturer.subjects.add(subject)

        # Create student
        student_user = User.objects.create_user(
            username='student1',
            email='student@gsu.am',
            password='student123',
            user_type=3,
            first_name='Alice',
            last_name='Johnson'
        )

        Student.objects.create(
            user=student_user,
            id_number='S12345',
            group=group
        )

        self.stdout.write(self.style.SUCCESS('Successfully created initial users'))