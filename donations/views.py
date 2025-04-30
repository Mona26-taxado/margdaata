from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from .forms import CustomerRegistrationForm, NotificationForm, BloodDonationApprovalForm, BloodDonationForm
from .models import Customer, BloodDonation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.contrib import messages
from .models import Customer, Notification, VyawasthaShulkReceipt
from .models import CustomUser, Sahyog
from .forms import CustomUserCreationForm, SahyogForm, SahyogReceipt, VyawasthaShulkReceiptForm
from donations.forms import SahyogReceiptForm
import os
from datetime import datetime
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.admin.views.decorators import staff_member_required
import fitz  # PyMuPDF
from django.http import FileResponse, HttpResponse
from io import BytesIO
import qrcode

from django.contrib.auth import get_user_model
import os

from django.shortcuts import render
from django.db.models import Sum
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST

def admin_dashboard(request):
    total_users = CustomUser.objects.count()
    total_sahyog = Sahyog.objects.count()
    total_blood_donors = BloodDonation.objects.count()
    total_vyawastha_shulk = VyawasthaShulkReceipt.objects.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        "total_users": total_users,
        "total_sahyog": total_sahyog,
        "total_blood_donors": total_blood_donors,
        "total_vyawastha_shulk": total_vyawastha_shulk,
    }

    return render(request, "donation/admin_dashboard.html", context)

CustomUser = get_user_model()

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")  # ✅ Users enter email, but Django expects 'username'
        password = request.POST.get("password")

        print(f"🔍 Debug: Login Email = {email}, Password = {password}")

        # ✅ Find user by email
        user = CustomUser.objects.filter(email=email).first()

        if not user:
            print("❌ Debug: No user found with this email")
            return render(request, "donation/login.html", {"error": "Invalid email or password"})

        print(f"✅ Debug: Found user with email = {user.email}")

        # ✅ Authenticate using 'username' argument (Django expects username, not email)
        user = authenticate(request, username=email, password=password)

        if user is None:
            print("❌ Debug: Authentication failed, incorrect password")
            return render(request, "donation/login.html", {"error": "Invalid email or password"})

        print(f"✅ Debug: Authentication successful for {user.email}")

        login(request, user)

        return redirect("admin_dashboard" if user.is_staff else "user_dashboard")

    return render(request, "donation/login.html")

from django.contrib import messages  # ✅ Import messages for Bootstrap alerts

def register_customer(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                cleaned_data = form.cleaned_data
                email = cleaned_data.get("email")
                password = request.POST.get("password")  # Password is not in form, so get from POST

                # Check for duplicate email
                if CustomUser.objects.filter(email=email).exists():
                    error_msg = "This email is already registered. Please use a different email or log in."
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': {'email': [error_msg]}}, status=400)
                    else:
                        form.add_error('email', error_msg)
                        return render(request, "donation/register.html", {"form": form})

                if not password:
                    error_msg = "Password is required."
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': {'password': [error_msg]}}, status=400)
                    else:
                        form.add_error(None, error_msg)
                        return render(request, "donation/register.html", {"form": form})

                user = CustomUser.objects.create(
                    email=email,
                    role="user",
                    is_approved=False,
                    is_active=False
                )
                user.set_password(password)
                user.save()

                customer = form.save(commit=False)
                customer.user = user
                customer.approved = False
                customer.save()

                # Send notification email to admins
                admin_emails = CustomUser.objects.filter(is_staff=True).values_list('email', flat=True)
                if admin_emails:
                    send_mail(
                        'New Registration Request',
                        f'A new registration request has been received from {customer.name} ({customer.email}).\n\n'
                        f'Please review and approve/reject the request in the admin dashboard.\n\n'
                        f'Details:\n'
                        f'Name: {customer.name}\n'
                        f'Email: {customer.email}\n'
                        f'Mobile: {customer.mobile}\n'
                        f'Transaction ID: {customer.transaction_id}\n'
                        f'Registered On: {customer.created_at.strftime("%d-%m-%Y %H:%M")}',
                        settings.EMAIL_HOST_USER,
                        list(admin_emails),
                        fail_silently=False,
                    )

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'redirect_url': reverse('registration_success')})
                messages.success(request, "Registration successful! Await admin approval.")
                return redirect('registration_success')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        except Exception as e:
            logging.exception("Registration error")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': {'__all__': [str(e)]}}, status=500)
            else:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = CustomerRegistrationForm()
    return render(request, "donation/register.html", {"form": form})

