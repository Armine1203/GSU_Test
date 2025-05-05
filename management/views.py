import csv

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from quiz.models import Mark, TestQuestion, Subject
from os.path import join

# Create your views here.
@method_decorator(staff_member_required, name="dispatch")
class Manage(View):
    def get(self, request):
        panel_options = {
            "Ավելացնել հարցեր": {
                "link": reverse("upload_question"),
                "btntxt": "Բեռնել"
            },
            "Ստանալ արդյունքները": {
                "link": reverse("results"),
                "btntxt": "Ստանալ"
            }
        }
        return render(
            request,
            "management/manage.html",
            {"panel_options": panel_options}
        )

# @method_decorator(staff_member_required, name="dispatch")
# class Results(View):
#     def get(self, request):
#         return render(request, "quiz/results.html", {"results": Mark.objects.all()})

class UploadQuestion(View):
    def get(self, request):
        if request.user.is_staff:
            subjects = Subject.objects.all()
        elif hasattr(request.user, 'lecturer'):
            subjects = request.user.lecturer.subjects.all()
        else:
            messages.error(request, "You don't have permission to upload questions")
            return redirect("index")

        return render(request, "management/upload_question.html", {
            'subjects': subjects
        })

    def post(self, request):
        q_file = request.FILES.get("qFile")
        subject_id = request.POST.get("subject")

        # Validate file
        if not q_file or not str(q_file).endswith(".csv"):
            messages.warning(request, "Please upload a valid CSV file")
            return redirect("upload_question")

        # Validate subject selection
        if not subject_id:
            messages.warning(request, "Please select a subject")
            return redirect("upload_question")

        try:
            subject = Subject.objects.get(id=subject_id)

            # Verify permission
            if not request.user.is_staff:
                if not hasattr(request.user, 'lecturer'):
                    messages.error(request, "Only lecturers can upload questions")
                    return redirect("index")
                if not subject.lecturers.filter(id=request.user.id).exists():
                    messages.error(request, "You don't teach this subject")
                    return redirect("upload_question")

            # Process CSV
            decoded_file = q_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            created_count = 0
            error_rows = []

            for i, row in enumerate(reader, start=2):  # start=2 for 1-based row numbering
                try:
                    TestQuestion.objects.create(
                        subject=subject,
                        question=row['question'],
                        option1=row['option1'],
                        option2=row['option2'],
                        option3=row['option3'],
                        option4=row['option4'],
                        correct_option=row['correct_option'].upper(),
                        score=int(row.get('score', 1)),
                        creator=request.user
                    )
                    created_count += 1
                except Exception as e:
                    error_rows.append(f"Row {i}: {str(e)}")
                    continue

            if created_count:
                messages.success(request, f"Successfully uploaded {created_count} questions")
            if error_rows:
                messages.warning(request, f"Errors in {len(error_rows)} rows")
                for error in error_rows[:3]:  # Show first 3 errors
                    messages.info(request, error)

        except Subject.DoesNotExist:
            messages.error(request, "Selected subject doesn't exist")
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")

        return redirect("upload_question")

@method_decorator(staff_member_required, name="dispatch")
class DownloadQuestionTemplate(View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="question_template.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'question',
            'option1',
            'option2',
            'option3',
            'option4',
            'correct_option',
            'score'
        ])

        # Add example row
        writer.writerow([
            'Ո՞րն է մայրաքաղաքը...',
            'Երևան',
            'Մոսկվա',
            'Տոկիո',
            'Պարիզ',
            'A',
            '1'
        ])

        return response