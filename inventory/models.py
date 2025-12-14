from django.db import models


class Members(models.Model):
    

    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    serial_no=models.IntegerField(default=0)
    book_number = models.CharField(max_length=15)
    address=models.CharField(max_length=500)
    photo=models.ImageField(null=True,upload_to='images/')
    
    
    year = models.DateField(null=True)
    
    def __str__(self):
        return self.name

class Payment(models.Model):
    member = models.ForeignKey(Members, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.member.name} - {self.amount}"

class CommitteeMember(models.Model):
    name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)   # NEW
    role = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='committee_photos/')
    posting_start_date = models.DateField()  
    phone_number = models.CharField(max_length=20)
# NEW

    def __str__(self):
        return self.name

class Notice(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]
    
class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    photo = models.ImageField(upload_to='event_photos/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

