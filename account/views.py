# from django.contrib.auth.models import User
# from django.shortcuts import redirect, render
# from django.views import View
# from django.contrib.auth import login, logout, authenticate
# from django.contrib import messages
# from .models import User #new added
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
#
# class Login(View):
#     def get(self, request):
#         if request.user.is_authenticated:
#                 # messages.info(request, "You are already login. Logout first")
#             return redirect("index")
#         return render(request, "account/login.html")
#
#     def post(self, request):
#         uname = request.POST.get("username")
#         passwd = request.POST.get("password")
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             messages.success(request, "Դուք հաջողությամբ մուտք եք գործել")
#             return redirect("index")
#         # else:
#         #         messages.warning(request, "Անունը կամ գաղտնաբառը սխալ են։")
#         # return render(request, "account/login.html")
#         #neq
#         messages.error(request, 'Invalid credentials')
#         return render(request, 'account/login.html')
#
#
# # @method_decorator(login_required, name="dispatch")
# # class Logout(View):
# #     def get(self, request):
# #         logout(request)
# #         return redirect("login")
#
# class Register(View):
#     def get(self, request):
#         if request.user.is_authenticated:
#          # messages.info(request, "You are already logged in")
#         #     return redirect("index")
#         # return render(request, "account/register.html")
#         #
#             return redirect('index')
#             return render(request, 'account/register.html')
#
#
#     def post(self, request):
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         # user = User.objects.filter(username=username).first()
#         # if user is None:
#         #     user = User(username=username)
#         #     user.set_password(password)
#         #     user.save()
#         #     login(request, user)
#         #     messages.success(request, "User created")
#         #     return redirect("index")
#         # else:
#         #     messages.info(request, "User already exists.")
#         #     return redirect("register")
#         if User.objects.filter(username=username).exists():
#             messages.error(request, 'Username already exists')
#             return redirect('register')
#
#         user = User.objects.create_user(username=username, password=password)
#         login(request, user)
#         messages.success(request, 'Account created successfully')
#         return redirect('index')
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import User


class Login(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        return render(request, 'account/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful')
            return redirect('index')
        messages.error(request, 'Invalid credentials')
        return render(request, 'account/login.html')


class Register(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')
        return render(request, 'account/register.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get("user_type", 1)

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        user = User.objects.create_user(username=username, password=password, user_type=user_type)
        login(request, user)
        messages.success(request, 'Account created successfully')
        return redirect('index')