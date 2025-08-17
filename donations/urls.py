from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse_lazy
from .views import (
    register_customer, custom_admin_login, admin_dashboard, user_dashboard,
    manage_members, view_members, edit_member, approve_user, reject_user,
    user_profile, user_download_id_card, upload_receipt, user_receipts, admin_receipts, upload_vyawastha_shulk, user_vyawastha_shulk_receipts, admin_vyawastha_shulk_receipts,
    submit_blood_donation, blood_donation_list, update_blood_donation_status,
    send_notification, manage_notifications, delete_notification, upi_qr, user_logout,
    CustomPasswordResetView, CustomPasswordResetConfirmView,
    download_members_excel, download_sahyog_excel, user_view_members
)
from .views import generate_payment_receipt, running_sahyog, sahyog_list, edit_sahyog, delete_sahyog, generate_id_card, add_member, delete_member, user_view_members, admin_id_card_management, admin_edit_id_card, admin_generate_id_card, admin_download_id_card
from django.conf.urls.static import static






urlpatterns = [
    path("register/", register_customer, name="register_customer"),
    path('registration-success/', lambda request: render(request, 'donation/registration_success.html'), name='registration_success'),
    path("approve-user/<int:user_id>/", approve_user, name="approve_user"),
    path("reject-user/<int:user_id>/", reject_user, name="reject_user"),
    path('receipt/<int:customer_id>/', generate_payment_receipt, name='generate_payment_receipt'),
    path('login/', custom_admin_login, name='login'),
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
    path('delete-sahyog/<int:sahyog_id>/', delete_sahyog, name="delete_sahyog"),
    path("send-notification/", send_notification, name="send_notification"),
    path("manage-notifications/", manage_notifications, name="manage_notifications"),
    path("admin/delete_notification/<int:notification_id>/", delete_notification, name="delete_notification"),
    
    # Excel Download URLs
    path("download-members-excel/", download_members_excel, name="download_members_excel"),
    path("download-sahyog-excel/", download_sahyog_excel, name="download_sahyog_excel"),
    
    # Logout URL
    path("logout/", user_logout, name="logout"),







    path("user-profile/", user_profile, name="user_profile"),  # ✅ Profile Page URL
    path("user-download-id-card/", user_download_id_card, name="user_download_id_card"),  # ✅ User ID Card Download
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
    
    # Admin ID Card Management URLs
    path("admin/id-cards/", admin_id_card_management, name="admin_id_card_management"),
    path("admin/id-cards/edit/<int:customer_id>/", admin_edit_id_card, name="admin_edit_id_card"),
    path("admin/id-cards/generate/<int:customer_id>/", admin_generate_id_card, name="admin_generate_id_card"),
    path("admin/id-cards/download/<int:customer_id>/", admin_download_id_card, name="admin_download_id_card"),


    


    # ✅ User Password Reset with Custom Views
    path("user/password_reset/", CustomPasswordResetView.as_view(), name="user_password_reset"),
    path("user/password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="donation/user_password_reset_done.html"), name="user_password_reset_done"),
    path("user/reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="user_password_reset_confirm"),
    path("user/reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="donation/user_password_reset_complete.html"), name="user_password_reset_complete"),
    
    # 🔹 Admin Password Reset URLs
    path("admin/password_reset/", auth_views.PasswordResetView.as_view(
        template_name="donation/admin_password_reset.html",
        email_template_name="donation/admin_password_reset_email.html",
        subject_template_name="donation/admin_password_reset_subject.txt",
        success_url=reverse_lazy("admin_password_reset_done")
    ), name="admin_password_reset"),
    path("admin/password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="donation/admin_password_reset_done.html"), name="admin_password_reset_done"),
    path("admin/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="donation/admin_password_reset_confirm.html"), name="admin_password_reset_confirm"),
    path("admin/reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="donation/admin_password_reset_complete.html"), name="admin_password_reset_complete"),
    path("upi-qr/", upi_qr, name="upi_qr"),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)