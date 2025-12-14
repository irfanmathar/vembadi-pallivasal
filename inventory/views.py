from django.shortcuts import render,redirect
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse, FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from .models import *
import os
import qrcode
from reportlab.lib import colors
from django.conf import settings
from django.shortcuts import get_object_or_404
from reportlab import rl_config
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import tempfile
from .models import Members, Payment
from reportlab.lib.units import inch
from django.http import FileResponse
import io
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.http import HttpResponseForbidden
from authentication.models import *
def get_static_file(filepath):
    # First check STATIC_ROOT (production)
    if getattr(settings, 'STATIC_ROOT', None):
        full_path = os.path.join(settings.STATIC_ROOT, filepath)
        if os.path.exists(full_path):
            return full_path

    # Development mode (STATICFILES_DIRS)
    if hasattr(settings, 'STATICFILES_DIRS'):
        for folder in settings.STATICFILES_DIRS:
            full_path = os.path.join(folder, filepath)
            if os.path.exists(full_path):
                return full_path

    return None


@login_required(login_url='/')
def member(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    
    if request.method=='POST':
        print(request.POST,request.FILES)
        photo = request.FILES.get('photo')
        addmember=Members(name=request.POST['name'],father_name=request.POST['fname'],family_name=request.POST['fname2'],
                          phone_number=request.POST['phno'],serial_no=request.POST['serial'],
                          book_number=request.POST['book'],year=request.POST['year'],address=request.POST['address'],photo=photo)
        
        addmember.save()
        messages.success(request, "Member details submitted successfully!")
    return render(request,'index.html')

@login_required(login_url='/')
def allmember(request):
    name = request.GET.get('name', '')
    father = request.GET.get('father', '')
    family = request.GET.get('family', '')

    members = Members.objects.all()

    if name:
        members = members.filter(name__icontains=name)

    if father:
        members = members.filter(father_name__icontains=father)
        
    if family:
        members = members.filter(family_name__icontains=family)
    total =members.count()
    for member in members:
        last_payment = Payment.objects.filter(member=member).order_by('-date').first()
        member.last_date = last_payment.date if last_payment else None
        member.last_amount = last_payment.amount if last_payment else None
    return render(request, 'allmembers.html', {'allmember': members,"total": total})


@login_required(login_url='/')
def update_member(request, id):
    member = Members.objects.get(id=id)

    if request.method == "POST":
        member.name = request.POST['name']
        member.father_name = request.POST['father_name']
        member.family_name = request.POST['family_name']
        member.phone_number = request.POST['phone_number']
        member.serial_no = request.POST['serial_no']
        member.book_number = request.POST['book_number']
        member.year = request.POST['year']
        member.address = request.POST['address']

        if 'photo' in request.FILES:
            member.photo = request.FILES['photo']

        member.save()
        messages.success(request, "Member details updated successfully!")
        return redirect('/inventory/allmember/')  # your list page name

    return render(request, 'editmember.html', {'member': member})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from .models import Members, Payment




import urllib.parse
@login_required(login_url='/')
def add_payment(request, member_id):
    member = get_object_or_404(Members, id=member_id)
    success = False
    whatsapp_url = None

    if request.method == "POST":
        amount = request.POST.get("amount")
        reason = request.POST.get("reason")

        if amount and reason:
            # Create payment and automatically save system date
            payment = Payment.objects.create(
                member=member,
                amount=amount,
                reason=reason
            )
            success = True

            # Format date from model
            payment_date = payment.date.strftime("%d/%m/%Y")

            # WhatsApp message in proper Tamil
            message = f"அஸ்ஸலாமு அலைக்கும் {member.name}, நீங்கள் இன்று {payment_date} நீங்கள் ரூ.{amount} {reason} கொடுத்தீர்கள். "
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/91{member.phone_number}?text={encoded_message}"

    return render(request, "add_payment.html", {
        "member": member,
        "success": success,
        "whatsapp_url": whatsapp_url,
    })
    
@login_required(login_url='/')
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == "POST":
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
        return redirect('view_payments', member_id=payment.member.id)

    return redirect('view_payments', member_id=payment.member.id)
    
from twilio.rest import Client
def send_whatsapp_payment(member, pdf_url, message):
    account_sid = 'YOUR_TWILIO_SID'
    auth_token = 'YOUR_TWILIO_AUTH_TOKEN'
    client = Client(account_sid, auth_token)

    whatsapp_number = f'whatsapp:+91{member.phone_number}'
    from_whatsapp = 'whatsapp:+14155238886'  # Twilio sandbox number

    # Send text message
    client.messages.create(
        body=message,
        from_=from_whatsapp,
        to=whatsapp_number
    )

    # Send media (PDF)
    client.messages.create(
        media_url=[pdf_url],  # must be public URL
        from_=from_whatsapp,
        to=whatsapp_number
    )
    
from django.utils import timezone
from datetime import datetime, time
@login_required(login_url='/')
def view_payments(request, member_id):
    member = get_object_or_404(Members, id=member_id)
    selected_date = request.GET.get("date")
    bill_id = request.GET.get("bill_id")

    payments = Payment.objects.filter(member=member)

    if selected_date:
        # Convert string to date
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

        # Get timezone-aware datetime range for that day in Asia/Kolkata
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(date_obj, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(date_obj, time.max), tz)

        payments = payments.filter(date__range=(start_dt, end_dt))

    if bill_id:
        payments = payments.filter(id=bill_id)

    payments = payments.order_by("-date")
    total = sum(p.amount for p in payments)
    today = timezone.localdate()  # default date for filter

    return render(request, "view_payments.html", {
        "member": member,
        "payments": payments,
        "total": total,
        "today": today
    })



@login_required(login_url='/')
def dash(request):
    committee = CommitteeMember.objects.all().order_by('-posting_start_date')
    all_events = Event.objects.all().order_by('date')
    top_committee = committee[:1]   
    next_two = committee[1:3] # First 3 fixed
    scroll_committee = committee[3:]
    notices = Notice.objects.all().order_by('-created_at')
    return render(request,'dashboard.html',{'notices': notices,"committee": committee, "top_committee": top_committee,"next-two":next_two,
        "scroll_committee": scroll_committee,'events': all_events})

@login_required(login_url='/')
def add_member(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    if request.method == "POST":
        name = request.POST.get("name")
        family_name = request.POST.get("family_name")
        phone_number = request.POST.get("phone_number")
        role = request.POST.get("role")
        posting_start_date = request.POST.get("posting_start_date")
        photo = request.FILES.get("photo")

        CommitteeMember.objects.create(
            name=name,
            family_name=family_name,
            phone_number=phone_number,
            role=role,
            posting_start_date=posting_start_date,
            photo=photo
        )

        return redirect("/inventory/dash/")

    return render(request, "addcommitte.html")

@login_required(login_url='/')
def edit_member(request, id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    member = get_object_or_404(CommitteeMember, id=id)

    if request.method == "POST":
        member.name = request.POST.get("name")
        member.family_name = request.POST.get("family_name")
        member.role = request.POST.get("role")
        member.posting_start_date = request.POST.get("posting_start_date")

        if request.FILES.get("photo"):
            member.photo = request.FILES.get("photo")

        member.save()
        return redirect("/inventory/dash/")

    return render(request, "updatecommitte.html", {"member": member})

@login_required(login_url='/')
def delete_member(request, id):
    member = get_object_or_404(CommitteeMember, id=id)
    member.delete()
    return redirect("/inventory/dash/")

@login_required(login_url='/')
def add_notice(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    if request.method == "POST":
        msg = request.POST.get("message")
        Notice.objects.create(message=msg)
        return redirect('/inventory/dash/')   # your homepage URL name
    return render(request, 'add_notice.html')

@login_required(login_url='/')
def delete_notice(request, id):
    notice = Notice.objects.get(id=id)
    notice.delete()
    return redirect('/inventory/dash/')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event



@login_required(login_url='/')
def add_event(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        photo = request.FILES.get('photo')
        Event.objects.create(name=name, date=date, photo=photo)
        return redirect('/inventory/dash/')
    return render(request, 'add_event.html')

@login_required(login_url='/')
def edit_event(request, event_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.name = request.POST.get('name')
        event.date = request.POST.get('date')
        if request.FILES.get('photo'):
            event.photo = request.FILES.get('photo')
        event.save()
        return redirect('/inventory/dash/')
    return render(request, 'edit_event.html', {'event': event})

@login_required(login_url='/')
def delete_event(request, event_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('/inventory/dash/')


from django.shortcuts import render
from django.utils import timezone
from .models import Members, Payment
from django.db.models import Q

from datetime import datetime, time
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Payment

@login_required(login_url='/')
def all_payments(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    # ---------------------------
    # Get search/filter values
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    search_name = request.GET.get("name", "")
    search_father = request.GET.get("father", "")
    

    payments = Payment.objects.all().order_by("-date")

    # ---------------------------
    # Date range filter
    if start_date:
        tz = timezone.get_current_timezone()
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        start_dt = timezone.make_aware(datetime.combine(start_obj, time.min), tz)
        
        if end_date:
            end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_obj = start_obj  # if no end date, use start date
        end_dt = timezone.make_aware(datetime.combine(end_obj, time.max), tz)
        payments = payments.filter(date__range=(start_dt, end_dt))

    # ---------------------------
    # Other text filters
    if search_name:
        payments = payments.filter(member__name__icontains=search_name)
    if search_father:
        payments = payments.filter(member__father_name__icontains=search_father)
    

    # ---------------------------
    # Convert UTC → local time for display
    for pay in payments:
        local_time = pay.date.astimezone(timezone.get_current_timezone())
        pay.local_date = local_time.strftime("%Y-%m-%d")
        pay.local_time = local_time.strftime("%I:%M %p")

    total_amount = sum(p.amount for p in payments)

    return render(request, "all_bills.html", {
        "payments": payments,
        "start_date": start_date,
        "end_date": end_date,
        "search_name": search_name,
        "search_father": search_father,
        "total": total_amount
    })
    
from io import BytesIO
import os, base64, qrcode
from weasyprint import HTML,CSS
def download_member(request, id):
    member = get_object_or_404(Members, id=id)
    base = settings.BASE_DIR

    # ---------- PATHS ----------
    font = os.path.join(base, 'static/fonts/Latha.ttf')
    logo = os.path.join(base, 'static/assests/images/masjid.webp')
    sign = os.path.join(base, 'static/assests/images/sign.jpg')
    seal = os.path.join(base, 'static/assests/images/seals.webp')
    photo = member.photo.path if member.photo else ''

    # ---------- QR ----------
    qr_text = f"{member.serial_no} | {member.name} | {member.phone_number}"
    qr = qrcode.make(qr_text)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    # ---------- HTML ----------
    html = f"""
<!DOCTYPE html>
<html lang="ta">
<head>
<meta charset="UTF-8">
<style>
@page {{
    size: 85.6mm 54mm;
    margin: 0;
}}
@font-face {{
    font-family: Latha;
    src: url('file:///{font.replace(os.sep,'/')}');
}}
body {{
    margin: 0;
    padding: 0;
    font-family: 'Latha', sans-serif;
}}
.card {{
    width: 85.6mm;
    height: 54mm;
    box-sizing: border-box;
    border: 2px solid #d4a437;
    border-radius: 6mm;
    padding: 2mm;
    position: relative;
    page-break-inside: avoid;
}}
.header {{
    background: #065f3c;
    color: white;
    border-radius: 2mm;
    padding: 1.5mm;
    display: flex;
    align-items: center;
}}
.header img {{
    width: 10mm;
}}
.header h4 {{
    flex: 1;
    text-align: center;
    margin: 0;
    font-size: 12px;
}}
.content {{
    display: flex;
    margin-top: 2mm;
}}
.left {{
    width: 60%;
    font-size: 9px;
    line-height: 1.3;
}}
.right {{
    width: 40%;
    text-align: center;
}}
.photo {{
    width: 18mm;
    height: 22mm;
    border: 1px solid #ccc;
    object-fit: cover;
    margin-bottom: 2mm;
}}
.qr {{
    width: 16mm;
}}
.footer {{
    position: absolute;
    bottom: 2mm;
    left: 2mm;
    right: 2mm;
    display: flex;
    justify-content: flex-start;
    align-items: center;
}}
.signature img {{
    width: 20mm;
}}
.seal {{
    width: 18mm;
}}
.back-content {{
    font-size: 8px;
    line-height: 1.3;
    padding: 3mm;
    text-align: left;
}}
</style>
</head>
<body>

<!-- ================= FRONT ================= -->
<div class="card">

    <div class="header">
        <img src="file:///{logo.replace(os.sep,'/')}">
        <h4>வேம்படி பள்ளிவாசல்</h4>
    </div>

    <div class="content">
        <div class="left">
            <b>பெயர்:</b> {member.name}<br>
            <b>தந்தை பெயர்:</b> {member.father_name}<br>
            <b>குடும்பம்:</b> {member.family_name}<br>  
            <b>தொலைபேசி எண்:</b> {member.phone_number}<br>
        </div>

        <div class="right">
            <img src="file:///{photo.replace(os.sep,'/')}" class="photo"><br>
        </div>
    </div>

    <div class="footer">
        <div class="signature" >
            <img src="file:///{sign.replace(os.sep,'/')}">
             <div style=" bottom:2mm; left:2mm; width:50mm; font-size:7px;">தலைவரின் கையொப்பம்</div>
            
        </div>
    </div>

</div>

<!-- ================= BACK ================= -->
<div class="card" style="page-break-before: always; position: relative;">

    <div class="back-content">
    <div style="font-size:8px; line-height:1.4;">
        <b>அட்டை விவரங்கள்</b><br><br>
        <b>புத்தகம் எண்:</b> {member.book_number}<br>
        <b>வரிசை எண்:</b> {member.serial_no}<br>
        <b>சேர்ந்த தேதி:</b> {member.year.strftime('%d/%m/%Y')}<br>
        <b>முகவரி:</b> {member.address}<br><br>
        </div>
    </div>
         <!-- Seal bottom-left -->
    <img src="file:///{seal.replace(os.sep,'/')}" style="position:absolute; bottom:4mm; left:2mm; width:20mm;">

    <!-- QR bottom-right -->
    <img src="data:image/png;base64,{qr_b64}" style="position:absolute; bottom:20mm; right:2mm; width:20mm;">
</div>



</body>
</html>
"""


    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{member.name}_CR80_ID.pdf"'
    return response

from django.utils import timezone
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import HRFlowable
import os

from datetime import datetime, time
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.staticfiles import finders
from weasyprint import HTML
from django.template.loader import render_to_string
from .models import Members, Payment

def download_payment_summary(request, member_id):
    member = Members.objects.get(id=member_id)
    selected_date = request.GET.get("date")
    bill_id = request.GET.get("bill_id")

    payments = Payment.objects.filter(member=member)

    # ---------------------------
    # DATE FILTER
    if selected_date:
        tz = timezone.get_current_timezone()
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        start_dt = timezone.make_aware(datetime.combine(date_obj, time.min), tz)
        end_dt = timezone.make_aware(datetime.combine(date_obj, time.max), tz)
        payments = payments.filter(date__range=(start_dt, end_dt))

    # BILL ID FILTER
    if bill_id:
        payments = payments.filter(id=bill_id)

    payments = payments.order_by("-date")
    total_amount = sum(p.amount for p in payments)

    # ---------------------------
    # Prepare payments table
    payment_list = []
    for p in payments:
        local_time = p.date.astimezone(timezone.get_current_timezone())
        payment_list.append({
            "id": p.id,
            "date": local_time.strftime("%Y-%m-%d"),
            "time": local_time.strftime("%I:%M %p"),
            "amount": f"{p.amount}",
            "reason": p.reason
        })

    # ---------------------------
    # Images
    logo_path = finders.find("assests/images/masjid.webp")
    sign_path = finders.find("assests/images/sign.jpg")
    seal_path = finders.find("assests/images/seals.webp")
    
    # Convert to file URLs for WeasyPrint
    logo_url = f"file:///{logo_path.replace(os.sep, '/')}" if logo_path else None
    sign_url = f"file:///{sign_path.replace(os.sep, '/')}" if sign_path else None
    seal_url = f"file:///{seal_path.replace(os.sep, '/')}" if seal_path else None


    # ---------------------------
    # Render HTML template
    html_string = render_to_string("payment_summary_tamil.html", {
        "member": member,
        "payments": payment_list,
        "total_amount": total_amount,
        "logo_url": logo_url,
        "sign_url": sign_url,
        "seal_url": seal_url,
        "selected_date": selected_date,
        "bill_id": bill_id,
    })

    # ---------------------------
    # Generate PDF
    pdf_file = io.BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_file)
    pdf_file.seek(0)

    # ---------------------------
    # Filename
    filename = f"{member.name}_PaymentSummary.pdf"
    if selected_date and bill_id:
        filename = f"{member.name}_{selected_date}_Bill_{bill_id}.pdf"
    elif selected_date:
        filename = f"{member.name}_{selected_date}_Bill.pdf"
    elif bill_id:
        filename = f"{member.name}_Bill_{bill_id}.pdf"

    return HttpResponse(pdf_file.getvalue(), content_type='application/pdf', headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    })



from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


import io
from datetime import datetime, time
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from weasyprint import HTML
from django.template.loader import render_to_string
from .models import Payment
@login_required(login_url='/')
def download_all_payments(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    # ---------------------------
    # Get filters
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    search_name = request.GET.get("name", "")
    search_father = request.GET.get("father", "")

    payments = Payment.objects.all().order_by("-date")

    # Date range filter
    if start_date:
        tz = timezone.get_current_timezone()
        start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        start_dt = timezone.make_aware(datetime.combine(start_obj, time.min), tz)
        if end_date:
            end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_obj = start_obj
        end_dt = timezone.make_aware(datetime.combine(end_obj, time.max), tz)
        payments = payments.filter(date__range=(start_dt, end_dt))

    if search_name:
        payments = payments.filter(member__name__icontains=search_name)
    if search_father:
        payments = payments.filter(member__father_name__icontains=search_father)

    total_amount = sum(p.amount for p in payments)

    # ---------------------------
    # Prepare payments list
    payment_list = []
    for p in payments:
        local_time = p.date.astimezone(timezone.get_current_timezone())
        payment_list.append({
            "id": p.id,
            "name": p.member.name,
            "father": p.member.father_name,
            "date": local_time.strftime("%Y-%m-%d"),
            "time": local_time.strftime("%I:%M %p"),
            "amount": f"{p.amount}",
            "reason": p.reason
        })

    # ---------------------------
    # Images
    logo_path = finders.find("assests/images/masjid.webp")
    sign_path = finders.find("assests/images/sign.jpg")
    seal_path = finders.find("assests/images/seals.webp")

    # Convert to file URLs for WeasyPrint
    logo_url = f"file:///{logo_path.replace(os.sep, '/')}" if logo_path else None
    sign_url = f"file:///{sign_path.replace(os.sep, '/')}" if sign_path else None
    seal_url = f"file:///{seal_path.replace(os.sep, '/')}" if seal_path else None

    # ---------------------------
    # Render HTML template
    html_string = render_to_string("all_payments_tamil.html", {
        "payments": payment_list,
        "total_amount": total_amount,
        "start_date": start_date,
        "end_date": end_date,
        "search_name": search_name,
        "search_father": search_father,
        "logo_url": logo_url,
        "sign_url": sign_url,
        "seal_url": seal_url,
    })

    # ---------------------------
    # Generate PDF
    pdf_file = io.BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_file)
    pdf_file.seek(0)

    filename = "All_Payments_Summary.pdf"
    return HttpResponse(pdf_file.getvalue(), content_type='application/pdf', headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    })