import json

from django.db import models
from django.db.models import Prefetch, Avg, Count, F, Sum, Exists, OuterRef, When, Case, BooleanField
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from .forms import SubjectForm, MidtermExamForm
from .models import TestQuestion, Mark, Lecturer, Student, MidtermExam, Subject, Group, StudentAnswer
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden


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
        # Get all marks with related user data
        marks = Mark.objects.select_related('user').all()

        # Annotate each user with their average percentage
        leaderboard_data = (
            marks.values('user__id', 'user__username', 'user__first_name', 'user__last_name')
            .annotate(
                average_percentage=Avg(F('got') * 100.0 / F('total')),
                total_tests=Count('id'),
                total_score=Sum('got'),
                max_score=Sum('total')
            )
            .order_by('-average_percentage')
        )

        context = {
            'leaderboard': leaderboard_data,
        }
        return render(request, 'leaderboard.html', context)
# In quiz/views.py

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
            messages.error(request, "Միայն դասախոսները թույլտվություն ունեն այս էջ մուտք գործելու")
            return redirect("index")

        lecturer = request.user.lecturer
        subjects = Subject.objects.filter(lecturers=request.user)

        # Calculate statistics
        total_questions = TestQuestion.objects.filter(subject__in=subjects).count()

        form = MidtermExamForm(user=request.user)

        return render(request, "quiz/lecturer_dashboard.html", {
            'lecturer': lecturer,
            'subjects': subjects,
            'total_questions': total_questions,
            'verified_questions': total_questions,
            'pending_questions': 0,
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
    print("Woking Create Exam")
    if request.method == 'POST':
        form = MidtermExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            form.save_m2m()
            return redirect('lecturer_dashboard')
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])


# views.py
from django.shortcuts import render, get_object_or_404
from .models import ExamResult, Mark, MidtermExam

@login_required
def results(request):
    if not hasattr(request.user, 'student'):
        return HttpResponseForbidden("You don't have permission to view this page")
    student = request.user.student
    marks = Mark.objects.filter(user=request.user).select_related('exam')
    exam_results = ExamResult.objects.filter(student=student).select_related('exam')

    # Calculate statistics
    total_tests = marks.count()
    avg_percentage = marks.aggregate(avg=models.Avg('got', output_field=models.FloatField()) * 100 / models.F('total'))[
        'avg']
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
    result = get_object_or_404(ExamResult, id=result_id)
    answers = result.answers.all()

    try:
        exam_result = ExamResult.objects.get(
            exam=result.exam,
            student=request.user.student
        )

        questions = []
        for answer in exam_result.answers.all().select_related('question'):
            questions.append({
                'question': answer.question,
                'student_answer': answer.answer,
                'correct_answer': answer.question.correct_option,
                'is_correct': answer.is_correct,
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
            'percentage': exam_result.percentage,
            'exam_result': exam_result,
        }
        return render(request, "quiz/result_detail.html", context)
    # {'result': result, 'answers': answers}
    except ExamResult.DoesNotExist:
        messages.error(request, "Detailed results not available")
        return redirect('results')


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
