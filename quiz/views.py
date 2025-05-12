import json

from django.db import models
from django.db.models import Prefetch, Avg, Count, F, Sum, Exists, OuterRef, When, Case, BooleanField
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from .forms import SubjectForm, MidtermExamForm
from .models import TestQuestion, Lecturer, Subject, Group, StudentAnswer, ExamResult, Mark, MidtermExam, Student
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.generic import View
from docx import Document
from openpyxl import Workbook
from io import BytesIO

# Create your views here.
@method_decorator(login_required, name="dispatch")
class Quiz(View):
    def get(self, request):
        exam_id = request.GET.get('exam_id')

        if exam_id:
            try:
                exam = MidtermExam.objects.get(id=exam_id)
                # Check if student already attempted this exam
                if Mark.objects.filter(user=request.user, exam=exam).exists():
                    messages.error(request, "Դուք արդեն անցել եք այս քննությունը")
                    return redirect("student_dashboard")

                questions = exam.questions.all()
                return render(request, "quiz/quiz.html", {
                    "questions": questions,
                    "time_limit": exam.time_limit * 60,
                    "start_time": timezone.now().isoformat(),
                    "exam": exam  # Make sure to pass the exam object
                })

            except MidtermExam.DoesNotExist:
                messages.error(request, "Քննությունը չի գտնվել")
                return redirect("student_dashboard")

        messages.error(request, "Չի նշվել քննություն")
        return redirect("student_dashboard")

    def post(self, request):
        exam_id = request.POST.get('exam_id')
        try:
            exam = MidtermExam.objects.get(id=exam_id)

            # Check if already taken
            if Mark.objects.filter(user=request.user, exam=exam).exists():
                messages.error(request, "You have already taken this exam")
                return redirect("student_dashboard")

            # Calculate score and prepare answers
            correct = 0
            student_answers = []

            for i in range(1, exam.questions.count() + 1):
                user_answer = request.POST.get(f'q{i}o')
                try:
                    question = exam.questions.get(id=request.POST.get(f'q{i}'))
                    is_correct = user_answer == question.correct_option
                    if is_correct:
                        correct += 1

                    # Create StudentAnswer instance
                    answer = StudentAnswer.objects.create(
                        question=question,
                        answer=user_answer,
                        is_correct=is_correct
                    )
                    student_answers.append(answer)

                except (TestQuestion.DoesNotExist, ValueError):
                    continue

            # Create Mark
            mark = Mark.objects.create(
                user=request.user,
                exam=exam,
                total=exam.questions.count(),
                got=correct
            )

            # Create ExamResult
            exam_result = ExamResult.objects.create(
                exam=exam,
                student=request.user.student,
                score=correct
            )

            # Add answers to the ExamResult
            exam_result.answers.set(student_answers)

            return redirect("result_detail", result_id=mark.id)

        except MidtermExam.DoesNotExist:
            messages.error(request, "Exam not found")
            return redirect("student_dashboard")