@login_required
def approve_user(request, user_id):
    if request.method != "POST":  # ❌ Rejects GET requests
        return JsonResponse({"error": "Invalid request method"}, status=405)

    # ✅ Ensure the user exists
    user = get_object_or_404(CustomUser, id=user_id)

    # ✅ Ensure the customer exists
    customer = Customer.objects.filter(user=user).first()
    if not customer:
        return JsonResponse({"error": "No customer found"}, status=404)

    # ✅ Approve and activate the user
    user.is_approved = True
    user.is_active = True
    user.save()

    # ✅ Approve the customer entry
    customer.approved = True
    customer.save()

    # ✅ Send Approval Email Notification
    send_mail(
        'Your Account Has Been Approved',
        f'Hello {user.username},\n\nYour account has been successfully approved. You can now log in and access your services.\n\nBest Regards,\nMargdata Team',
        settings.EMAIL_HOST_USER,
        [user.email],  # Send to the user's registered email
        fail_silently=False,
    )

    return redirect("manage_members")






from django.urls import reverse

def reject_user(request, user_id):
    if request.method == "POST":
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            messages.error(request, "❌ User not found or already deleted.")
            return redirect(reverse("manage_members"))

        user_email = user.email  # Save email before deleting
        user.delete()  # ✅ Completely remove user

        # ✅ Send rejection email
        send_mail(
            "Your Registration Request is Rejected",
            f"Hello,\n\nUnfortunately, your registration request has been rejected and removed from our system.\nFor more information, please contact support.\n\nBest Regards,\nMargdata Team",
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False,
        )

        messages.success(request, f"❌ User {user_email} has been rejected and deleted.")
    
    return redirect(reverse("manage_members"))  # Redirect back to admin panel

from django.contrib.auth.backends import ModelBackend

# ✅ Custom authentication backend that supports both email and username
class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # ✅ Prevents crashes by returning None for missing credentials
        if username is None or password is None:
            return None

        try:
            if "@" in username:
                user = CustomUser.objects.get(email=username)
            else:
                user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return None  # ✅ User not found, return None

        # ✅ Ensures password verification is correct
        if user and user.check_password(password):
            return user

        return None

# ✅ Login View (Supports Both Admin & User Login)
def custom_admin_login(request):
    if request.user.is_authenticated:
        return redirect("admin_dashboard" if request.user.role == "admin" else "user_dashboard")

    if request.method == "POST":
        email_or_username = request.POST.get("email")  # ✅ Supports email or username
        password = request.POST.get("password")
        user = authenticate(request, username=email_or_username, password=password)

        if user:
            if user.is_approved and user.is_active:
                login(request, user)
                return redirect("admin_dashboard" if user.role == "admin" else "user_dashboard")
            else:
                messages.error(request, "Your account is pending approval or inactive.")
        else:
            messages.error(request, "Invalid email/username or password.")

    return render(request, "donation/login.html")

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt  # Bypasses CSRF token issues (for GET logout)
def user_logout(request):
    if request.method == "POST" or request.method == "GET":  # Accept both methods
        logout(request)
        return redirect("login")  # Redirect to login page

