from django.urls import path
from django.conf import settings
from django.shortcuts import render
from .views import register_customer, manage_members, edit_member, user_view_members,user_logout, delete_member, add_member, submit_blood_donation, blood_donation_list, update_blood_donation_status, view_members
from .views import approve_user, login_view,  admin_dashboard, user_dashboard, reject_user, generate_id_card
from .views import generate_payment_receipt, running_sahyog, sahyog_list, edit_sahyog, delete_sahyog, send_notification, manage_notifications, delete_notification
from django.conf.urls.static import static
from .views import user_profile, upload_receipt, user_receipts, admin_receipts, upload_vyawastha_shulk, user_vyawastha_shulk_receipts, admin_vyawastha_shulk_receipts
from django.urls import path






urlpatterns = [
    path("register/", register_customer, name="register_customer"),
    path('registration-success/', lambda request: render(request, 'donation/registration_success.html'), name='registration_success'),
    path("approve-user/<int:user_id>/", approve_user, name="approve_user"),
    path("reject-user/<int:user_id>/", reject_user, name="reject_user"),
    path('receipt/<int:customer_id>/', generate_payment_receipt, name='generate_payment_receipt'),
    path('login/', login_view, name='login'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path("user-dashboard/", user_dashboard, name="user_dashboard"),  # ✅ Ensure this exists
    path('manage-members/', manage_members, name='manage_members'),
    path("view-members/", view_members, name="view_members"),
    path("user-view-members/", user_view_members, name="user_view_members"),  # Normal Users Only
    path("edit-member/<int:user_id>/", edit_member, name="edit_member"),
    path("delete-member/<int:user_id>/", delete_member, name="delete_member"),
    path('add-member/', add_member, name='add_member'),
    path('running-sahyog/', running_sahyog, name='running_sahyog'),  # ✅ Admin Adds Sahyog
    path('sahyog-list/', sahyog_list, name='sahyog_list'),  # ✅ Users View Sahyog

    # ✅ Only Custom Admins (is_staff) can access these
    path('edit-sahyog/<int:sahyog_id>/', edit_sahyog, name='edit_sahyog'),
    path('delete-sahyog/<int:sahyog_id>/', delete_sahyog, name='delete_sahyog'),
    path("send-notification/", send_notification, name="send_notification"),
    path("manage-notifications/", manage_notifications, name="manage_notifications"),
    path("admin/delete_notification/<int:notification_id>/", delete_notification, name="delete_notification"),







    path("user-profile/", user_profile, name="user_profile"),  # ✅ Profile Page URL
    path("upload_receipt/", upload_receipt, name="upload_receipt"),  # Removed sahyog_id
    path("user_receipts/", user_receipts, name="user_receipts"),
    path("admin_receipts/", admin_receipts, name="admin_receipts"),
    path("upload_vyawastha_shulk/", upload_vyawastha_shulk, name="upload_vyawastha_shulk"),
    path("user_vyawastha_shulk_receipts/", user_vyawastha_shulk_receipts, name="user_vyawastha_shulk_receipts"),
    path("admin_vyawastha_shulk_receipts/", admin_vyawastha_shulk_receipts, name="admin_vyawastha_shulk_receipts"),
    path("donate/", submit_blood_donation, name="submit_blood_donation"),
    path("donations/", blood_donation_list, name="blood_donation_list"),
    path("update_donation/<int:donation_id>/<str:status>/", update_blood_donation_status, name="update_blood_donation_status"),
    path("generate_id_card/", generate_id_card, name="generate_id_card"),




    
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)