@method_decorator(login_required, name="dispatch")
class AddQuestion(View):
    def get(self, request):
        if not hasattr(request.user, 'lecturer'):
            messages.error(request, "Only lecturers can add questions")
            return redirect("index")

        # Get parameters with defaults
        try:
            question_count = int(request.GET.get('count', 10))
            question_count = max(1, min(50, question_count))  # Limit between 1-50
        except ValueError:
            question_count = 10

        subject_id = request.GET.get('subject')
        lecturer = request.user.lecturer
        subject = None

        if subject_id:
            try:
                subject = Subject.objects.get(id=subject_id)
                if subject not in lecturer.subjects.all():
                    subject = None
            except Subject.DoesNotExist:
                pass

        return render(
            request,
            "quiz/add_questions.html",
            {
                "questions": range(1, question_count + 1),
                "lecturer": lecturer,
                "subjects": lecturer.subjects.all(),
                "selected_subject": subject,
                "question_count": question_count
            }
        )

    def post(self, request):
        if not hasattr(request.user, 'lecturer'):
            messages.error(request, "Only lecturers can add questions")
            return redirect("index")

        lecturer = request.user.lecturer
        subject_id = request.POST.get("subject")

        try:
            subject = Subject.objects.get(id=subject_id)
            if subject not in lecturer.subjects.all():
                messages.error(request, "You don't teach this subject")
                return redirect("add_question")
        except Subject.DoesNotExist:
            messages.error(request, "Invalid subject selected")
            return redirect("add_question")

        count, already_exists = 0, 0
        for i in range(1, int(request.POST.get("question_count", 10)) + 1):
            data = request.POST
            files = request.FILES

            q = data.get(f"q{i}", "").strip()
            if not q:  # Skip empty questions
                continue

            o1 = data.get(f"q{i}o1", "").strip()
            o2 = data.get(f"q{i}o2", "").strip()
            o3 = data.get(f"q{i}o3", "").strip()
            o4 = data.get(f"q{i}o4", "").strip()
            co = data.get(f"q{i}c", "")
            score = int(data.get(f"q{i}score", 1))
            image = files.get(f"q{i}image")

            if TestQuestion.objects.filter(question=q, subject=subject).exists():
                already_exists += 1
                continue

            question = TestQuestion(
                subject=subject,
                question=q,
                option1=o1,
                option2=o2,
                option3=o3,
                option4=o4,
                correct_option=co,
                score=score,
                creator=request.user,
                image=image
            )
            question.save()
            count += 1

        if already_exists:
            messages.warning(request, f"{already_exists} questions already exist for this subject")
        if count:
            messages.success(request, f"Հաջողությամբ {count} հարց ավելացվել է {subject.name} առարկայի համար")
        else:
            messages.warning(request, "Հարցեր չկան ավելացվելու համար")

        return redirect("lecturer_dashboard")

@method_decorator(login_required, name="dispatch")
class Result(View):
    def get(self, request):
        results = ExamResult.objects.filter(student__user=request.user)

        # Calculate statistics
        if results.exists():
            total_tests = results.count()
            total_questions = sum(r.total for r in results)
            correct_answers = sum(r.got for r in results)
            avg_percentage = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0
            best_score = results.order_by('-got').first()

            # Add percentage to each result
            for result in results:
                result.percentage = round((result.got / result.total) * 100, 2) if result.total > 0 else 0
        else:
            avg_percentage = 0
            best_score = None

        return render(request, "quiz/results.html", {
            "results": results,
            "avg_percentage": avg_percentage,
            "best_score": best_score
        })


@method_decorator(login_required, name="dispatch")
class Leaderboard(View):
    def get(self, request):
        try:
            if hasattr(request.user, 'student'):
                    # Student view (same as before)
                    student = request.user.student
                    current_group = student.group
                    group_exams = MidtermExam.objects.filter(
                        group=current_group
                    ).select_related('subject').order_by('-due_date')

                    exam_results = ExamResult.objects.filter(
                        exam__group=current_group
                    ).select_related('student', 'exam')

                    context = {
                        'user_type': 'student',
                        'current_group': current_group,
                        'group_exams': group_exams,
                        'exam_results': exam_results,
                    }

            elif hasattr(request.user, 'lecturer'):
                # Lecturer view
                lecturer = request.user.lecturer
                subjects = lecturer.subjects.all()
                groups = Group.objects.filter(
                    major__in=subjects.values('major')
                ).distinct()

                selected_group_id = request.GET.get('group')
                export_format = request.GET.get('export')
                selected_group = None
                group_exams = MidtermExam.objects.none()
                exam_results = ExamResult.objects.none()

                if selected_group_id:
                    selected_group = get_object_or_404(Group, id=selected_group_id)
                    group_exams = MidtermExam.objects.filter(
                        group=selected_group,
                        subject__in=subjects
                    ).select_related('subject').order_by('-due_date')

                    exam_results = ExamResult.objects.filter(
                        exam__in=group_exams
                    ).select_related('student', 'exam')

                    # Handle export request
                    if export_format in ['word', 'excel']:
                        return self.export_results(selected_group, group_exams, exam_results, export_format)

                context = {
                    'user_type': 'lecturer',
                    'subjects': subjects,
                    'groups': groups,
                    'selected_group': selected_group,
                    'group_exams': group_exams,
                    'exam_results': exam_results,
                }

            else:
                return render(request, 'quiz/leaderboard.html', {
                    'error': "Invalid user type"
                })

            if not group_exams.exists():
                context['no_exams'] = True

            return render(request, 'quiz/leaderboard.html', context)

        except AttributeError:
            return render(request, 'quiz/leaderboard.html', {
                'error': "Profile not found"
            })

    def export_results(self, group, exams, results, format):
        if format == 'word':
            return self.export_to_word(group, exams, results)
        elif format == 'excel':
            return self.export_to_excel(group, exams, results)

    def export_to_word(self, group, exams, results):
        document = Document()

        # Add title
        document.add_heading(f'Միջանկյալ քննության արդյունքեր - խումբ {group.name} ', level=1)

        for exam in exams:
            # Add exam section
            document.add_heading(f'Առարկա - {exam.subject.name}', level=2)
            document.add_paragraph(f'Օր - {exam.due_date.strftime("%d.%m.%Y")}')

            # Create table
            table = document.add_table(rows=1, cols=3)
            table.style = 'Table Grid'

            # Add headers
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = '#'
            hdr_cells[1].text = 'Ուսանող'
            hdr_cells[2].text = 'Միավոր'

            # Add data rows
            exam_results = [r for r in results if r.exam.id == exam.id]
            for idx, result in enumerate(exam_results, start=1):
                row_cells = table.add_row().cells
                row_cells[0].text = str(idx)
                row_cells[1].text = f"{result.student.name} {result.student.last_name}"
                row_cells[2].text = str(result.score)

        # Prepare response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{group.name}_քննության_արդյունքներ.docx"'
        document.save(response)

        return response


