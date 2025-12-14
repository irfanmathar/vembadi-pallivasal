from django.core.mail import send_mail

def send_email_otp(email, otp):
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP is {otp}",
        from_email="noreply@yourdomain.com",
        recipient_list=[email],
        fail_silently=False,
    )

def send_phone_otp(phone, otp):
    # For now print (later integrate SMS API)
    print(f"OTP for {phone}: {otp}")
