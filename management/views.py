import csv
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from quiz.models import TestQuestion, Subject
import chardet  # For encoding detection


class UploadQuestion(View):
    def get(self, request):
        if request.user.is_staff:
            subjects = Subject.objects.all()
        elif hasattr(request.user, 'lecturer'):
            subjects = request.user.lecturer.subjects.all()
        else:
            messages.error(request, "Դուք չունեք հարցեր բեռնելու թույլտվություն")
            return redirect("index")

        return render(request, "management/upload_question.html", {
            'subjects': subjects
        })

    def post(self, request):
        q_file = request.FILES.get("qFile")
        subject_id = request.POST.get("subject")

        # Validate file
        if not q_file or not str(q_file).endswith(".csv"):
            messages.warning(request, "Խնդրում ենք ներբեռնել ճիշտ CSV ֆայլ")
            return redirect("upload_question")

        # Validate subject selection
        if not subject_id:
            messages.warning(request, "Խնդրում ենք ընտրել առարկան")
            return redirect("upload_question")

        try:
            subject = Subject.objects.get(id=subject_id)

            # Verify permission
            if not request.user.is_staff:
                if not hasattr(request.user, 'lecturer'):
                    messages.error(request, "Միայն դասախոսները կարող են բեռնել հարցեր")
                    return redirect("index")
                if not subject.lecturers.filter(id=request.user.id).exists():
                    messages.error(request, "Դուք չեք դասավանդում այս առարկան")
                    return redirect("upload_question")

            # Process CSV with proper encoding handling
            file_content = q_file.read()

            # Try to detect encoding
            detected = chardet.detect(file_content)
            encodings_to_try = [
                detected['encoding'],  # Try detected encoding first
                'utf-8-sig',  # UTF-8 with BOM
                'utf-8',  # Standard UTF-8
                'utf-16',  # UTF-16
                'windows-1252',  # Common Windows encoding
                'iso-8859-1'  # Latin-1
            ]

            decoded_file = None
            for encoding in encodings_to_try:
                if not encoding:
                    continue
                try:
                    decoded_file = file_content.decode(encoding).splitlines()
                    break
                except (UnicodeDecodeError, LookupError):
                    continue

            if not decoded_file:
                messages.error(request, "Չհաջողվեց վերծանել ֆայլի կոդավորումը: Խնդրում ենք օգտագործել UTF-8 կոդավորում")
                return redirect("upload_question")

            reader = csv.DictReader(decoded_file)

            created_count = 0
            error_rows = []

            for i, row in enumerate(reader, start=2):
                try:
                    # Ensure all text fields are properly encoded
                    question = TestQuestion(
                        subject=subject,
                        question=row['Հարց'],
                        option1=row['Տարբերակ 1'],
                        option2=row['Տարբերակ 2'],
                        option3=row['Տարբերակ 3'],
                        option4=row['Տարբերակ 4'],
                        correct_option=row['Ճիշտ պատասխան'].upper(),
                        score=int(row.get('Միավոր', 1)),
                        creator=request.user
                    )
                    question.save()
                    created_count += 1
                except Exception as e:
                    error_rows.append(f"Տող {i}: {str(e)}")
                    continue

            if created_count:
                messages.success(request, f"Հաջողությամբ բեռնվեց {created_count} հարց")
            if error_rows:
                messages.warning(request, f"Սխալներ {len(error_rows)} տողերում")
                for error in error_rows[:3]:  # Show first 3 errors only
                    messages.info(request, error)

        except Subject.DoesNotExist:
            messages.error(request, "Ընտրված առարկան գոյություն չունի")
        except Exception as e:
            messages.error(request, f"Ֆայլի մշակման սխալ: {str(e)}")

        return redirect("upload_question")

@method_decorator(staff_member_required, name="dispatch")
class DownloadQuestionTemplate(View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="Հարցի_օրինակ.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Հարց',
            'Տարբերակ 1',
            'Տարբերակ 2',
            'Տարբերակ 3',
            'Տարբերակ 4',
            'Ճիշտ պատասխան',
            'Միավոր'
        ])

        # Add example row with Armenian characters
        writer.writerow([
            'Ո՞րն է Հայաստանի մայրաքաղաքը',
            'Երևան',
            'Մոսկվա',
            'Տոկիո',
            'Պարիզ',
            'A',
            '1'
        ])

        return response