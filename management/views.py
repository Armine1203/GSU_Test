from django.shortcuts import redirect, render
from django.urls import reverse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from os.path import join
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from quiz.models import Question, Mark
from account.models import User


def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_admin(),
        login_url='/account/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

@method_decorator(admin_required(), name="dispatch")
class Manage(View):
    def get(self, request):
        panel_options = {
            "Ավելացնել հարցեր": {
                "link": reverse("upload_question"),
                "btntxt": "Բեռնել"
            },
            "Ստուգել հարցերը": {
                "link": reverse("verify_question"),
                "btntxt": "Ստուգել"
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

@method_decorator(admin_required(), name="dispatch")
class Results(View):
    def get(self, request):
        return render(request, "management/results.html", {"results": Mark.objects.all()})

@method_decorator(admin_required(), name="dispatch")
class UploadQuestion(View):
    def get(self, request):
        return render(request, "management/upload_question.html")

    def post(self, request):
        qFile = request.FILES["qFile"]
        filepath = join(settings.BASE_DIR, "upload", "questions.csv")
        if not str(qFile).endswith(".csv"):
            messages.warning(request, "Only CSV file allowed")
        else:
            with open(filepath, "wb") as f:
                for chunk in qFile.chunks():
                    f.write(chunk)
            messages.success(request, "CSV file uploaded")
        return redirect("manage")

@method_decorator(admin_required(), name="dispatch")
class VerifyQuestion(View):
    def get(self, request):
        qs = Question.objects.filter(verified=False)
        return render(request, "management/verify_question.html", {"questions": qs})

    def post(self, request):
        count = 0
        for q, v in request.POST.items():
            if q.startswith("q") and v == "on":
                id = q[1:]
                q = Question.objects.filter(id=id).first()
                if q is not None:
                    q.verified = True
                    q.save()
                    count += 1
                else:
                    messages.warning(request, f"No question exists with id {id}")
        messages.success(request, f"{count} questions added")
        return redirect("manage")

@method_decorator(admin_required(), name="dispatch")
class Setting(View):
    def get(self, request):
        info = {
            "question_limit": settings.GLOBAL_SETTINGS["questions"]
        }
        return render(request, "management/setting.html", {"info": info})

    def post(self, request):
        qlimit = int(request.POST.get("qlimit", 10))
        if qlimit > 0:
            settings.GLOBAL_SETTINGS["questions"] = qlimit
            messages.success(request, "Դուք հաջողությամբ պահպանել եք կարգավորումները")
        else:
            messages.warning(request, "Question limit can't be 0 or less than 0")
        return redirect("setting")
