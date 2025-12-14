from django.urls import path
from .views import *

urlpatterns = [
    path('home/',member),
    path('dash/',dash),
    path('allmember/',allmember),
    path('all-payments/', all_payments, name='all_payments'),
    path('update/<int:id>/', update_member, name='update_member'),
    path('download/<int:id>/', download_member, name='download_member'),
    path('member/<int:member_id>/payment/add/', add_payment, name="add_payment"),
    path('member/<int:member_id>/payment/history/', view_payments, name="view_payments"),
    path(
    'payment/delete/<int:payment_id>/',
    delete_payment,
    name='delete_payment'
),

    path('member/<int:member_id>/payment/pdf/', download_payment_summary, name="download_payment_summary"),
    path("dashboard/committee/add/", add_member, name="add_member"),
    path("dashboard/committee/edit/<int:id>/", edit_member, name="edit_member"),
    path("dashboard/committee/delete/<int:id>/", delete_member, name="delete_member"),
    path('dashboard/notice/add/', add_notice, name='add_notice'),
    path('dashboard/notice/delete/<int:id>/', delete_notice, name='delete_notice'),
    
    path('payments/download-all/', download_all_payments, name='download_all_payments'),
    
    path('events/add/', add_event, name='add_event'),
    path('events/edit/<int:event_id>/', edit_event, name='edit_event'),
    path('events/delete/<int:event_id>/', delete_event, name='delete_event'),


    

]