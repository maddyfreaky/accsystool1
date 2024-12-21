from django.contrib.auth import login as auth_login, authenticate ,logout as auth_logout # Import login and rename it to auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
import random
import string
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.urls import reverse

@login_required
def members(request):
    if request.user.is_authenticated:
        username = request.user.username
        return render(request, 'all_leads.html', {'username': username})
    else:
        return redirect('login')


def user_logout(request):
   if request.method == 'POST':  # Only allow logout on POST request
        auth_logout(request)
        return redirect('login')  # Redirect to login after logout
   return redirect('members')  # If not logged out, redirect to members

# def member_login(request):
#     return render(request,"login.html")

def forms(request):
    return render(request,"forms.html")

def table(request):
    return render(request,"table.html")

# def register(request):
#     print("reg")
#     return render(request,"register.html")

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['cpassword']

        if password != password2:
            return HttpResponse("Passwords do not match")
        
        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already taken")
        
        if User.objects.filter(email=email).exists():
            return HttpResponse("Email already in use")

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        user.save()

        # Log in the user and then redirect to another page
        auth_login(request, user)  # Renamed login to auth_login to avoid confusion
        return redirect('login')  # Redirect to home page or another success page

    return render(request, 'register.html')

def user_login(request):
    # Check if the user is already authenticated
    if request.user.is_authenticated:
        return redirect('members')  # Redirect to members page if user is logged in

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Check if a user with the entered email exists
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return an error response if email does not exist
            return JsonResponse({'status': 'error', 'message': 'No User Found'})

        # Authenticate using the username linked to the email
        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            # If authentication is successful
            auth_login(request, user)
            request.session['login_success'] = True
            return JsonResponse({'status': 'success', 'redirect_url': reverse('todlistpage')})
        else:
            # Return an error response if the password is incorrect
            return JsonResponse({'status': 'error', 'message': 'Invalid login credentials'})
    
    return render(request, 'login.html')


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp(email, otp):
    subject = "Password Reset OTP"
    message = f"Your OTP for password reset is: {otp}"
    send_mail(subject, message, 'your-email@example.com', [email])

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Get email from input form
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No user is associated with this email.")
            return redirect('forgot_password')

        # Generate OTP and save it in session
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['email'] = email

        # Send OTP to user's email
        send_otp(email, otp)
        messages.success(request, 'An OTP has been sent to your email.')
        return redirect('verify_otp')

    return render(request, 'forgot_password.html')

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')  # Get OTP from input form
        if entered_otp == request.session.get('otp'):
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify_otp')

    return render(request, 'verify_otp.html')

def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            email = request.session.get('email')
            user = User.objects.get(email=email)
            user.password = make_password(new_password)
            user.save()

            # Clear OTP from session after password reset
            request.session.pop('otp', None)
            request.session.pop('email', None)

            messages.success(request, 'Password reset successfully. Please login.')
            return redirect('userlogin')  # Redirect to login page
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password')

    return render(request, 'reset_password.html')

def maintenance(request):
    return render(request, 'maintenance.html')

