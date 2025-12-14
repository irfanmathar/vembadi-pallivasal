from django.urls import path
from .views import *

urlpatterns = [
    path('',loginpage,name='loginpage'),
    path('signup/',signuppage, name='signuppage'),
    path('logout/',logoutpage, name='logoutpage'),
    path('verify-signup-otp/', verify_signup_otp, name='verify_signup_otp'),
    
    path('verify-login-otp/', verify_login_otp, name='verify_login_otp'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/', reset_password, name='reset_password'),
]
