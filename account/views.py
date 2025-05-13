from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

User = get_user_model()


class Login(View):
    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, "You are already login. Logout first")
            return redirect("index")
        return render(request, "account/login.html")

    def post(self, request):
        uname = request.POST.get("username", "")
        passwd = request.POST.get("password", "")
        user = authenticate(username=uname, password=passwd)
        if user is not None:
            login(request, user)
            messages.success(request, "Դուք հաջողությամբ մուտք եք գործել")

            # Redirect based on user type
            # Redirect based on user type
            if user.is_superuser or user.is_staff:
                return redirect("index")
            elif hasattr(user, 'user_type'):
                if user.user_type == 2:  # Lecturer
                    return redirect("lecturer_dashboard")
                elif user.user_type == 3:  # Student
                    return redirect("student_dashboard")

            # Default redirect for other users
            return redirect("index")
        else:
            messages.warning(request, "Invalid username or password")
        return render(request, "account/login.html")


@method_decorator(login_required, name="dispatch")
class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("login")


class Register(View):
    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in")
            return redirect("index")
        return render(request, "account/register.html")

    def post(self, request):
        uname = request.POST.get("username", "")
        passwd = request.POST.get("password", "")
        user = User.objects.filter(username=uname).first()
        if user is None:
            user = User(username=uname)
            user.set_password(passwd)
            user.save()
            login(request, user)
            messages.success(request, "User created")
            return redirect("index")
        else:
            messages.info(request, "User already exists.")
            return redirect("register")