@method_decorator(login_required, name="dispatch")
class StudentDashboard(View):
    def get(self, request):
        try:
            student = request.user.student  # More direct access
            now = timezone.now()

            # Get all exams for student's group
            exams = MidtermExam.objects.filter(
                group=student.group
            ).annotate(
                is_completed=Exists(
                    Mark.objects.filter(
                        exam=OuterRef('pk'),
                        user=request.user
                    )
                ),
                is_available=Case(
                    When(due_date__gte=now, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            ).order_by('due_date')

            return render(request, "quiz/student_dashboard.html", {
                'student': student,
                'exams': exams,
                'now': now,  # Pass current time to template
            })

        except AttributeError:  # Catches missing student profile
            messages.error(request, "Student profile not found")
            return redirect("index")


@method_decorator(login_required, name="dispatch")
class LecturerDashboard(View):
    def get(self, request):
        if not hasattr(request.user, 'lecturer'):
            return HttpResponseForbidden("Only lecturers can access this page")

        lecturer = request.user.lecturer
        now = timezone.now()

        # Get lecturer's subjects and questions
        subjects = Subject.objects.filter(lecturers=request.user)
        total_questions = TestQuestion.objects.filter(subject__in=subjects).count()

        # Get exams created by this lecturer with annotations
        created_exams = MidtermExam.objects.filter(
            created_by=request.user
        ).annotate(
            question_count=Count('questions'),
            is_active=Case(
                When(due_date__gt=now, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).select_related('subject', 'group').order_by('-due_date')

        form = MidtermExamForm(user=request.user)

        return render(request, "quiz/lecturer_dashboard.html", {
            'lecturer': lecturer,
            'subjects': subjects,
            'total_questions': total_questions,
            'created_exams': created_exams,
            'now': now,
            'form': form,
        })

# Add to views.py
@method_decorator(login_required, name="dispatch")
class ViewQuestions(View):
    def get(self, request, subject_id):
        try:
            subject = Subject.objects.get(id=subject_id)
            lecturer = request.user.lecturer

            # Verify lecturer teaches this subject
            if subject not in lecturer.subjects.all():
                messages.error(request, "Դուք չեք դասավանդում այս առարկան")
                return redirect("lecturer_dashboard")

            questions = TestQuestion.objects.filter(
                subject=subject,
                creator=request.user
            ).order_by('-id')

            return render(request, "quiz/view_questions.html", {
                'subject': subject,
                'questions': questions
            })

        except Subject.DoesNotExist:
            messages.error(request, "Առարկան չի գտնվել")
            return redirect("lecturer_dashboard")

@method_decorator(login_required, name="dispatch")
class DeleteQuestion(View):
    def post(self, request, pk):
        try:
            question = TestQuestion.objects.get(id=pk)
            if question.creator != request.user:
                messages.error(request, "Դուք կարող եք ջնջել միայն ձեր կողմից ստեղծված հարցերը")
                return redirect("lecturer_dashboard")

            question.delete()
            messages.success(request, "Հարցը հաջողությամբ ջնջվել է ")
            return redirect("view_questions", subject_id=question.subject.id)

        except TestQuestion.DoesNotExist:
            messages.error(request, "Հարցը չի գտնվել")
            return redirect("lecturer_dashboard")


@method_decorator(login_required, name="dispatch")
class AddSubject(View):
    def get(self, request):
        form = SubjectForm()
        return render(request, "quiz/add_subject.html", {'form': form})

    def post(self, request):
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            subject.lecturers.add(request.user)

            # Also add to Lecturer model if exists
            lecturer, created = Lecturer.objects.get_or_create(user=request.user)
            lecturer.subjects.add(subject)

            messages.success(request, "Առարկան հաջողությամբ ավելացվել է")
            return redirect('lecturer_dashboard')
        return render(request, "quiz/add_subject.html", {'form': form})


@method_decorator(login_required, name="dispatch")
class SelectQuestionCount(View):
    def get(self, request):
        if not hasattr(request.user, 'lecturer'):
            messages.error(request, "Only lecturers can add questions")
            return redirect("index")

        lecturer = request.user.lecturer
        return render(request, "quiz/select_question_count.html", {
            "lecturer": lecturer,
            "subjects": lecturer.subjects.all()
        })

    def post(self, request):
        if not hasattr(request.user, 'lecturer'):
            messages.error(request, "Only lecturers can add questions")
            return redirect("index")

        question_count = request.POST.get("question_count")
        subject_id = request.POST.get("subject")

        if not question_count or not subject_id:
            messages.error(request, "Please select both subject and question count")
            return redirect("select_question_count")

        try:
            question_count = int(question_count)
            if question_count < 1 or question_count > 50:
                messages.error(request, "Please enter a number between 1 and 50")
                return redirect("select_question_count")
        except ValueError:
            messages.error(request, "Please enter a valid number")
            return redirect("select_question_count")

        return redirect(f"{reverse('add_question')}?count={question_count}&subject={subject_id}")

# API Views


def api_questions_list(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'lecturer'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    subject_id = request.GET.get('subject')
    try:
        subject = Subject.objects.get(id=subject_id)
        if subject not in request.user.lecturer.subjects.all():
            return JsonResponse({'error': 'Forbidden'}, status=403)

        questions = TestQuestion.objects.filter(
            subject=subject,
            creator=request.user
        ).values('id', 'question', 'option1', 'option2',
                 'option3', 'option4', 'correct_option',
                 'verified', 'image')

        return JsonResponse({'questions': list(questions)})

    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Առարկան չի գտնվել'}, status=404)

def api_question_detail(request, pk):
    if not request.user.is_authenticated or not hasattr(request.user, 'lecturer'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        question = TestQuestion.objects.get(id=pk)
        if question.creator != request.user:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        data = {
            'id': question.id,
            'text': question.question,
            'option1': question.option1,
            'option2': question.option2,
            'option3': question.option3,
            'option4': question.option4,
            'correct_option': question.correct_option,
            'score': question.score,
            'image': question.image.url if question.image else None
        }
        return JsonResponse(data)

    except TestQuestion.DoesNotExist:
        return JsonResponse({'error': 'Հարցը չի գտնվել'}, status=404)

def get_groups_for_subject(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'lecturer'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    subject_id = request.GET.get('subject')
    try:
        subject = Subject.objects.get(id=subject_id)
        # Verify the lecturer teaches this subject
        if subject not in request.user.lecturer.subjects.all():
            return JsonResponse({'error': 'Forbidden'}, status=403)

        groups = Group.objects.filter(major=subject.major)
        data = {
            'groups': [{'id': group.id, 'name': group.name} for group in groups]
        }
        return JsonResponse(data)
    except Subject.DoesNotExist:
        return JsonResponse({'groups': []}, status=404)


@login_required
def create_exam(request):
    if request.method == 'POST':
        form = MidtermExamForm(request.POST, user=request.user)  # Pass user to form
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            form.save_m2m()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Exam created successfully',
                    'exam_id': exam.id
                })
            return redirect('lecturer_dashboard')

        # Handle form errors
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        messages.error(request, "Please correct the errors below")
    else:
        form = MidtermExamForm(user=request.user)

    return render(request, 'quiz/exam_form.html', {'form': form})


@login_required
def results(request):
    if not hasattr(request.user, 'student'):
        return HttpResponseForbidden("You don't have permission to view this page")

    exam_id = request.GET.get('exam_id')

    if exam_id:
        # Show specific exam results
        try:
            exam = MidtermExam.objects.get(id=exam_id)
            result = ExamResult.objects.get(exam=exam, student=request.user.student)
            return redirect('result_detail', result_id=result.id)
        except (MidtermExam.DoesNotExist, ExamResult.DoesNotExist):
            messages.error(request, "Results not found for this exam")
            return redirect('student_dashboard')

    # Show all results
    student = request.user.student
    marks = Mark.objects.filter(user=request.user).select_related('exam')
    exam_results = ExamResult.objects.filter(student=student).select_related('exam')

    # Calculate statistics
    total_tests = marks.count()
    avg_percentage = marks.aggregate(
        avg=models.Avg('got', output_field=models.FloatField()) * 100 / models.F('total')
    )['avg']
    best_score = marks.order_by('-got').first()

    context = {
        'results': marks,
        'total_tests': total_tests,
        'avg_percentage': avg_percentage or 0,
        'best_score': best_score,
    }
    return render(request, 'quiz/results.html', context)


@login_required
def result_detail(request, result_id):
    # Get the result with all related data
    result = get_object_or_404(
        ExamResult.objects.select_related('exam', 'student')
                         .prefetch_related('answers__question'),
        id=result_id,
        student__user=request.user
    )

    # Calculate actual points earned (sum of scores for correct answers)
    points_earned = sum(
        answer.question.score
        for answer in result.answers.all()
        if answer.is_correct
    )

    # Calculate total possible points
    total_possible_points = sum(
        answer.question.score
        for answer in result.answers.all()
    )

    # Prepare questions data
    questions = []
    for answer in result.answers.all():
        questions.append({
            'question': answer.question,
            'student_answer': answer.answer,
            'correct_answer': answer.question.correct_option,
            'is_correct': answer.is_correct,
            'score': answer.question.score,
            'options': {
                'A': answer.question.option1,
                'B': answer.question.option2,
                'C': answer.question.option3,
                'D': answer.question.option4,
            }
        })

    context = {
        'result': result,
        'exam': result.exam,
        'questions': questions,
        'correct_answers_count': result.score,  # Number of correct answers
        'total_questions': result.total_questions,  # Total number of questions
        'points_earned': points_earned,  # Total points earned
        'total_possible_points': total_possible_points,  # Max possible points
        'percentage': round((points_earned / total_possible_points) * 100, 2) if total_possible_points > 0 else 0,
    }
    return render(request, "quiz/result_detail.html", context)


# views.py - Example of how to save exam results
def submit_exam(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(MidtermExam, id=exam_id)
        student = request.user.student

        # Calculate score
        score = 0
        student_answers = []

        for question in exam.questions.all():
            answer_key = f'question_{question.id}'
            student_answer = request.POST.get(answer_key)

            if student_answer == question.correct_option:
                score += question.score
                is_correct = True
            else:
                is_correct = False

            student_answer_obj = StudentAnswer.objects.create(
                question=question,
                answer=student_answer,
                is_correct=is_correct
            )
            student_answers.append(student_answer_obj)

        # Create exam result
        exam_result = ExamResult.objects.create(
            exam=exam,
            student=student,
            score=score
        )
        exam_result.answers.set(student_answers)

        # Create mark
        mark = Mark.objects.create(
            total=exam.questions.count(),
            got=score,
            user=request.user,
            exam=exam
        )

        return redirect('results')

def exam_detail_view(request, exam_id):
    exam = get_object_or_404(MidtermExam, id=exam_id)
    return render(request, 'exams/exam_detail.html', {'exam': exam})