def generate_payment_receipt(request, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return HttpResponse("Customer not found", status=404)

    # Set up the response as a PDF file
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payment_Receipt_{customer.md_code}.pdf"'

    # Create the PDF object
    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle(f"Payment Receipt - {customer.md_code}")

    # Add content to the PDF
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Payment Receipt")
    pdf.setFont("Helvetica", 12)

    pdf.drawString(100, 700, f"MD Code: {customer.md_code}")
    pdf.drawString(100, 680, f"Name: {customer.name}")
    pdf.drawString(100, 660, f"Email: {customer.email}")
    pdf.drawString(100, 640, f"Mobile: {customer.mobile}")
    pdf.drawString(100, 620, f"Nominee: {customer.nominee_name} ({customer.nominee_relation})")
    pdf.drawString(100, 600, f"Payment Slip: {customer.payment_slip.url if customer.payment_slip else 'N/A'}")

    pdf.drawString(100, 570, "Thank you for your payment!")

    pdf.showPage()
    pdf.save()

    return response

# ✅ Admin Dashboard (Only for Custom Admin)
@login_required
def custom_admin_dashboard(request):
    if request.user.role != "admin":
        return redirect('user_dashboard')  # If user is not admin, redirect to user dashboard
    return render(request, "donation/admin_dashboard.html")

# ✅ User Dashboard (For Normal Users)
@login_required
def user_dashboard(request):
    if request.user.is_staff:
        return HttpResponseForbidden("You are not allowed to access this page.")

    notifications = Notification.objects.filter(
        Q(target_type="all_users") |
        Q(target_type="specific_user", specific_user=request.user)
    ).order_by('-created_at')

    return render(request, 'donation/user_dashboard.html', {'notifications': notifications})

def manage_members(request):
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Fetch approved users with search filter
    approved_users = Customer.objects.filter(approved=True)
    if search_query:
        approved_users = approved_users.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )
    approved_users = approved_users.order_by("-created_at")
    
    # Fetch pending requests with search filter
    pending_requests = Customer.objects.filter(approved=False)
    if search_query:
        pending_requests = pending_requests.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )
    pending_requests = pending_requests.order_by("-created_at")

    # Pagination for approved users (10 per page)
    approved_paginator = Paginator(approved_users, 10)
    approved_page_number = request.GET.get('approved_page', 1)
    approved_page_obj = approved_paginator.get_page(approved_page_number)

    # Add serial numbers for approved users
    approved_start_index = (approved_page_obj.number - 1) * approved_paginator.per_page + 1
    for index, user in enumerate(approved_page_obj, start=approved_start_index):
        user.serial_number = index

    # Pagination for pending requests (10 per page)
    pending_paginator = Paginator(pending_requests, 10)
    pending_page_number = request.GET.get('pending_page', 1)
    pending_page_obj = pending_paginator.get_page(pending_page_number)

    # Add serial numbers for pending requests
    pending_start_index = (pending_page_obj.number - 1) * pending_paginator.per_page + 1
    for index, user in enumerate(pending_page_obj, start=pending_start_index):
        user.serial_number = index

    return render(request, "donation/manage_members.html", {
        "approved_users": approved_page_obj,
        "pending_requests": pending_page_obj,
        "search_query": search_query,
        "approved_paginator": approved_paginator,
        "pending_paginator": pending_paginator
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customer
from .forms import CustomerRegistrationForm  # Use the existing form

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Customer
from .forms import CustomerEditForm

# View Members: Separate for Admin and Users
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Customer  # Import your model

def view_members(request):
    search_query = request.GET.get('search', '')  # Get search query from request
    approved_users = Customer.objects.filter(approved=True)  # Fetch only approved users

    # If search query exists, filter by name, email, or mobile
    if search_query:
        approved_users = approved_users.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )

    approved_users = approved_users.order_by("-created_at")  # Order by newest first

    # Pagination (10 users per page)
    paginator = Paginator(approved_users, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Add serial numbers based on page number
    start_index = (page_obj.number - 1) * paginator.per_page + 1
    for index, user in enumerate(page_obj, start=start_index):
        user.serial_number = index

    # Check if user is admin or normal user
    if request.user.is_staff:  
        return render(request, "donation/view_members.html", {
            "approved_users": page_obj,
            "search_query": search_query,
            "paginator": paginator,
            "page_obj": page_obj
        })
    else:  
        return render(request, "donation/user_view_members.html", {
            "approved_users": page_obj,
            "search_query": search_query,
            "paginator": paginator,
            "page_obj": page_obj
        })

# Edit Member Details (Only for Admin)
def edit_member(request, user_id):
    if not request.user.is_staff:  # Prevent users from editing
        messages.error(request, "Unauthorized Access!")
        return redirect("view_members")

    member = get_object_or_404(Customer, id=user_id)
    if request.method == "POST":
        form = CustomerEditForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.name}'s details have been updated!")
            return redirect("view_members")
    else:
        form = CustomerEditForm(instance=member)

    return render(request, "donation/edit_member.html", {"form": form, "member": member})

# Delete Member (Only for Admin)
def delete_member(request, user_id):
    if not request.user.is_staff:  # Prevent users from deleting
        messages.error(request, "Unauthorized Access!")
        return redirect("view_members")

    member = get_object_or_404(Customer, id=user_id)
    member.delete()
    messages.error(request, f"{member.name} has been removed!")
    return redirect("view_members")

def user_view_members(request):
    approved_users = Customer.objects.filter(approved=True).order_by("-created_at")  # ✅ Order by newest first
    return render(request, "donation/user_view_members.html", {"approved_users": approved_users})

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_member(request):
    if request.method == "POST":
        print("✅ DEBUG: Received POST request to add member")
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_approved = True  # ✅ Auto-approve admin-added users
                user.is_active = True  # ✅ Activate user
                user.role = "user"  # ✅ Ensure correct role
                
                print(f"🔍 DEBUG: Trying to save user {user.email}")  # Debug print
                
                user.save()
                
                print(f"✅ User {user.email} saved successfully!")  # Debug print

                # ✅ Ensure a `Customer` entry is created
                customer, created = Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        "name": request.POST.get("name"),
                        "email": user.email,
                        "mobile": request.POST.get("mobile"),
                        "approved": True,  # ✅ Auto-approve
                        "posting_state": request.POST.get("posting_state"),  # ✅ Save State
                        "posting_district": request.POST.get("posting_district"),  # ✅ Save District
                    }
                )

                print(f"✅ Customer entry created for {user.email}")  # Debug print
                print(f"📌 State: {customer.posting_state}, District: {customer.posting_district}")  # Debugging output

                messages.success(request, "New member added successfully.")
                return redirect('manage_members')

            except Exception as e:
                print(f"❌ ERROR while saving user: {str(e)}")  # Print error message
                messages.error(request, f"Error adding member: {str(e)}")
        else:
            print("❌ FORM ERROR:", form.errors)  # Print validation errors
            messages.error(request, f"Form errors: {form.errors}")

    else:
        form = CustomUserCreationForm()

    return render(request, 'donation/add_member.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def running_sahyog(request):
    if request.method == "POST":
        title = request.POST.get("title")
        account_holder_name = request.POST.get("account_holder_name")  # ✅ New Field
        bank_name = request.POST.get("bank_name")
        account_number = request.POST.get("account_number")
        ifsc_code = request.POST.get("ifsc_code")
        qr_code = request.FILES.get("qr_code")

        sahyog = Sahyog(
            title=title,
            account_holder_name=account_holder_name,  # ✅ Saving New Field
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            qr_code=qr_code
        )
        sahyog.save()
        return redirect('sahyog_list')

    return render(request, "donation/running_sahyog.html")

# ✅ Restrict Editing to Custom Admins Only
@login_required
@user_passes_test(lambda u: u.is_staff)  # ✅ Only Custom Admin can access
def edit_sahyog(request, sahyog_id):
    sahyog = get_object_or_404(Sahyog, id=sahyog_id)  # Get Sahyog by ID

    if request.method == "POST":
        form = SahyogForm(request.POST, request.FILES, instance=sahyog)
        if form.is_valid():
            form.save()
            return redirect('sahyog_list')  # Redirect to Sahyog list after edit
    else:
        form = SahyogForm(instance=sahyog)

    return render(request, "donation/edit_sahyog.html", {"form": form, "sahyog": sahyog})

# ✅ Restrict Deleting to Custom Admins Only
@login_required
@user_passes_test(lambda u: u.is_staff)  # Only admins can delete
def delete_sahyog(request, sahyog_id):
    sahyog = get_object_or_404(Sahyog, id=sahyog_id)
    sahyog.delete()
    return redirect('sahyog_list')

def sahyog_list(request):
    sahyog_entries = Sahyog.objects.all()  # ✅ Get all Sahyog entries
    
    # ✅ Choose base template dynamically
    base_template = "donation/base.html" if request.user.is_staff else "donation/base_user.html"
    
    return render(request, "donation/sahyog_list.html", {
        "sahyog_list": sahyog_entries,
        "base_template": base_template
    })

# Check if the user is a Custom Admin
def is_custom_admin(user):
    return user.is_staff  # Modify if you have a separate admin role

User = get_user_model()  # ✅ This ensures it fetches `CustomUser`

def send_notification(request):
    users = User.objects.all()
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            target_type = form.cleaned_data["target_type"]
            specific_user_id = request.POST.get("specific_user")

            if target_type == "specific_user":
                if not specific_user_id:
                    messages.error(request, "Please select a user.")
                else:
                    notification = form.save(commit=False)
                    notification.specific_user_id = specific_user_id
                    notification.save()
                    messages.success(request, "Notification sent successfully!")
                    return redirect("send_notification")
            else:
                # For all users, clear specific_user
                notification = form.save(commit=False)
                notification.specific_user = None
                notification.save()
                messages.success(request, "Notification sent successfully!")
                return redirect("send_notification")
    else:
        form = NotificationForm()
    return render(request, "donation/send_notification.html", {"form": form, "users": users})

# ✅ View to display notifications for admin
@login_required
@user_passes_test(is_custom_admin)
def manage_notifications(request):
    notifications = Notification.objects.order_by("-created_at")  # Show latest notifications first
    return render(request, "donation/manage_notifications.html", {"notifications": notifications})

@staff_member_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return redirect("manage_notifications")  # Redirect back to notifications list

@login_required
def user_profile(request):
    customer = get_object_or_404(Customer, user=request.user)

    if request.method == "POST":
        # Retrieve each field from request.POST
        customer.name = request.POST.get("name")
        customer.mobile = request.POST.get("mobile")
        customer.email = request.POST.get("email")
        customer.dob = request.POST.get("dob")
        customer.aadhar = request.POST.get("aadhar")
        customer.home_address = request.POST.get("home_address")
        customer.department = request.POST.get("department")
        customer.post = request.POST.get("post")
        customer.posting_state = request.POST.get("posting_state")
        customer.posting_district = request.POST.get("posting_district")
        customer.disease = request.POST.get("disease")

        # Nominee fields as well
        customer.first_nominee_name = request.POST.get("first_nominee_name")
        customer.first_nominee_relation = request.POST.get("first_nominee_relation")
        customer.first_nominee_mobile = request.POST.get("first_nominee_mobile")

        # Finally save
        customer.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("user_profile")  # refreshes the page

    # GET request just shows the form
    return render(request, "donation/user_profile.html", {"customer": customer})

@login_required
def upload_receipt(request):
    if request.method == "POST":
        form = SahyogReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user  # Attach the receipt to the logged-in user
            receipt.sahyog = None  # ✅ Ensure no Sahyog is assigned
            receipt.save()
            return redirect("user_receipts")  # Redirect to receipt list

    else:
        form = SahyogReceiptForm()

    return render(request, "donation/upload_receipt.html", {"form": form})

@login_required
def user_receipts(request):
    receipts = SahyogReceipt.objects.filter(user=request.user)
    return render(request, "donation/user_receipts.html", {"receipts": receipts})

@staff_member_required
def admin_receipts(request):
    receipts = SahyogReceipt.objects.all()
    return render(request, "donation/admin_receipts.html", {"receipts": receipts})

@login_required
def upload_vyawastha_shulk(request):
    if request.method == "POST":
        form = VyawasthaShulkReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.user = request.user
            receipt.save()
            return redirect("user_vyawastha_shulk_receipts")  # Redirect to receipt list

    else:
        form = VyawasthaShulkReceiptForm()

    return render(request, "donation/upload_vyawastha_shulk.html", {"form": form})

@login_required
def user_vyawastha_shulk_receipts(request):
    receipts = VyawasthaShulkReceipt.objects.filter(user=request.user)
    return render(request, "donation/user_vyawastha_shulk_receipts.html", {"receipts": receipts})

@staff_member_required
def admin_vyawastha_shulk_receipts(request):
    receipts = VyawasthaShulkReceipt.objects.all()
    return render(request, "donation/admin_vyawastha_shulk_receipts.html", {"receipts": receipts})

@login_required
def submit_blood_donation(request):
    if request.method == "POST":
        form = BloodDonationForm(request.POST, request.FILES)
        if form.is_valid():
            blood_donation = form.save(commit=False)
            blood_donation.user = request.user
            blood_donation.save()
            return redirect("blood_donation_list")
    else:
        form = BloodDonationForm()
    return render(request, "donation/blood_donation_form.html", {"form": form})

@login_required
def blood_donation_list(request):
    donations = BloodDonation.objects.all().order_by("-created_at")
    
    # Use different base templates based on user type
    if request.user.is_staff:
        base_template = "donation/base.html"
    else:
        base_template = "donation/base_user.html"

    return render(request, "donation/blood_donation_list.html", {
        "donations": donations,
        "base_template": base_template
    })

@staff_member_required
def update_blood_donation_status(request, donation_id, status):
    donation = get_object_or_404(BloodDonation, id=donation_id)
    if status in ["Pending", "Approved", "Completed"]:
        donation.status = status
        donation.save()
    return redirect("blood_donation_list")

@login_required
def generate_id_card(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        return HttpResponse("Customer profile not found", status=404)

    # Load the existing ID Card PDF template
    template_path = "static/assets/img/Margdata_ID_Card.pdf"
    doc = fitz.open(template_path)
    page = doc[0]  # Select the first page

    # Define text positions (X, Y)
    text_positions = {
        "name": (10, 70),  
        "email": (10, 90),
        "mobile": (10, 110),
        "dob": (10, 130),
        "posting_state": (10, 150),
        "md_code": (10, 170),
        "registered_on": (10, 190),
    }

    # ✅ Add user details with better text wrapping
    add_wrapped_text(page, "Name:", customer.name or "N/A", text_positions["name"])
    add_wrapped_text(page, "Email:", customer.email or "N/A", text_positions["email"], max_width=120, line_spacing=10)
    add_wrapped_text(page, "Mobile:", customer.mobile or "N/A", text_positions["mobile"])
    add_wrapped_text(page, "DOB:", customer.dob.strftime('%d-%m-%Y') if customer.dob else "N/A", text_positions["dob"])
    add_wrapped_text(page, "State:", customer.posting_state or "N/A", text_positions["posting_state"], max_width=120, line_spacing=10)
    add_wrapped_text(page, "MD Code:", customer.md_code or "N/A", text_positions["md_code"])
    add_wrapped_text(page, "Registered On:", customer.created_at.strftime('%d-%m-%Y'), text_positions["registered_on"])

    # Save the modified PDF
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename="Margdata_ID_Card.pdf")

# ✅ Improved Text Wrapping Function
def add_wrapped_text(page, label, value, position, max_width=120, line_spacing=8):
    """Handles wrapping text if it exceeds max width."""
    words = (f"{label} {value}").split()
    current_line = ""
    y_offset = 0
    font_size = 8
    text_color = (0, 0, 0)
    font_regular = "times-roman"

    for word in words:
        test_line = f"{current_line} {word}".strip()
        text_width = page.insert_text(position, test_line, fontsize=font_size, fontname=font_regular, color=text_color)

        # ✅ If text exceeds max_width, move to the next line
        if text_width > max_width:
            page.insert_text((position[0], position[1] + y_offset), current_line, fontsize=font_size, fontname=font_regular, color=text_color)
            current_line = word  # Start new line
            y_offset += line_spacing  # Adjust line spacing
        else:
            current_line = test_line

    # ✅ Insert the last line
    page.insert_text((position[0], position[1] + y_offset), current_line, fontsize=font_size, fontname=font_regular, color=text_color)

import smtplib
from email.mime.text import MIMEText

def send_approval_email(user_email, username):
    sender_email = "margdatatrust2025@gmail.com"
    sender_password = "gfsk zxli lmkv gygp"

    subject = "Your ID is Activated"
    body = f"Hello {username},\n\nYour ID has been approved and is now active. You can log in and use our services.\n\nBest Regards,\nMargdata Team"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = user_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)  # Change SMTP settings if needed
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        print("Approval email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)

from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.contrib.auth.forms import SetPasswordForm
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
import logging

logger = logging.getLogger(__name__)

class CustomPasswordResetView(PasswordResetView):
    template_name = "donation/user_password_reset.html"
    email_template_name = "donation/password_reset_email.html"
    subject_template_name = "donation/password_reset_subject.txt"
    success_url = reverse_lazy("user_password_reset_done")
    from_email = settings.EMAIL_HOST_USER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain'] = settings.SITE_DOMAIN
        context['protocol'] = 'https' if not settings.DEBUG else 'http'
        context['title'] = 'Password Reset'
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        logger.info(f"Password reset requested for email: {email}")
        
        try:
            user = CustomUser.objects.get(email=email)
            logger.info(f"User found with email: {email}")
            
            extra_context = {
                'domain': settings.SITE_DOMAIN,
                'protocol': 'https' if not settings.DEBUG else 'http',
                'email': email,
            }
            
            # Only send email if user exists
            form.save(
                request=self.request,
                from_email=self.from_email,
                email_template_name=self.email_template_name,
                subject_template_name=self.subject_template_name,
                extra_email_context=extra_context
            )
            logger.info(f"Password reset email sent successfully to {email}")
            return super().form_valid(form)
                
        except CustomUser.DoesNotExist:
            logger.warning(f"No user found with email: {email}")
            # Still return success to prevent email enumeration
            return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "donation/user_password_reset_confirm.html"
    success_url = reverse_lazy("user_password_reset_complete")
    form_class = SetPasswordForm

    def form_valid(self, form):
        user = form.save(commit=False)  # Get user instance
        raw_password = form.cleaned_data["new_password1"]  # Capture new password
        user.set_password(raw_password)  # Hash and set password
        user.save()  # Force save
        update_session_auth_hash(self.request, user)  # Keep session active
        print(f"Password changed successfully for {user.email}")  # Debugging print
        return super().form_valid(form)

def upi_qr(request):
    upi_url = "upi://pay?pa=margdatatrust@sbi&pn=Margdata Trust&am=50&cu=INR"
    img = qrcode.make(upi_url)
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response



