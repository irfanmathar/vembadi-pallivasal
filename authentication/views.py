from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from .models import *

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import user, OTP
from .utils import generate_otp
from .otp_service import send_email_otp, send_phone_otp

# --------------------------
# Signup Page
# --------------------------
def signuppage(request):
    context = {"error": ""}
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST['username']
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        password = request.POST['password']

        # Check duplicates
        if User.objects.filter(username=username).exists():
            context['error'] = "Username already exists"
            return render(request, 'signup.html', context)
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            context['error'] = "Phone number already exists"
            return render(request, 'signup.html', context)
        if email and User.objects.filter(email=email).exists():
            context['error'] = "Email already registered"
            return render(request, 'signup.html', context)

        # Save user temporarily in session for OTP verification
        request.session['signup_data'] = {
            "full_name": full_name,
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "password": password
        }

        # Generate OTP
        otp_code = generate_otp()
        request.session['signup_otp'] = otp_code

        # Send OTP
        if email:
            send_email_otp(email, otp_code)
        if phone_number:
            send_phone_otp(phone_number, otp_code)

        return redirect('verify_signup_otp')

    return render(request, 'signup.html', context)


# --------------------------
# Verify Signup OTP
# --------------------------
def verify_signup_otp(request):
    context = {"error": ""}
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("signup_otp")
        signup_data = request.session.get("signup_data")

        if not session_otp or not signup_data:
            context["error"] = "Session expired. Try again."
            return redirect('signuppage')

        if entered_otp != session_otp:
            context["error"] = "Invalid OTP"
            return render(request, "verify_signup_otp.html", context)

        # Create user
        new_user = User.objects.create_user(
            username=signup_data['username'],
            email=signup_data['email'],
            password=signup_data['password']
        )
        new_user.full_name = signup_data['full_name']
        new_user.phone_number = signup_data['phone_number']
        new_user.save()

        # Clear session
        request.session.pop('signup_data')
        request.session.pop('signup_otp')

        messages.success(request, "Signup successful. You can now login.")
        return redirect('/inventory/dash/')

    return render(request, "verify_signup_otp.html", context)


# --------------------------
# Login Page (password)
# --------------------------
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from .models import user
from .utils import generate_otp
from .otp_service import send_email_otp, send_phone_otp

# --------------------------
# Step 1: Login with username/password
# --------------------------
def loginpage(request):
    if request.user.is_authenticated:
        return redirect('/inventory/dash/')
    
    context = {"error": ""}
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user_obj = authenticate(username=username, password=password)
        if user_obj:
            # Password is correct → generate OTP
            otp_code = generate_otp()
            request.session['login_otp'] = otp_code
            request.session['login_user_id'] = user_obj.id
            
            # Send OTP
            if user_obj.email:
                send_email_otp(user_obj.email, otp_code)
            if user_obj.phone_number:
                send_phone_otp(user_obj.phone_number, otp_code)
            
            messages.success(request, "OTP sent to your email/phone.")
            return redirect('verify_login_otp')
        else:
            context["error"] = "Invalid username or password"
    
    return render(request, "login.html", context)


# --------------------------
# Step 2: Verify OTP
# --------------------------
def verify_login_otp(request):
    context = {"error": ""}
    
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("login_otp")
        user_id = request.session.get("login_user_id")
        
        if not session_otp or not user_id:
            context["error"] = "Session expired. Please login again."
            return redirect("loginpage")
        
        if entered_otp != session_otp:
            context["error"] = "Invalid OTP"
            return render(request, "verify_login_otp.html", context)
        
        # OTP is correct → login the user
        user_obj = User.objects.get(id=user_id)
        auth_login(request, user_obj)
        
        # Clear session
        request.session.pop("login_otp")
        request.session.pop("login_user_id")
        
        return redirect("/inventory/dash/")
    
    return render(request, "verify_login_otp.html", context)


# --------------------------
# Logout
# --------------------------
def logoutpage(request):
    auth_logout(request)
    return redirect("/")

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
# Temporary storage for OTPs (you can use DB model for production)
otp_storage = {}

# -------------------------------
# Step 1: Forgot Password (Send OTP)
# -------------------------------
otp_storage = {}
User = get_user_model()
def forgot_password(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # email or phone

        try:
            if "@" in identifier:  # Treat as email
                user = User.objects.get(email=identifier)
                otp = random.randint(100000, 999999)
                request.session['reset_otp'] = str(otp)
                request.session['reset_user'] = user.username

                # Send OTP via email
                send_mail(
                    subject="Password Reset OTP",
                    message=f"Your OTP is {otp}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, f"OTP sent to email {identifier}")

            else:  # Treat as phone number
                user = User.objects.get(phone_number=identifier)
                otp = random.randint(100000, 999999)
                request.session['reset_otp'] = str(otp)
                request.session['reset_user'] = user.username

                # For testing, print OTP (replace with SMS API)
                print(f"OTP for {identifier} is {otp}")
                messages.success(request, f"OTP sent to phone {identifier}")

            return redirect("reset_password")

        except User.DoesNotExist:
            messages.error(request, "User with this email/phone not found.")
            return render(request, "forgot_password.html")

    return render(request, "forgot_password.html")
# -------------------------------
# Step 2: Reset Password using OTP
# -------------------------------
def reset_password(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        session_otp = request.session.get('reset_otp')
        username = request.session.get('reset_user')

        if not session_otp or not username:
            messages.error(request, "Session expired. Try again.")
            return redirect("forgot_password")

        if otp_input != session_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, "reset_password.html")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")

        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()

            # Clear session
            request.session.pop('reset_otp')
            request.session.pop('reset_user')

            messages.success(request, "Password reset successfully. You can now login.")
            return redirect("login")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("forgot_password")

    return render(request, "reset_password.html")
