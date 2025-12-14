from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from django.conf import settings
class user(AbstractUser):
    age=models.IntegerField(default=0)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
class OTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # ✅ CORRECT
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"